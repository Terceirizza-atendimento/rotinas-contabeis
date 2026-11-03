"""Classifica por regras (sem agentes, sem tokens) e monta o CSV unico de importacao.

Uso: python classificar.py "<pasta do cliente>" regras\043.json
Le Razao.xlsx (contas a reclassificar) e o extrato do banco (linhas que ainda NAO estao no Razao), aplica as regras
(primeiro que casar, por contraparte), grava lotes e chama montar_csv.py (valida e escreve o CSV em
'Arquivos de importacao\02 Pendente de importar'). O que nao casa ou espera conta nova vai para PENDENCIAS
(nunca chuta). Imprime um resumo curto.
"""
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter

import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
pasta, regras_f = sys.argv[1], sys.argv[2]
R = json.load(open(regras_f, encoding="utf-8"))
BANCO = R["banco"]
fmt = lambda v: f"{abs(v):.2f}".replace(".", ",")
limpo = lambda s: re.sub(r'[;&"]', " ", re.sub(r"\s+", " ", s)).strip()


def conta_por_regra(hist, entrada):
    u = hist.upper()
    for r in R["contrapartes"]:
        if any(k in u for k in r["contem"]):
            c = r.get("entrada" if entrada else "saida", r.get("conta"))
            if c is not None:
                return c
    return None


def aguardando(h):
    return any(k in h.upper() for k in R.get("aguardando_conta", []))


# 1) Razao: lancamentos das contas a reclassificar e do banco
ws = openpyxl.load_workbook(os.path.join(pasta, "Razão.xlsx"), read_only=True, data_only=True).active
conta = None
razao = {int(k): [] for k in R["reclassificar"]}
banco = Counter()
for r in ws.iter_rows(values_only=True):
    if not r:
        continue
    if r[0] == "Conta:":
        conta = int(r[1]); continue
    if isinstance(r[0], datetime.datetime) and len(r) > 9:
        d = r[0].strftime("%d/%m/%Y")
        if conta in razao:
            razao[conta].append((d, int(r[1]), limpo(str(r[2])), r[8] or 0, r[9] or 0))
        if conta == BANCO:
            banco[(d, round((r[8] or 0) - (r[9] or 0), 2))] += 1

lotes, pend = [], []
n_rec = 0
for c, sentido in ((int(k), v) for k, v in R["reclassificar"].items()):
    for d, lote, hist, deb, cred in razao[c]:
        v = deb if sentido == "saida" else cred
        if v <= 0:
            continue
        if aguardando(hist):
            pend.append(("aguarda conta", d, v, hist[:50])); continue
        dest = conta_por_regra(hist, sentido == "entrada")
        if dest in (None, c):
            if dest is None:
                pend.append((f"{c} mantido (sem regra)", d, v, hist[:60]))
            continue
        h = f"RECLASS LOTE {lote} {hist[:60]}"
        lotes.append(dict(data=d, deb=dest if sentido == "saida" else c, cred=c if sentido == "saida" else dest, valor=fmt(v), hist=h))
        n_rec += 1

# 2) Extrato: so o que ainda nao esta no Razao do banco (casa por data+valor)
n_novas = 0
extrato = os.path.join(pasta, R["extrato"])
for l in open(extrato, encoding="latin-1").read().splitlines()[6:]:
    c = l.split(";")
    if len(c) < 4 or not re.match(r"\d\d/\d\d/\d{4}$", c[0]):
        continue
    v = round(float(c[2].replace(".", "").replace(",", ".")), 2)
    if banco[(c[0], v)] > 0:
        banco[(c[0], v)] -= 1; continue
    h = limpo(c[1])[:70]
    if aguardando(h):
        pend.append(("aguarda conta", c[0], abs(v), h)); continue
    dest = conta_por_regra(h, v > 0)
    if dest is None:
        dest = R["padrao_entrada"] if v > 0 else R["padrao_saida"]
        pend.append((f"padrao {dest} (sem regra)", c[0], abs(v), h))
    lotes.append(dict(data=c[0], deb=BANCO if v > 0 else dest, cred=dest if v > 0 else BANCO, valor=fmt(v), hist=h))
    n_novas += 1

work = os.path.join(AQUI, "..", "saida"); os.makedirs(work, exist_ok=True)
lf = os.path.join(work, "lotes.json")
json.dump(lotes, open(lf, "w", encoding="utf-8"), ensure_ascii=False)
nome = f"{os.path.basename(pasta).split()[0]}_reclass_e_extrato.csv"
r = subprocess.run([sys.executable, os.path.join(AQUI, "montar_csv.py"), pasta, lf, nome], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
print((r.stdout + r.stderr).strip().splitlines()[-3:] if r.returncode else (r.stdout.strip().splitlines()[0]))
print(f"reclassificacoes {n_rec} | linhas novas do extrato {n_novas} | CSV: {nome}")
for t, n in Counter(p[0] for p in pend).items():
    print(f"  PENDENCIA {t}: {n} linhas, {sum(p[2] for p in pend if p[0] == t):.2f}")
json.dump(pend, open(os.path.join(work, "pendencias.json"), "w", encoding="utf-8"), ensure_ascii=False)
sys.exit(r.returncode)
