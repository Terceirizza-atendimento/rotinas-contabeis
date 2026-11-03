"""Monta e valida o CSV único de importação do Domínio a partir de uma lista simples (JSON).

Uso: python montar_csv.py "<pasta do cliente>" <lotes.json> [nome_saida.csv]
Entrada (JSON): lista de lotes, cada um com a data e as linhas. Lançamento simples (uma partida):
  {"data": "05/01/2026", "deb": 519, "cred": 5, "valor": "4000,00", "hist": "RECLASSIFICACAO ..."}
Lançamento de várias linhas (um lado por linha):
  {"data": "26/06/2026", "linhas": [{"cred": 8, "valor": "181,25", "hist": "..."},
                                    {"deb": 191, "valor": "178,31", "hist": "..."},
                                    {"deb": 352, "valor": "2,94", "hist": "..."}]}
Saída: <pasta>\\Arquivos de importação\\02 Pendente de importar\\<nome>.csv (padrão do modelo: separador ';',
cp1252, CRLF, vírgula decimal, 10 colunas, "Inicia Lote" numerado na primeira linha de cada lote; sobrescreve o
mesmo nome, nunca versiona). Valida antes de gravar e NÃO grava se houver FALHA: lote que não fecha, conta fora de
Plano de contas.txt da pasta (99999 = conta nova pendente: avisa), ';' ou entidade HTML no histórico, data
inválida, valor inválido. Ordena por data (estável). Não importa nada no Domínio.
"""
import csv
import datetime
import io
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

CAB = ["Data", "Cód. Conta Debito", "Cód. Conta Credito", "Valor", "Cód. Histórico", "Complemento Histórico",
       "Inicia Lote", "Código Matriz/Filial", "Centro de Custo Débito", "Centro de Custo Crédito"]


def dec(v):
    return Decimal(str(v).replace(".", "").replace(",", ".")) if "," in str(v) else Decimal(str(v))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pasta, spec = os.path.normpath(sys.argv[1]), sys.argv[2]
    nome = sys.argv[3] if len(sys.argv) > 3 else "Importacao_Dominio.csv"
    falhas, avisos = [], []

    plano = set()
    pc = os.path.join(pasta, "Plano de contas.txt")
    if os.path.exists(pc):
        for l in open(pc, "rb").read().decode("latin-1").split("\n"):
            if l[:7].isdigit() and set(l.strip()) != {"9"}:
                plano.add(int(l[:7]))
    else:
        avisos.append("Plano de contas.txt não encontrado na pasta: contas não conferidas")

    lotes = []
    for i, it in enumerate(json.load(open(spec, encoding="utf-8")), 1):
        linhas = it.get("linhas") or [{k: it[k] for k in ("deb", "cred", "valor", "hist") if k in it}]
        lotes.append((it["data"], linhas, i))

    rows = []
    for ordem, (data, linhas, i) in enumerate(sorted(lotes, key=lambda l: datetime.datetime.strptime(l[0], "%d/%m/%Y")
                                                      if re.fullmatch(r"\d\d/\d\d/\d{4}", l[0]) else datetime.datetime.min), 1):
        try:
            datetime.datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            falhas.append(f"lote {i}: data inválida '{data}'")
        d = c = Decimal(0)
        for k, ln in enumerate(linhas):
            try:
                v = dec(ln["valor"])
            except (InvalidOperation, KeyError):
                falhas.append(f"lote {i}: valor inválido {ln.get('valor')!r}")
                continue
            if v <= 0:
                falhas.append(f"lote {i}: valor não positivo {v}")
            if ln.get("deb"):
                d += v
            if ln.get("cred"):
                c += v
            for lado in ("deb", "cred"):
                cod = ln.get(lado)
                if cod and plano and int(cod) not in plano:
                    (avisos if int(cod) == 99999 else falhas).append(f"lote {i}: conta {cod} {'(conta nova pendente)' if int(cod) == 99999 else 'não existe no plano'}")
            h = str(ln.get("hist", ""))
            if ";" in h or re.search(r"&[A-Za-z]+;", h):
                falhas.append(f"lote {i}: ';' ou entidade HTML no histórico")
            try:
                h.encode("cp1252")
            except UnicodeEncodeError:
                falhas.append(f"lote {i}: histórico com caractere fora do cp1252")
            rows.append([data, ln.get("deb", ""), ln.get("cred", ""), f"{v:.2f}".replace(".", ","), "", h,
                         ordem if k == 0 else "", "", "", ""])
        if d != c:
            falhas.append(f"lote {i} ({data}): débito {d} ≠ crédito {c}")

    saida = os.path.join(pasta, "Arquivos de importação", "02 Pendente de importar", nome)
    print(f"{len(lotes)} lotes, {len(rows)} linhas, total de débitos {sum(dec(r[3]) for r in rows if r[1]):.2f}")
    for a in avisos:
        print("[AVISO]", a)
    for f in falhas:
        print("[FALHA]", f)
    if falhas:
        sys.exit("NÃO gravado: corrija as falhas")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    buf = io.StringIO(newline="")
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow(CAB)
    w.writerows(rows)
    open(saida, "wb").write(buf.getvalue().encode("cp1252"))
    print("gravado:", saida)


main()
