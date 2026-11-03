"""Exporta Balancete, Razão e Plano de contas da empresa ativa e roda o sensor, tudo num comando só.

Uso: python fechar_exportar.py "<pasta do cliente>" ddmmaaaa ddmmaaaa [--empresa NN]
  As datas são obrigatórias (lidas por OCR; só digita se o campo estiver diferente). --empresa NN: aborta antes de
  gerar se a barra de empresa do Domínio não mostrar o código NN.
Faz, em ordem: abre a Contabilidade se não houver janela (precisa de DW_SYS_USER/DW_SYS_PASS e, para o portal,
DW_USER/DW_PASS) -> arquiva Balancete.xlsx, Razão.xlsx e Plano de contas.txt atuais em
"99 Originais e duplicados" (prefixo antes_AAAAMMDD_HHMM_) -> balancete + exporta -> razão + exporta -> plano ->
sensor validar_exportacao.py. Imprime UMA linha por etapa e, no fim, o resultado do sensor (só FALHA/AVISO).
Para na primeira falha (código de saída 1) e mostra as últimas linhas do script que falhou.
NÃO importa CSV, NÃO gera/regera lançamentos. Importação: importar_csv.py. Integração: integracao.py.
"""
import datetime
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))


def rodar(nome, *args, limite=300):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(AQUI, nome), *args], cwd=AQUI, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=limite)
    seg = time.time() - t0
    if r.returncode != 0:
        print(f"[FALHOU] {nome} ({seg:.0f}s)")
        print("\n".join((r.stdout + r.stderr).strip().splitlines()[-8:]))
        sys.exit(1)
    print(f"[ok] {nome} {' '.join(args[1:2])} ({seg:.0f}s)".replace("  ", " "))
    return r.stdout


def main():
    args = sys.argv[1:]
    if "--empresa" in args:
        i = args.index("--empresa")
        os.environ["DOMINIO_EMPRESA"] = args[i + 1]
        del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    pasta = os.path.normpath(args[0])
    datas = args[1:3]
    if not os.path.isdir(pasta):
        sys.exit(f"pasta não existe: {pasta}")

    sys.path.insert(0, AQUI)
    from dominio_lib import achar_sistema
    if not achar_sistema():
        print("[..] sistema fechado: abrindo")
        subprocess.Popen([sys.executable, os.path.join(AQUI, "login_portal.py")], cwd=AQUI,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(45)
        rodar("abrir_contabilidade.py", limite=240)

    # arquivar o que já existe (nunca sobrescrever sem preservar)
    dest = os.path.join(pasta, "99 Originais e duplicados")
    os.makedirs(dest, exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    for f in ("Balancete.xlsx", "Razão.xlsx", "Plano de contas.txt"):
        src = os.path.join(pasta, f)
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest, f"antes_{carimbo}_{f}"))
    print("[ok] arquivos anteriores movidos para 99 Originais e duplicados")

    rodar("balancete.py", *datas)
    os.environ.pop("DOMINIO_EMPRESA", None)   # empresa já conferida; com o relatório aberto a barra fica coberta
    rodar("exportar_excel.py", pasta, "Balancete.xlsx")
    rodar("razao.py", *datas)
    rodar("exportar_excel.py", pasta, "Razão.xlsx")
    rodar("plano_contas.py", pasta)

    sensor = ["validar_exportacao.py", pasta, "--max-idade-min", "30"]
    if datas:
        sensor += ["--periodo", *datas]
    r = subprocess.run([sys.executable, os.path.join(AQUI, sensor[0]), *sensor[1:]], cwd=AQUI, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    linhas = (r.stdout + r.stderr).strip().splitlines()
    print("\n".join(l for l in linhas if not l.startswith("[OK]")))
    sys.exit(r.returncode)


main()
