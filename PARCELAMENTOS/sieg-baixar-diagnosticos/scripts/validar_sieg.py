"""Recebe e valida os downloads do SIEG (Diagnóstico Fiscal + Certidões + planilha Visão Geral).

Uso (sempre com -I):
  python -I validar_sieg.py receber --pasta "<...>\\DIAGNOSTICO FISCAL"          # pega os arquivos de Downloads e organiza
  python -I validar_sieg.py validar --pasta "<...>\\DIAGNOSTICO FISCAL"          # valida a rodada mais recente
  python -I validar_sieg.py validar --pasta "<...>" --rodada 2026-10-19

Só LÊ os PDFs/planilha e escreve resumo_<rodada>.csv e resumo_<rodada>.txt na pasta. Não acessa a internet.
Regra de ouro: o que não dá para provar pelo documento vira "REVISAR"; o script nunca "chuta" regular/irregular.
Sai com código 1 se houver algum ERRO (documento inválido, CNPJ divergente, arquivo faltando).
"""
import argparse, csv, glob, html, os, re, shutil, subprocess, sys, tempfile, time, zipfile
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOJE = date.today()
RE_CNPJ = re.compile(r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b")
RE_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


# ---------------------------------------------------------------- utilidades
def so_digitos(s):
    return re.sub(r"\D", "", s or "")


def lp(caminho):
    """Caminho absoluto com o prefixo de caminho longo do Windows (evita o limite de 260 caracteres do OneDrive)."""
    pref = "\\\\?\\"
    c = os.path.abspath(caminho)
    return pref + c if os.name == "nt" and not c.startswith(pref) else c


def d_br(s):
    m = RE_DATA.search(s or "")
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None
    except ValueError:
        return None


def fmt(d):
    return d.strftime("%d/%m/%Y") if d else ""


def texto_pdf(caminho):
    """Texto do PDF. Tenta pdftotext (Poppler); se não houver, pypdf. Retorna None se o PDF não abrir."""
    exe = shutil.which("pdftotext")
    if exe:
        # o pdftotext não aceita caminho longo: lê uma cópia temporária com nome curto
        with tempfile.TemporaryDirectory() as tmp:
            curto = os.path.join(tmp, "a.pdf")
            shutil.copyfile(lp(caminho), curto)
            r = subprocess.run([exe, "-enc", "UTF-8", "-layout", curto, "-"], capture_output=True)
        return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Falta um leitor de PDF. Rode:  python -m pip install pypdf   (ou instale o Poppler/pdftotext) e tente de novo.")
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(lp(caminho)).pages)
    except Exception:
        return None


def extrair_zip_seguro(zip_path, destino):
    """Extrai sem permitir caminhos fora do destino (zip slip)."""
    destino = os.path.abspath(destino)
    base = os.path.normcase(destino)
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            alvo = os.path.normcase(os.path.abspath(os.path.join(destino, info.filename)))
            if alvo != base and not alvo.startswith(base + os.sep):
                sys.exit(f"ZIP suspeito (caminho fora da pasta): {info.filename}. Parei.")
        # prefixo \\?\ evita o limite de 260 caracteres do Windows (comum em pastas do OneDrive)
        z.extractall("\\\\?\\" + destino if os.name == "nt" else destino)


def ler_xlsx(caminho):
    """Lê a 1ª planilha do .xlsx só com a biblioteca padrão. Retorna lista de dicts pelo cabeçalho."""
    with zipfile.ZipFile(caminho) as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode("utf-8"), re.S):
                ss.append(html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
        aba = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
        linhas = []
        for row in re.findall(r"<row[^>]*>(.*?)</row>", z.read(aba).decode("utf-8"), re.S):
            cel = {}
            for ref, attrs, corpo in re.findall(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', row, re.S):
                v = re.search(r"<v>(.*?)</v>", corpo or "", re.S)
                is_ = re.search(r"<is>.*?<t[^>]*>(.*?)</t>", corpo or "", re.S)
                if v and 't="s"' in attrs:
                    cel[ref] = ss[int(v.group(1))]
                elif v:
                    cel[ref] = html.unescape(v.group(1))
                elif is_:
                    cel[ref] = html.unescape(is_.group(1))
            linhas.append(cel)
    if not linhas:
        return []
    cab = {col: nome.strip() for col, nome in linhas[0].items()}
    return [{cab[c]: v for c, v in l.items() if c in cab} for l in linhas[1:] if l]


def campo(r, nome):
    """Valor de uma coluna da Visão Geral, tolerando acento/encoding no cabeçalho."""
    base = re.sub(r"[^a-z]", "", nome.lower())
    for k, v in r.items():
        if re.sub(r"[^a-z]", "", k.lower()).startswith(base[:4]):
            return (v or "").strip()
    return ""


# ---------------------------------------------------------------- receber
def cmd_receber(a):
    downloads = a.downloads or os.path.join(os.path.expanduser("~"), "Downloads")
    padroes = {"Diagnosticos": "Diagn*_*.zip", "Certidoes": "Certidoes_*.zip", "visao": "Certidao-VisaoGeral-*.xlsx"}
    limite, achados = time.time() + a.esperar * 60, {}
    print(f"Procurando em {downloads} (arquivos dos últimos {a.recentes} min; espero até {a.esperar} min).")
    while time.time() < limite:
        for k, pad in padroes.items():
            if k in achados:
                continue
            c = [p for p in glob.glob(os.path.join(downloads, pad))
                 if os.path.getmtime(p) >= time.time() - a.recentes * 60]
            if c:
                achados[k] = max(c, key=os.path.getmtime)
                print(f"  recebido: {os.path.basename(achados[k])}")
        if len(achados) == len(padroes):
            break
        time.sleep(5)
    if not achados:
        sys.exit("Nenhum arquivo do SIEG encontrado em Downloads.")
    tag = HOJE.isoformat()
    for k in ("Diagnosticos", "Certidoes"):
        if k not in achados:
            continue
        dest = os.path.join(a.pasta, f"{k}_{tag}")
        if os.path.isdir(dest):
            print(f"  {k}_{tag} já existe: NÃO sobrescrevi. Apague ou renomeie a pasta se quiser refazer.")
            continue
        os.makedirs(dest)
        try:
            extrair_zip_seguro(achados[k], dest)
        except (OSError, zipfile.BadZipFile) as e:
            shutil.rmtree(dest, ignore_errors=True)  # não deixa pasta pela metade
            sys.exit(f"Falha ao extrair {os.path.basename(achados[k])}: {e}\nUse uma --pasta com caminho mais curto (ex.: C:\\DIAGNOSTICO FISCAL) e rode de novo.")
        shutil.copy2(achados[k], a.pasta)
        print(f"  extraído em {os.path.basename(dest)}")
    if "visao" in achados:
        shutil.copy2(achados["visao"], a.pasta)
    faltando = [k for k in padroes if k not in achados]
    if faltando:
        print("ATENÇÃO, não encontrei em Downloads:", ", ".join(faltando))
    print("Agora rode o comando 'validar'.")


# ---------------------------------------------------------------- classificação de documentos
def classificar_diagnostico(txt):
    """Retorna (situacao, detalhes, alertas). Só afirma o que o texto prova."""
    u = txt.upper()
    if len(txt.strip()) < 300 or "DIAGNÓSTICO FISCAL" not in u:
        return "ERRO", [], ["arquivo não parece um Diagnóstico Fiscal (vazio, erro ou captcha)"]
    pend = sorted(set(p.strip() for p in re.findall(r"Pendência\s*-\s*([^\n_]+?)\s*_{3,}", txt)))
    n_dev = len(re.findall(r"\bDEVEDOR\b", u))
    det, alertas = [], []
    i = u.find("PROCURADORIA-GERAL DA FAZENDA NACIONAL _")
    pgfn = txt[i:] if i >= 0 else ""
    pgfn_limpo = bool(re.search(r"N[ÃA]O FORAM DETECTADAS PEND", pgfn.upper()))
    if pgfn and not pgfn_limpo and len(pgfn.strip()) > 120:
        pend.append("PGFN (conteúdo na seção; revisar)")
    sem_pend = bool(re.search(r"N[ÃA]O FORAM DETECTADAS PEND", u))
    if not pend and not n_dev and not sem_pend:
        return "REVISAR", [], ["não achei nem 'Pendência' nem 'Não foram detectadas pendências': conferir o PDF"]
    det += pend
    if n_dev:
        det.append(f"{n_dev} linha(s) DEVEDOR na Receita")
    corpo = re.sub(r"N[ÃA]O FORAM DETECTADAS PEND[^\n]*", "", txt, flags=re.I)
    if re.search(r"parcelamento|exigibilidade suspensa", corpo, re.I):
        alertas.append("cliente tem PARCELAMENTO/exigibilidade suspensa no diagnóstico: NÃO usar 'não identificamos pagamentos'; perguntar à coordenação")
    return ("COM_PENDENCIA" if (pend or n_dev) else "SEM_PENDENCIA"), det, alertas


def classificar_certidao(tipo, txt):
    """Retorna (situacao, validade|None, alertas)."""
    u = txt.upper()
    if len(txt.strip()) < 120:
        return "ERRO", None, ["arquivo vazio ou página de erro/captcha: NÃO é certidão"]
    D = r"(\d{2}/\d{2}/\d{4})"
    val = None
    for pad in (r"VALIDADE:?\s*" + D + r"\s+A\s+" + D,                      # FGTS: "Validade: 14/09/2026 a 13/10/2026"
                r"DATA DE EMISS[ÃA]O\s+DATA DE VALIDADE\s*" + D + r"\s+" + D,  # MG: emissão e validade lado a lado
                r"(?:DATA DE VALIDADE|VALIDADE|V[ÁA]LIDA AT[ÉE])\s*:?\s*" + D):
        m = re.search(pad, u)
        if m:
            val = d_br(m.group(m.lastindex))  # último grupo = a data de validade
            break
    if tipo == "FGTS":
        if "CERTIFICADO DE REGULARIDADE" in u:
            sit = "NEGATIVA"
        elif "IRREGULAR" in u:
            sit = "POSITIVA"
        else:
            sit = "REVISAR"
    elif tipo == "Trabalhista":
        if "CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS" in u or re.search(r"N[ÃA]O CONSTA COMO\s+INADIMPLENTE", u):
            sit = "NEGATIVA"
        elif "CERTIDÃO POSITIVA" in u or re.search(r"CONSTA COMO\s+INADIMPLENTE", u):
            sit = "POSITIVA"
        else:
            sit = "REVISAR"
    else:  # CRFB_PGFN, Estadual, Municipal e demais
        if "POSITIVA COM EFEITOS" in u:
            sit = "POSITIVA_COM_EFEITOS_DE_NEGATIVA"
        elif re.search(r"CERTID[ÃA]O POSITIVA", u):
            sit = "POSITIVA"
        elif re.search(r"POSITIVA", u):
            sit = "POSITIVA"
        elif re.search(r"CERTID[ÃA]O NEGATIVA|NEGATIVA|N[ÃA]O CONSTAM D[ÉE]BITOS", u):
            sit = "NEGATIVA"
        else:
            sit = "REVISAR"
    alertas = []
    if sit == "REVISAR":
        alertas.append("não consegui classificar pelo texto: abrir o PDF; não afirmar regular/irregular")
    if val and val < HOJE:
        alertas.append(f"VENCIDA em {fmt(val)}")
    return sit, val, alertas


# ---------------------------------------------------------------- validar
def achar_rodada(pasta, rodada):
    if rodada:
        return rodada
    tags = set()
    for p in glob.glob(os.path.join(pasta, "*_????-??-??")):
        m = re.match(r"(?:Diagnosticos|Certidoes)_(\d{4}-\d{2}-\d{2})$", os.path.basename(p))
        if m and os.path.isdir(p):
            tags.add(m.group(1))
    if not tags:
        sys.exit(f"Nenhuma pasta Diagnosticos_AAAA-MM-DD / Certidoes_AAAA-MM-DD em {pasta}. Rode 'receber' antes.")
    return sorted(tags)[-1]


def cmd_validar(a):
    a.pasta = lp(a.pasta)
    rod = achar_rodada(a.pasta, a.rodada)
    pd_ = os.path.join(a.pasta, f"Diagnosticos_{rod}")
    pc_ = os.path.join(a.pasta, f"Certidoes_{rod}")
    linhas, erros, avisos = [], [], []

    def add(cli, cnpj, doc, sit, consulta, validade, det, alertas):
        linhas.append([cli, cnpj, doc, sit, fmt(consulta), fmt(validade), "; ".join(det), "; ".join(alertas)])
        for al in alertas:
            grave = sit == "ERRO" or al.startswith("CNPJ")
            (erros if grave else avisos).append(f"{cli} [{doc}]: {al}")

    # MANIFESTO.txt: o que o SIEG não colocou no ZIP
    for nome, pz in (("Diagnósticos", pd_), ("Certidões", pc_)):
        if not os.path.isdir(pz):
            avisos.append(f"Pasta {os.path.basename(pz)} não existe: {nome} NÃO foram validados.")
            continue
        m = os.path.join(pz, "MANIFESTO.txt")
        if os.path.exists(m):
            conteudo = open(m, encoding="utf-8", errors="replace").read().strip()
            erros.append(f"MANIFESTO de {nome}: o SIEG avisou que arquivos NÃO entraram no ZIP (baixar de novo):\n      "
                         + conteudo.replace("\n", "\n      "))

    # Visão Geral
    visao = {}
    xl = sorted(glob.glob(os.path.join(a.pasta, "Certidao-VisaoGeral-*.xlsx")), key=os.path.getmtime)
    if xl:
        for r in ler_xlsx(xl[-1]):
            visao.setdefault(so_digitos(campo(r, "CNPJ")), []).append(r)
    else:
        avisos.append("Planilha Certidao-VisaoGeral-*.xlsx não encontrada: sem conferência cruzada.")

    # diagnósticos
    diag = {}
    for pdf in sorted(glob.glob(os.path.join(pd_, "*", "Diagnostico_*.pdf"))):
        cli = os.path.basename(os.path.dirname(pdf))
        cnpj_arq = so_digitos(os.path.basename(pdf))
        cnpj_pasta = (re.findall(r"\((\d{11,14})\)\s*$", cli) or [""])[0]
        txt = texto_pdf(pdf)
        if txt is None:
            add(cli, cnpj_arq, "Diagnóstico", "ERRO", None, None, [], ["PDF ilegível/corrompido"])
            continue
        sit, det, al = classificar_diagnostico(txt)
        m = re.search(r"CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", txt)  # ignora "CNPJ do certificado" (certificado digital do escritório)
        if cnpj_pasta and cnpj_pasta != cnpj_arq:
            al.append(f"CNPJ da pasta ({cnpj_pasta}) ≠ CNPJ do arquivo ({cnpj_arq})")
        if m and so_digitos(m.group(1)) != cnpj_arq:
            al.append(f"CNPJ dentro do PDF ({m.group(1)}) ≠ CNPJ do arquivo ({cnpj_arq})")
        if not m and sit != "ERRO":
            al.append("não achei CNPJ no texto do PDF: conferir à mão")
        ts = re.search(r"(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}:\d{2}", txt[:1500])
        consulta = d_br(ts.group(1)) if ts else None
        if not consulta:
            al.append("não achei a data/hora da consulta no topo do PDF")
        elif (HOJE - consulta).days > a.max_idade:
            al.append(f"consulta de {fmt(consulta)} tem mais de {a.max_idade} dias: pode estar desatualizada")
        if any(x.startswith("CNPJ") for x in al):
            sit = "ERRO"
        diag[cnpj_arq] = (sit, cli)
        add(cli, cnpj_arq, "Diagnóstico", sit, consulta, None, det, al)

    # certidões
    for pdf in sorted(glob.glob(os.path.join(pc_, "*", "*_Certidao_*.pdf"))):
        cli = os.path.basename(os.path.dirname(pdf))
        mm = re.match(r"(\d{11,14})_Certidao_(.+)\.pdf$", os.path.basename(pdf))
        if not mm:
            continue
        cnpj_arq, tipo = mm.group(1), mm.group(2)
        txt = texto_pdf(pdf)
        if txt is None:
            add(cli, cnpj_arq, f"Certidão {tipo}", "ERRO", None, None, [], ["PDF ilegível/corrompido"])
            continue
        sit, val, al = classificar_certidao(tipo, txt)
        if len(cnpj_arq) == 14 and sit != "ERRO":
            achados = {so_digitos(x) for x in RE_CNPJ.findall(txt)}
            if achados and cnpj_arq not in achados and not any(x[:8] == cnpj_arq[:8] for x in achados):
                al.append(f"CNPJ dentro do PDF ({', '.join(sorted(achados))}) ≠ CNPJ do arquivo ({cnpj_arq})")
                sit = "ERRO"
        add(cli, cnpj_arq, f"Certidão {tipo}", sit, None, val, [], al)

    # conferência cruzada com a Visão Geral
    for cnpj, regs in visao.items():
        for r in regs:
            tipo, sit_x, emp = campo(r, "Tipo"), campo(r, "Situação"), campo(r, "Empresa") or cnpj
            if tipo == "Outros":
                avisos.append(f"{emp}: tipo 'Outros' na Visão Geral = consulta que falhou (captcha etc.), não é débito: refazer.")
            elif sit_x.lower() == "irregular" and tipo == "CRFB_PGFN":
                d = diag.get(cnpj)
                if not d:
                    erros.append(f"{emp}: irregular federal na Visão Geral mas SEM diagnóstico nos arquivos baixados.")
                elif d[0] == "SEM_PENDENCIA":
                    avisos.append(f"{emp}: Visão Geral diz irregular federal, mas o diagnóstico baixado está SEM pendência: conferir datas.")
    if visao:
        for cnpj, (sit, cli) in diag.items():
            irregular = any(campo(r, "Situação").lower() == "irregular" for r in visao.get(cnpj, []))
            if sit == "COM_PENDENCIA" and not irregular:
                avisos.append(f"{cli}: diagnóstico com pendência, mas a Visão Geral não lista como irregular: conferir.")

    # relatório
    com = sorted(cli for s, cli in diag.values() if s == "COM_PENDENCIA")
    n_sem = sum(1 for s, _ in diag.values() if s == "SEM_PENDENCIA")
    n_rev = sum(1 for s, _ in diag.values() if s in ("REVISAR", "ERRO"))
    out = [f"RODADA {rod}  (validado em {fmt(HOJE)})",
           f"Diagnósticos lidos: {len(diag)} | com pendência: {len(com)} | sem pendência: {n_sem} | revisar/erro: {n_rev}",
           f"Certidões lidas: {sum(1 for l in linhas if l[2].startswith('Certidão'))}", ""]
    out.append("== ERROS (resolver antes de usar os arquivos) ==" if erros else "== Nenhum erro ==")
    out += [f"  - {e}" for e in erros]
    out += ["", "== AVISOS (conferir) ==" if avisos else "== Nenhum aviso =="]
    out += [f"  - {e}" for e in avisos]
    out += ["", "== CLIENTES COM PENDÊNCIA NO DIAGNÓSTICO FEDERAL =="] + ([f"  - {c}" for c in com] or ["  (nenhum)"])
    pos = [l for l in linhas if l[2].startswith("Certidão") and l[3].startswith("POSITIVA")]
    out += ["", "== CERTIDÕES POSITIVAS (outras pendências: federal/estadual/trabalhista/etc.) =="]
    out += [f"  - {l[0]} [{l[2]}] {l[3]}" for l in pos] or ["  (nenhuma)"]
    rev = [l for l in linhas if l[3] == "REVISAR"]
    if rev:
        out += ["", "== NÃO CLASSIFICADOS (abrir o PDF; não afirmar nada ao cliente) =="]
        out += [f"  - {l[0]} [{l[2]}]" for l in rev]
    texto = "\n".join(out)
    print(texto)
    csv_p = os.path.join(a.pasta, f"resumo_{rod}.csv")
    txt_p = os.path.join(a.pasta, f"resumo_{rod}.txt")
    with open(csv_p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cliente", "cnpj", "documento", "situacao", "data_consulta", "validade", "detalhes", "alertas"])
        w.writerows(linhas)
    with open(txt_p, "w", encoding="utf-8") as f:
        f.write(texto)
    print("\nGerado: " + csv_p.replace("\\\\?\\", "") + "\n        " + txt_p.replace("\\\\?\\", ""))
    sys.exit(1 if erros else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("receber")
    r.add_argument("--pasta", required=True)
    r.add_argument("--downloads")
    r.add_argument("--esperar", type=int, default=20, help="minutos esperando os arquivos (padrão 20)")
    r.add_argument("--recentes", type=int, default=60, help="só arquivos baixados nos últimos N min (padrão 60)")
    v = sp.add_parser("validar")
    v.add_argument("--pasta", required=True)
    v.add_argument("--rodada")
    v.add_argument("--max-idade", type=int, default=10, help="dias; consulta mais velha gera aviso (padrão 10)")
    a = p.parse_args()
    if a.cmd == "receber":
        os.makedirs(a.pasta, exist_ok=True)
    elif not os.path.isdir(a.pasta):
        sys.exit(f"Pasta não existe: {a.pasta}")
    {"receber": cmd_receber, "validar": cmd_validar}[a.cmd](a)


if __name__ == "__main__":
    main()
