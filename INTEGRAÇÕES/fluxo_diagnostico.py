"""Fluxo do diagnóstico fiscal: tarefas "Consulta Relação Débitos" (Gclick) x diagnósticos baixados do SIEG.

Uso:  python -I fluxo_diagnostico.py                    (usa a rodada mais recente em DIAGNOSTICO FISCAL)
      python -I fluxo_diagnostico.py --rodada 2026-10-19
Só LÊ (Gclick e pastas). Gera dados/diagnostico_<rodada>.csv com o que enviar.

O que ainda é manual: anexar o PDF na etapa 2 e dar o check (endpoint de parceiro do Gclick) e o envio ao cliente
(hoje feito pelo Gclick/Digisac, ver skill gclick-diagnostico-fiscal).
"""
import csv, glob, os, re, subprocess, sys
from datetime import date
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
RAIZ = os.path.join(AQUI, "..", "DIAGNOSTICO FISCAL")


def env(n):
    if os.environ.get(n):
        return os.environ[n]
    return subprocess.run(["powershell", "-NoProfile", "-Command", f"[Environment]::GetEnvironmentVariable('{n}','User')"],
                          capture_output=True, text=True).stdout.strip()


def receber_sieg(minutos=20):
    """Etapa 0: espera os ZIPs/planilha baixados do SIEG em Downloads e organiza em DIAGNOSTICO FISCAL.
    O download em si é feito no navegador (login e cliques do usuário; ver skill gclick-diagnostico-fiscal, seção 1)."""
    import shutil, time, zipfile
    downloads = os.path.join(os.path.expanduser("~"), "Downloads"); hoje = date.today().isoformat()
    padroes = {"Diagnosticos": "Diagn*stico_*.zip", "Certidoes": "Certidoes_*.zip", "visao": "Certidao-VisaoGeral-*.xlsx"}
    inicio = time.time() - 1800  # só arquivos baixados na última meia hora
    print(f"Etapa 0: aguardando os arquivos do SIEG em {downloads} (até {minutos} min).")
    print("  Baixe: Certidões (Baixar Todos, filtro Irregular), Diagnóstico Fiscal (idem) e a Visão Geral (Exportar Todos).")
    achados, limite = {}, time.time() + minutos * 60
    while len(achados) < len(padroes) and time.time() < limite:
        for k, pad in padroes.items():
            if k in achados:
                continue
            c = [p for p in glob.glob(os.path.join(downloads, pad)) if os.path.getmtime(p) >= inicio and not p.endswith(".crdownload")]
            if c:
                achados[k] = max(c, key=os.path.getmtime); print(f"  recebido: {os.path.basename(achados[k])}")
        time.sleep(5)
    if not achados:
        sys.exit("Nenhum arquivo do SIEG encontrado. Baixe e rode de novo.")
    for k in ("Diagnosticos", "Certidoes"):
        if k in achados:
            dest = os.path.join(RAIZ, f"{k}_{hoje}")
            if os.path.isdir(dest):
                print(f"  {k}_{hoje} já existe: não sobrescrevi."); continue
            os.makedirs(dest)
            with zipfile.ZipFile(achados[k]) as z:
                z.extractall(dest)
            shutil.copy(achados[k], RAIZ); print(f"  extraído em {os.path.basename(dest)}")
            man = os.path.join(dest, "MANIFESTO.txt")
            if os.path.exists(man):
                print("  MANIFESTO.txt (arquivos que não entraram):\n   " + open(man, encoding="utf-8", errors="replace").read()[:600].replace("\n", "\n   "))
    if "visao" in achados:
        shutil.copy(achados["visao"], RAIZ)
    faltando = [k for k in padroes if k not in achados]
    if faltando:
        print("  ATENÇÃO, não encontrei:", ", ".join(faltando))


def main():
    if "--sieg" in sys.argv:
        receber_sieg()
    pastas = sorted(glob.glob(os.path.join(RAIZ, "Diagnosticos_*")))
    if "--rodada" in sys.argv:
        rodada = sys.argv[sys.argv.index("--rodada") + 1]
    elif pastas:
        rodada = os.path.basename(pastas[-1]).split("_", 1)[1]
    else:
        sys.exit("Nenhuma pasta Diagnosticos_AAAA-MM-DD encontrada em DIAGNOSTICO FISCAL.")
    base = os.path.join(RAIZ, f"Diagnosticos_{rodada}")
    if not os.path.isdir(base):
        sys.exit(f"Pasta não encontrada: {base}")

    # 1) diagnósticos baixados do SIEG (só clientes com débito), indexados por CNPJ/CPF
    diag = {}
    for d in os.listdir(base):
        m = re.search(r"\((\d{11,14})\)\s*$", d)
        if not m:
            continue
        pdfs = glob.glob(os.path.join(base, d, "Diagnostico_*.pdf"))
        if pdfs:
            diag[m.group(1)] = (d, pdfs[0])
    print(f"Rodada {rodada}: {len(diag)} cliente(s) com diagnóstico em PDF.")

    # 2) tarefas abertas no Gclick
    for n in ("GCLICK_CLIENT_ID", "GCLICK_CLIENT_SECRET"):
        os.environ[n] = os.environ.get(n) or env(n)
    import gclick
    hoje = date.today(); ini = hoje.replace(day=1).isoformat()
    fim = hoje.replace(month=12, day=31).isoformat() if hoje.month == 12 else (hoje.replace(month=hoje.month + 1, day=1)).isoformat()
    tarefas = gclick.tarefas_por_nome("Débitos", ini, fim, status="A")
    print(f"Gclick: {len(tarefas)} tarefa(s) 'Consulta Relação Débitos' abertas em {hoje:%m/%Y}.")
    # tarefas já tratadas no mês (C = concluída, D = dispensada), por inscrição do cliente
    tratadas = {}
    for st, rotulo in (("C", "CONCLUIDA"), ("D", "DISPENSADA")):
        for t in gclick.tarefas_por_nome("Débitos", ini, fim, status=st):
            tratadas.setdefault(t.get("clienteInscricao") or "", f"{rotulo} em {t.get('dataConclusao') or t.get('dataAcao') or '?'} (tarefa {t['id']})")
    print(f"Gclick: {len(tratadas)} cliente(s) com tarefa já concluída/dispensada no mês.\n")

    # 3) cruzamento
    linhas, usados = [], set()
    for t in tarefas:
        insc = t.get("clienteInscricao") or ""
        d = diag.get(insc)
        if d:
            usados.add(insc)
        linhas.append([t["id"], t.get("clienteApelido"), insc, t.get("dataVencimento"),
                       "SIM" if d else "NAO", d[1] if d else "", "ENVIAR" if d else "SEM DIAGNOSTICO (sem débito? suspenso? conferir)"])
    for insc, (nome, p) in diag.items():
        if insc not in usados:
            linhas.append(["", nome, insc, "", "SIM", p, tratadas.get(insc, "SEM TAREFA NO GCLICK (falta criar? conferir)")])

    print(f"{'Tarefa':10} {'Cliente':38} {'Diag':5} Situação")
    for l in linhas:
        print(f"{l[0]:10} {str(l[1])[:38]:38} {l[4]:5} {l[6]}")
    saida = os.path.join(AQUI, "dados", f"diagnostico_{rodada}.csv")
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["tarefa", "cliente", "inscricao", "vencimento", "tem_diagnostico", "pdf", "situacao"])
        w.writerows(linhas)
    print(f"\nRelatório salvo em {saida}")


main()
