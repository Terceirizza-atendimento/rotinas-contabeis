r"""Fechamento de um cliente em UM comando, por etapas retomaveis (sem agentes, saida curta).

Uso: python fechar.py <NNN> <ddmmaaaa> <ddmmaaaa> [--integrar] [--gravar] [--de ETAPA] [--ate ETAPA] [--forcar]
Etapas (nesta ordem): sessao, integrar, exportar, classificar, importar, conferir
  sessao      abre a Contabilidade se preciso, troca para a empresa NNN e confere a barra
  integrar    integracao fiscal+folha do periodo, com Gravar (so com --integrar)
  exportar    Balancete, Razao e Plano de contas + sensor (fechar_exportar.py)
  classificar regras\NNN.json: reclassifica o Razao e lanca o extrato -> CSV unico em 02 Pendente de importar
  importar    importa o CSV no Dominio e GRAVA (so com --gravar; uma unica vez: o estado bloqueia repetir)
  conferir    reexporta e roda o sensor depois da importacao
Estado em saida\estado_NNN.json: etapas ja feitas (retoma com --de). 'importar' feita nao roda de novo sem --forcar.
Imprime uma linha por etapa; para na primeira falha mostrando o motivo.
"""
import datetime
import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import dominio_lib  # noqa: E402  (carrega DW_* do Windows)

ETAPAS = ["sessao", "integrar", "exportar", "classificar", "importar", "conferir"]


def args():
    a = sys.argv[1:]
    flags = {"integrar", "gravar", "forcar"}
    opts = {x[2:]: True for x in a if x.startswith("--") and x[2:] in flags}
    de = a[a.index("--de") + 1] if "--de" in a else ETAPAS[0]
    ate = a[a.index("--ate") + 1] if "--ate" in a else ETAPAS[-1]
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--de", "--ate"))]
    if len(pos) != 3:
        sys.exit(__doc__)
    return pos[0], pos[1], pos[2], opts, de, ate


def pasta_cliente(nnn):
    raiz = os.environ.get("DOMINIO_CLIENTES", r"C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO")
    for d in os.listdir(raiz):
        if d.startswith(nnn + " ") and os.path.isdir(os.path.join(raiz, d)):
            return os.path.join(raiz, d)
    sys.exit(f"pasta {nnn} - ... não encontrada em {raiz}")


def rodar(nome, *a, limite=900):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(AQUI, nome), *a], cwd=AQUI, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=limite)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines(), time.time() - t0


def main():
    nnn, ini, fim, opts, de, ate = args()
    pasta = pasta_cliente(nnn)
    mm, aaaa = ini[2:4], ini[4:]
    comp = f"{ini[2:4]}{ini[4:]}-{fim[2:4]}{fim[4:]}"
    ef = os.path.join(AQUI, "..", "saida", f"estado_{nnn}.json"); os.makedirs(os.path.dirname(ef), exist_ok=True)
    estado = json.load(open(ef, encoding="utf-8")) if os.path.exists(ef) else {}
    cod = str(int(nnn))
    os.environ["DOMINIO_EMPRESA"] = cod
    print(f"Cliente {os.path.basename(pasta)} | {ini[:2]}/{ini[2:4]}/{ini[4:]} a {fim[:2]}/{fim[2:4]}/{fim[4:]}")

    def feito(e, msg):
        estado[e] = {"quando": datetime.datetime.now().isoformat(timespec="seconds"), "msg": msg}
        json.dump(estado, open(ef, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[ok] {e}: {msg}")

    def falha(e, linhas):
        print(f"[FALHOU] {e}")
        print("\n".join(linhas[-6:])); sys.exit(1)

    for e in ETAPAS[ETAPAS.index(de):ETAPAS.index(ate) + 1]:
        if e == "integrar" and not opts.get("integrar"):
            print("[--] integrar: pulado (use --integrar)"); continue
        if e == "importar":
            if not opts.get("gravar"):
                print("[--] importar: pulado (use --gravar; grava lançamentos)"); continue
            if "importar" in estado and not opts.get("forcar"):
                print(f"[--] importar: JÁ FEITO em {estado['importar']['quando']} (não repete; --forcar só se tiver certeza)"); continue
        if e == "sessao":
            if not dominio_lib.achar_sistema():
                rc, l, s = rodar("abrir_contabilidade.py", limite=300)
                time.sleep(30)                                  # o módulo termina de carregar depois do login
                if not dominio_lib.achar_sistema(): falha(e, l or ["Contabilidade não abriu"])
            rc, l, s = rodar("trocar_empresa.py", cod, limite=300)
            if rc: falha(e, l)
            feito(e, f"empresa {cod} ativa")
        elif e == "integrar":
            rc, l, s = rodar("integracao.py", comp, "--gravar", limite=900)
            if rc or any("GRAVAR PENDENTE" in x for x in l): falha(e, l)
            feito(e, f"fiscal+folha {comp} gravados ({s:.0f}s)")
        elif e == "exportar" or e == "conferir":
            rc, l, s = rodar("fechar_exportar.py", pasta, ini, fim, "--empresa", cod, limite=1200)
            res = [x for x in l if x.startswith("RESULTADO") or x.startswith("[FALHA")]
            if rc: falha(e, l)
            feito(e, (res[-1] if res else "ok") + f" ({s:.0f}s)")
        elif e == "classificar":
            rg = os.path.join(AQUI, "regras", f"{nnn}.json")
            if not os.path.exists(rg):
                print(f"[--] classificar: sem regras/{nnn}.json (crie com as regras do cliente)"); continue
            rc, l, s = rodar("classificar.py", pasta, rg)
            if rc: falha(e, l)
            feito(e, " | ".join(x.strip() for x in l))
        elif e == "importar":
            rc, l, s = rodar("importar_csv.py", pasta, "--gravar", limite=1500)
            if rc: falha(e, l)
            feito(e, f"CSV importado e gravado ({s:.0f}s); mova o CSV para 01 Importados")


main()
