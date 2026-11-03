#!/usr/bin/env python3
"""Registro padronizado das NFS-e emitidas pela Terceirizza.

Uso (PowerShell, a partir desta pasta):
  python -I nfse_registro.py registrar  <arquivo.pdf | arquivo_nfse.xml> [--sigla RJ]
  python -I nfse_registro.py proximo-ndps STUDIO_A [--serie 1]
  python -I nfse_registro.py validar --sigla STUDIO_A --tomador-doc 08532073000136 --cep 89213330 \
        --valor 537.00 --competencia 2026-10-30 [--ctrib 070104 --nbs 114021100]
  python -I nfse_registro.py listar [--sigla RJ]
  python -I nfse_registro.py conferir          # confere se todo PDF do registro existe e se nao ha duplicata

registrar: le o DANFSe (PDF) ou o XML da NFS-e (retorno da API), grava/atualiza a linha em
registro_notas.csv (chave de acesso = identificador unico) e copia o PDF para
<pasta do prestador>\\AAAA-MM\\ com o nome padrao (ver LEIA-ME - PADRAO.md).
"""
import argparse, csv, datetime as dt, json, re, shutil, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "registro_notas.csv"
COLS = ["chave", "sigla", "prestador_cnpj", "prestador_nome", "nNFSe", "serie_dps", "nDPS",
        "competencia", "emissao", "tomador_doc", "tomador_nome", "valor", "cTribNac", "nbs",
        "canal", "pdf_padrao", "obs"]


def prestadores():
    d = json.loads((BASE / "prestadores.json").read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def sigla_por_cnpj(cnpj):
    for s, p in prestadores().items():
        if p["cnpj"] == cnpj:
            return s
    return ""


def so_digitos(s):
    return re.sub(r"\D", "", s or "")


# ---------- validacoes ----------
def cnpj_ok(c):
    c = so_digitos(c)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    for n in (12, 13):
        pesos = list(range(n - 7, 1, -1)) + list(range(9, 1, -1))
        soma = sum(int(a) * b for a, b in zip(c[:n], pesos))
        dv = 11 - soma % 11
        dv = 0 if dv >= 10 else dv
        if int(c[n]) != dv:
            return False
    return True


def cpf_ok(c):
    c = so_digitos(c)
    if len(c) != 11 or len(set(c)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(a) * b for a, b in zip(c[:n], range(n + 1, 1, -1)))
        dv = (soma * 10) % 11 % 10
        if int(c[n]) != dv:
            return False
    return True


def cmd_validar(a):
    erros, avisos = [], []
    P = prestadores()
    p = P.get(a.sigla)
    if not p:
        erros.append(f"prestador '{a.sigla}' nao cadastrado em prestadores.json (cadastrar so depois de confirmar os parametros com o usuario)")
    doc = so_digitos(a.tomador_doc)
    if len(doc) == 14:
        if not cnpj_ok(doc): erros.append(f"CNPJ do tomador invalido (digito verificador): {doc}")
    elif len(doc) == 11:
        if not cpf_ok(doc): erros.append(f"CPF do tomador invalido (digito verificador): {doc}")
    else:
        erros.append(f"documento do tomador deve ter 11 ou 14 digitos: '{a.tomador_doc}'")
    if p and doc == p["cnpj"]:
        erros.append("tomador igual ao prestador")
    if a.cep and len(so_digitos(a.cep)) != 8:
        erros.append(f"CEP deve ter 8 digitos: '{a.cep}'")
    try:
        v = float(a.valor)
        if v <= 0: erros.append("valor deve ser maior que zero")
        if not re.fullmatch(r"\d+\.\d{2}", a.valor):
            erros.append(f"valor deve usar ponto e 2 casas (ex. 537.00): '{a.valor}'")
    except ValueError:
        erros.append(f"valor invalido: '{a.valor}' (use 537.00, sem R$ nem virgula)")
    try:
        c = dt.date.fromisoformat(a.competencia)
        hoje = dt.date.today()
        if c > hoje: erros.append(f"competencia no futuro: {c}")
        if (hoje - c).days > 60: avisos.append(f"competencia com mais de 60 dias ({c}); confirmar com o usuario")
    except ValueError:
        erros.append(f"competencia deve ser AAAA-MM-DD: '{a.competencia}'")
    if a.ctrib and not re.fullmatch(r"\d{6}", a.ctrib): erros.append("cTribNac deve ter 6 digitos (ex. 070104)")
    if a.nbs and not re.fullmatch(r"\d{9}", a.nbs): erros.append("NBS deve ter 9 digitos (ex. 114021100)")
    if p:
        if a.ctrib and "cTribNac" in p and a.ctrib != p["cTribNac"]:
            avisos.append(f"cTribNac {a.ctrib} difere do cadastro do prestador ({p['cTribNac']}); so seguir se o usuario pediu")
        if a.nbs and "nbs" in p and a.nbs != p["nbs"]:
            avisos.append(f"NBS {a.nbs} difere do cadastro do prestador ({p['nbs']}); so seguir se o usuario pediu")
    # duplicidade provavel: mesma data de competencia + tomador + valor ja registrados
    for r in ler():
        if (r["sigla"] == a.sigla and so_digitos(r["tomador_doc"]) == doc and r["valor"] == a.valor.replace(".", ",")
                and r["competencia"] == a.competencia):
            avisos.append(f"POSSIVEL DUPLICIDADE: ja existe NFS-e {r['nNFSe']} (chave {r['chave']}) com mesmo tomador, valor e competencia")
    for e in erros: print("ERRO  :", e)
    for w in avisos: print("AVISO :", w)
    if not erros:
        print("OK    : pedido consistente. Ainda falta a conferencia visual e o 'pode emitir' do usuario.")
    sys.exit(1 if erros else 0)


# ---------- leitura do registro ----------
def ler():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def gravar(rows):
    rows.sort(key=lambda r: (r["sigla"], r["emissao"], r["nNFSe"].zfill(9)))
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def cmd_proximo(a):
    serie = str(int(a.serie))
    usados = [int(r["nDPS"]) for r in ler()
              if r["sigla"] == a.sigla and r["serie_dps"].lstrip("0") == serie.lstrip("0") and r["nDPS"].isdigit()]
    prox = max(usados) + 1 if usados else 1
    print(prox)
    print(f"(ultimo nDPS registrado na serie {serie}: {max(usados) if usados else 'nenhum'}; "
          "se o servidor recusar por duplicidade, consulte as notas do prestador no portal e use o proximo livre)", file=sys.stderr)


# ---------- extracao ----------
def extrair_pdf(path):
    import pymupdf
    t = pymupdf.open(str(path))[0].get_text()
    L = [x.strip() for x in t.splitlines()]

    def apos(rotulo_inicio, n=1, ocorrencia=1):
        achou = 0
        for i, x in enumerate(L):
            if x.upper().startswith(rotulo_inicio.upper()):
                achou += 1
                if achou == ocorrencia:
                    return L[i + n]
        return ""
    chave = apos("CHAVE DE ACESSO DA NFS-e")
    d = {"chave": chave, "nNFSe": ""}
    # numero da NFS-e: linha apos o rotulo 'N?MERO DA NFS-e' (acento vira lixo, entao busca por sufixo)
    for i, x in enumerate(L):
        if x.endswith("MERO DA NFS-e"): d["nNFSe"] = L[i + 1]; break
    for i, x in enumerate(L):
        if x.endswith("MERO DA DPS"): d["nDPS"] = L[i + 1]
        if x.endswith("RIE DA DPS"): d["serie_dps"] = L[i + 1]
        if x.startswith("COMPET") and "NFS-e" in x: d["competencia"] = L[i + 1]
        if x.startswith("DATA E HORA DA EMISS") and x.endswith("NFS-e") and "emissao" not in d: d["emissao"] = L[i + 1]
        if x.startswith("VALOR DA OPERA"): d["valor"] = L[i + 1]
        if x.startswith("PRESTADOR / FORNECEDOR"): d["prestador_cnpj"] = so_digitos(L[i + 2])
        if x.startswith("TOMADOR / ADQUIRENTE"): d["tomador_doc"] = so_digitos(L[i + 2])
        if x.startswith("C") and x.endswith("digo da NBS"): d["nbs"] = so_digitos(L[i + 1])
        if x.startswith("C") and "Tributa" in x and x.endswith("Nacional/Municipal"): d["cTribNac"] = so_digitos(L[i + 1].split("/")[0])
    nomes = [L[i + 1] for i, x in enumerate(L) if x == "Nome / Nome Empresarial"]
    d["prestador_nome"] = nomes[0] if nomes else ""
    d["tomador_nome"] = nomes[1] if len(nomes) > 1 else ""
    # normalizacoes
    d["competencia"] = br_para_iso(d.get("competencia", ""))
    d["emissao"] = br_para_iso(d.get("emissao", ""), com_hora=True)
    d["valor"] = re.sub(r"[^\d,]", "", d.get("valor", ""))
    d["serie_dps"] = str(int(d["serie_dps"])) if d.get("serie_dps", "").isdigit() else d.get("serie_dps", "")
    # Serie 70000 = numeracao do portal web (Emissor Nacional); serie 1 = nosso script de API
    d["canal"] = "portal" if d.get("serie_dps") == "70000" else "api"
    return d


def extrair_xml(path):
    x = Path(path).read_text(encoding="utf-8")
    g = lambda tag: (re.search(rf"<{tag}>([^<]*)</{tag}>", x) or [None, ""])[1]
    chave = (re.search(r'Id="NFS(\d{50})"', x) or [None, ""])[1]
    emit = re.search(r"<emit>.*?<CNPJ>(\d+)</CNPJ>.*?<xNome>([^<]*)</xNome>", x, re.S)
    toma = re.search(r"<toma>.*?<(?:CNPJ|CPF)>(\d+)</(?:CNPJ|CPF)>.*?<xNome>([^<]*)</xNome>", x, re.S)
    d = {"chave": chave, "nNFSe": g("nNFSe"), "nDPS": g("nDPS"), "serie_dps": str(int(g("serie") or 0)),
         "competencia": g("dCompet"), "emissao": g("dhProc")[:19].replace("T", " ") or g("dhEmi")[:19].replace("T", " "),
         "valor": g("vServ").replace(".", ","), "cTribNac": g("cTribNac"), "nbs": g("cNBS"),
         "prestador_cnpj": emit[1] if emit else "", "prestador_nome": emit[2] if emit else "",
         "tomador_doc": toma[1] if toma else "", "tomador_nome": toma[2] if toma else "",
         "canal": "api"}
    return d


def br_para_iso(s, com_hora=False):
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})(?:\s+(\d\d:\d\d:\d\d))?", s or "")
    if not m: return s or ""
    out = f"{m[3]}-{m[2]}-{m[1]}"
    return out + (f" {m[4]}" if com_hora and m[4] else "")


# ---------- nome padrao ----------
def nome_curto(nome, limite=30):
    import unicodedata
    s = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limite].strip() or "SEM NOME"


def nome_padrao(d):
    data = (d["emissao"] or d["competencia"])[:10]
    return f"{data} - NFS-e {int(d['nNFSe'])} - {nome_curto(d['tomador_nome'])} - {d['chave']}.pdf"


def cmd_registrar(a):
    src = Path(a.arquivo)
    d = extrair_xml(src) if src.suffix.lower() == ".xml" else extrair_pdf(src)
    if not re.fullmatch(r"\d{50}", d.get("chave", "")):
        sys.exit(f"ERRO: chave de acesso de 50 digitos nao encontrada em {src.name}: '{d.get('chave')}'")
    sigla = a.sigla or sigla_por_cnpj(d["prestador_cnpj"])
    if not sigla:
        sys.exit(f"ERRO: CNPJ {d['prestador_cnpj']} ({d['prestador_nome']}) nao esta em prestadores.json; cadastre antes ou informe --sigla")
    P = prestadores()[sigla]
    if P["cnpj"] != d["prestador_cnpj"]:
        sys.exit(f"ERRO: a nota e do CNPJ {d['prestador_cnpj']}, mas a sigla {sigla} e {P['cnpj']}. Pasta errada? Nada foi gravado.")
    d["sigla"] = sigla
    d.setdefault("obs", "")
    rows = ler()
    antigo = next((r for r in rows if r["chave"] == d["chave"]), None)
    if src.suffix.lower() == ".pdf":
        mes = (d["emissao"] or d["competencia"])[:7]
        destino = BASE / P["pasta"] / mes
        destino.mkdir(parents=True, exist_ok=True)
        alvo = destino / nome_padrao(d)
        if len(str(alvo)) > 240:
            sys.exit(f"ERRO: caminho com {len(str(alvo))} caracteres (limite 260 do Windows): {alvo}")
        if not alvo.exists():
            shutil.copy2(src, alvo)
        d["pdf_padrao"] = str(alvo.relative_to(BASE))
    elif antigo:
        d["pdf_padrao"] = antigo["pdf_padrao"]
    else:
        d["pdf_padrao"] = ""
        d["obs"] = "so XML; falta baixar o DANFSe (Consulta Publica)"
    if antigo:
        for k in COLS:
            if d.get(k): antigo[k] = d[k]
        if d["pdf_padrao"]: antigo["obs"] = ""
        acao = "atualizada"
    else:
        rows.append({k: d.get(k, "") for k in COLS})
        acao = "incluida"
    gravar(rows)
    print(f"Nota {int(d['nNFSe'])} de {sigla} {acao} no registro. Tomador: {d['tomador_nome']}  Valor: R$ {d['valor']}  Competencia: {d['competencia']}")
    if d["pdf_padrao"]: print("PDF padrao:", BASE / d["pdf_padrao"])


def cmd_listar(a):
    for r in ler():
        if a.sigla and r["sigla"] != a.sigla: continue
        print(f"{r['sigla']:9} nº{r['nNFSe']:>4} {r['emissao'][:10]} comp {r['competencia']} R$ {r['valor']:>9}  {r['tomador_nome'][:38]:38} série {r['serie_dps']} nDPS {r['nDPS']} [{r['canal']}]")


def cmd_conferir(a):
    rows = ler(); ok = True
    vistos = set()
    for r in rows:
        if r["chave"] in vistos: print("DUPLICADA:", r["chave"]); ok = False
        vistos.add(r["chave"])
        if r["pdf_padrao"] and not (BASE / r["pdf_padrao"]).exists():
            print("PDF ausente:", r["pdf_padrao"]); ok = False
        if not r["pdf_padrao"]: print("sem PDF:", r["sigla"], r["nNFSe"], r["tomador_nome"]); ok = False
        if not re.fullmatch(r"\d{50}", r["chave"]): print("chave invalida:", r["chave"]); ok = False
    print(f"{len(rows)} notas no registro;", "tudo conferido." if ok else "ha pendencias acima.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("registrar"); r.add_argument("arquivo"); r.add_argument("--sigla"); r.set_defaults(f=cmd_registrar)
    n = sp.add_parser("proximo-ndps"); n.add_argument("sigla"); n.add_argument("--serie", default="1"); n.set_defaults(f=cmd_proximo)
    v = sp.add_parser("validar")
    for k in ("--sigla", "--tomador-doc", "--valor", "--competencia"): v.add_argument(k, required=True)
    for k in ("--cep", "--ctrib", "--nbs"): v.add_argument(k)
    v.set_defaults(f=cmd_validar)
    l = sp.add_parser("listar"); l.add_argument("--sigla"); l.set_defaults(f=cmd_listar)
    c = sp.add_parser("conferir"); c.set_defaults(f=cmd_conferir)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
