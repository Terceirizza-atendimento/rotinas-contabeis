r"""Sensor: valida as exportações do Domínio (Balancete.xlsx, Razão.xlsx, Plano de contas.txt) na pasta do cliente.

SOMENTE LEITURA: não abre o Domínio, não mexe em nada; só lê arquivos. Não depende de pyautogui.

Uso: python validar_exportacao.py "<pasta do cliente>" [--tipo balancete razao plano]
                                   [--periodo ddmmaaaa ddmmaaaa] [--cnpj 11222333000144]
                                   [--max-idade-min 60]
  --tipo           o que validar (padrão: os três)
  --periodo        período esperado no cabeçalho (padrão: não confere)
  --cnpj           CNPJ esperado (padrão: tabela do painel + cnpj_extra.json, pelo número da pasta NNN)
  --max-idade-min  o arquivo precisa ter sido gravado há no máximo N min (0 = não confere)
Saída: uma linha por checagem ([OK] / [AVISO] / [FALHA]) e o resultado final. Código de saída 1 se houver FALHA.
"""
import argparse
import json
import os
import re
import sys
import time

import openpyxl

BASE = r"C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO"
PAINEL = os.path.join(BASE, "CONTEXTOS", "painel-fechamento-contabil.md")
EXTRA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cnpj_extra.json")
ARQUIVOS = {"balancete": "Balancete.xlsx", "razao": "Razão.xlsx", "plano": "Plano de contas.txt"}

res = []


def ok(m): res.append(("OK", m))
def aviso(m): res.append(("AVISO", m))
def falha(m): res.append(("FALHA", m))


def so_digitos(s):
    return re.sub(r"\D", "", str(s or ""))


def cnpj_esperado(cod):
    """CNPJ pela tabela do painel (| NNN | cliente | 14 dígitos |) e, na falta, cnpj_extra.json."""
    try:
        txt = open(PAINEL, encoding="utf-8").read()
        m = re.search(rf"\|\s*{cod:03d}\s*\|[^|]*\|\s*(\d{{14}})", txt)
        if m:
            return m.group(1), "painel"
    except OSError:
        pass
    try:
        extra = json.load(open(EXTRA, encoding="utf-8"))
        v = extra.get(f"{cod:03d}")
        if v:
            return so_digitos(v["cnpj"] if isinstance(v, dict) else v), "cnpj_extra.json"
    except (OSError, ValueError):
        pass
    return None, None


def idade_min(caminho):
    return (time.time() - os.path.getmtime(caminho)) / 60


def checar_arquivo(pasta, chave, max_idade):
    p = os.path.join(pasta, ARQUIVOS[chave])
    if not os.path.exists(p):
        falha(f"{ARQUIVOS[chave]}: não existe na raiz da pasta do cliente")
        return None
    tam = os.path.getsize(p)
    if tam == 0:
        falha(f"{ARQUIVOS[chave]}: arquivo vazio (0 bytes; gravação incompleta?)")
        return None
    ok(f"{ARQUIVOS[chave]}: existe na raiz da pasta ({tam} bytes)")
    if max_idade:
        i = idade_min(p)
        (ok if i <= max_idade else falha)(f"{ARQUIVOS[chave]}: gravado há {i:.0f} min (limite {max_idade})")
    return p


def ler_xlsx(p, titulo, cnpj_esp, periodo, nome_aba):
    """Valida cabeçalho e devolve (códigos das contas, n de linhas de dados)."""
    nome = os.path.basename(p)
    try:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    except Exception as e:  # arquivo corrompido, não é xlsx, etc.
        falha(f"{nome}: não abre como xlsx ({type(e).__name__})")
        return None, 0
    if wb.sheetnames[0] != nome_aba:
        aviso(f"{nome}: aba '{wb.sheetnames[0]}' (esperado '{nome_aba}')")
    linhas = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))
    cab = {}
    for r in linhas[:8]:
        vals = [c for c in r if c not in (None, "")]
        if len(vals) >= 2 and isinstance(vals[0], str) and vals[0].endswith(":"):
            cab[vals[0].rstrip(":")] = vals[1]
    texto_titulo = next((str(c) for r in linhas[:8] for c in r if c and str(c).strip().upper() == titulo), None)
    (ok if texto_titulo else falha)(f"{nome}: título '{titulo}' {'presente' if texto_titulo else 'ausente (relatório errado?)'}")

    emp, cnpj_arq, per = cab.get("Empresa"), so_digitos(cab.get("C.N.P.J.")), cab.get("Período")
    if not emp or not cnpj_arq:
        falha(f"{nome}: cabeçalho sem Empresa/CNPJ")
    else:
        if cnpj_esp:
            if cnpj_arq == cnpj_esp:
                ok(f"{nome}: CNPJ {cnpj_arq} confere com o cliente da pasta ({emp})")
            else:
                falha(f"{nome}: CNPJ {cnpj_arq} ({emp}) é DIFERENTE do esperado {cnpj_esp}: arquivo de outra empresa na pasta")
        else:
            aviso(f"{nome}: sem CNPJ esperado para esta pasta; arquivo é de {emp} ({cnpj_arq}), confira à mão")
    if periodo:
        esp = f"{periodo[0][:2]}/{periodo[0][2:4]}/{periodo[0][4:]} - {periodo[1][:2]}/{periodo[1][2:4]}/{periodo[1][4:]}"
        (ok if per == esp else falha)(f"{nome}: período '{per}' {'= esperado' if per == esp else f'≠ esperado {esp}'}")
    else:
        ok(f"{nome}: período {per}")

    codigos, dados = set(), 0
    for r in linhas[7:]:
        if len(r) < 2:
            continue
        if titulo == "BALANCETE" and isinstance(r[0], (int, float)):
            codigos.add(int(r[0]))
            dados += 1
        elif titulo == "RAZÃO" and r[0] == "Conta:" and isinstance(r[1], (int, float)):
            codigos.add(int(r[1]))
            dados += 1
    (ok if dados else falha)(f"{nome}: {dados} contas no relatório" if dados else f"{nome}: nenhuma conta encontrada (relatório vazio?)")
    return codigos, dados


def ler_plano(p):
    """Valida formato do plano (latin-1, largura fixa, sentinela de 9s) e devolve o conjunto de códigos de conta."""
    raw = open(p, "rb").read()
    txt = raw.decode("latin-1")
    linhas = [l for l in txt.split("\n") if l.strip("\r")]
    linhas = [l.rstrip("\r") for l in linhas]
    if len(linhas) < 3:
        falha(f"Plano de contas.txt: só {len(linhas)} linhas")
        return set()
    sent = linhas[-1]
    (ok if set(sent) == {"9"} else falha)("Plano de contas.txt: " + ("termina com a linha sentinela de 9s" if set(sent) == {"9"} else "sem a linha sentinela de 9s (gravação incompleta?)"))
    larg = {len(l) for l in linhas[:-1]}
    (ok if len(larg) == 1 else falha)(f"Plano de contas.txt: {len(linhas) - 1} contas, largura fixa {sorted(larg)[0]}" if len(larg) == 1
                                       else f"Plano de contas.txt: larguras de linha diferentes {sorted(larg)[:5]} (corrompido?)")
    codigos = set()
    for l in linhas[:-1]:
        if l[:7].isdigit():
            codigos.add(int(l[:7]))
    if len(codigos) != len(linhas) - 1:
        falha("Plano de contas.txt: códigos de conta repetidos ou inválidos")
    return codigos


def checar_outras_pastas(pasta, tipos, ref_mtime, max_idade):
    """Procura o mesmo arquivo gravado recentemente em OUTRA pasta de cliente (sintoma de pasta errada)."""
    janela = (max_idade or 60) * 60
    for d in sorted(os.listdir(BASE)):
        outra = os.path.join(BASE, d)
        if not (os.path.isdir(outra) and re.match(r"^\d{3} - ", d)) or os.path.normcase(outra) == os.path.normcase(pasta):
            continue
        for t in tipos:
            f = os.path.join(outra, ARQUIVOS[t])
            if os.path.exists(f):
                m = os.path.getmtime(f)
                if time.time() - m <= janela and (ref_mtime is None or m >= ref_mtime):
                    falha(f"{ARQUIVOS[t]} gravado há {idade_min(f):.0f} min na pasta '{d}', depois do da pasta validada: pode ter ido para a pasta errada")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--tipo", nargs="+", choices=list(ARQUIVOS), default=list(ARQUIVOS))
    ap.add_argument("--periodo", nargs=2, metavar=("INI", "FIM"))
    ap.add_argument("--cnpj")
    ap.add_argument("--max-idade-min", type=int, default=60)
    a = ap.parse_args()
    pasta = os.path.normpath(a.pasta)

    # 1) pasta do cliente
    nome = os.path.basename(pasta)
    m = re.match(r"^(\d{3}) - (.+)$", nome)
    if not os.path.isdir(pasta):
        falha(f"pasta do cliente não existe: {pasta}")
        return fim()
    if not m:
        falha(f"pasta '{nome}' fora do padrão 'NNN - NOME'")
        return fim()
    if os.path.normcase(os.path.dirname(pasta)) != os.path.normcase(BASE):
        aviso("pasta não está diretamente dentro de IMPORTAÇÃO DOMINIO")
    ok(f"pasta do cliente: {nome}")
    cod = int(m.group(1))
    esp, fonte = (so_digitos(a.cnpj), "--cnpj") if a.cnpj else cnpj_esperado(cod)
    if esp:
        ok(f"CNPJ esperado {esp} (fonte: {fonte})")
    else:
        aviso(f"não achei CNPJ esperado para o cliente {cod:03d} (nem no painel nem em cnpj_extra.json)")

    # 2) arquivos
    codigos = {}
    mtimes = []
    for t in a.tipo:
        p = checar_arquivo(pasta, t, a.max_idade_min)
        if not p:
            continue
        mtimes.append(os.path.getmtime(p))
        if t == "balancete":
            codigos[t], _ = ler_xlsx(p, "BALANCETE", esp, a.periodo, "Balancete")
        elif t == "razao":
            codigos[t], _ = ler_xlsx(p, "RAZÃO", esp, a.periodo, "Razão")
        else:
            codigos[t] = ler_plano(p)

    # 3) coerência entre os arquivos (balancete/razão x plano)
    plano = codigos.get("plano")
    for t in ("balancete", "razao"):
        c = codigos.get(t)
        if plano and c:
            faltam = c - plano
            if faltam:
                falha(f"{ARQUIVOS[t]}: {len(faltam)} contas não existem no Plano de contas.txt (ex.: {sorted(faltam)[:5]}): plano de outra empresa?")
            else:
                ok(f"{ARQUIVOS[t]}: todas as {len(c)} contas existem no Plano de contas.txt")

    # 4) arquivos soltos e gravações em outras pastas
    soltos = [f for f in os.listdir(pasta) if re.match(r"^(Balancete|Razão|Razao)_", f) and f.lower().endswith((".xlsx", ".xls"))]
    if soltos:
        aviso(f"{len(soltos)} arquivo(s) 'Balancete_/Razão_...' soltos na raiz (fora do padrão; podem ser de outras empresas): {soltos[:3]}")
    checar_outras_pastas(pasta, a.tipo, min(mtimes) if mtimes else None, a.max_idade_min)
    fim()


def fim():
    for s, m in res:
        print(f"[{s}] {m}")
    nf = sum(1 for s, _ in res if s == "FALHA")
    na = sum(1 for s, _ in res if s == "AVISO")
    print(f"RESULTADO: {'REPROVADO' if nf else 'APROVADO'} ({nf} falha(s), {na} aviso(s))")
    sys.exit(1 if nf else 0)


main()
