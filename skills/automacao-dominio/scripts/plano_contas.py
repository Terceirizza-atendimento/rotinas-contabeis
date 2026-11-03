r"""Utilitários -> Exportação -> Contas: exporta o plano de contas (todas as contas) para a pasta do cliente.

Uso: python plano_contas.py "<pasta do cliente>" [--digitar]
  <pasta do cliente>: ex. ...\IMPORTAÇÃO DOMINIO\075 - DARLENE - UNIKA (o arquivo é Plano de contas.txt, na raiz)
  Lê o campo "Nome do arquivo" por OCR; se não for a pasta do cliente, digita o caminho certo e confere
  de novo antes de Exportar (aborta sem exportar se não ficar). --digitar é aceito e ignorado.
Pré-requisito: sistema aberto (abrir_contabilidade.py) e empresa do cliente ativa.
"""
import os
import sys
import time

import ocr
from dominio_lib import achar_sistema, capturar, clicar, digitar_texto, foco, limpar_campo, log, ler_area

pasta = sys.argv[1]
destino = os.path.join(pasta, "Plano de contas.txt")
remoto = "M:" + destino[2:]          # no Domínio o C: local aparece como M:


def main():
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto")
    antes = os.path.getmtime(destino) if os.path.exists(destino) else 0
    # outras pastas de cliente: se algum Plano de contas.txt mudar durante a exportação, o Domínio gravou no lugar errado
    raiz = os.path.dirname(os.path.normpath(pasta))
    outros = {}
    for d in os.listdir(raiz):
        f = os.path.join(raiz, d, "Plano de contas.txt")
        if os.path.normpath(os.path.join(raiz, d)) != os.path.normpath(pasta) and os.path.exists(f):
            outros[f] = os.path.getmtime(f)
    foco(h, maximizar=True)
    time.sleep(0.5)
    clicar(h, 620, 66)           # Utilitários
    time.sleep(1)
    clicar(h, 634, 626)          # Exportação
    time.sleep(1)
    clicar(h, 1105, 658)         # Contas
    time.sleep(2)
    log("diálogo Contas aberto")

    # O campo "Nome do arquivo" vem com a ÚLTIMA pasta usada: confere por OCR e, se não for a do cliente, troca.
    toks = [w for w in os.path.basename(os.path.normpath(pasta)).split() if w != "-"]
    cod, palavra = toks[0], toks[-1].upper()      # o campo rola: só o fim do caminho aparece
    def campo_ok():
        txt = " ".join(ler_area((690, 598, 560, 32), 3).split()).upper()
        log(f"campo Nome do arquivo: '{txt}'")
        return "CONTAS.TXT" in txt.replace(" ", "").replace("CONTAS .TXT","CONTAS.TXT")   # campo rola: só o fim do caminho aparece
    if not campo_ok():
        clicar(h, 1127, 613)     # campo "Nome do arquivo"
        time.sleep(0.4)
        limpar_campo(h, 260)
        digitar_texto(h, remoto)
        time.sleep(1)
        if not campo_ok():
            capturar("erro_plano_contas.png", reduzir=(960, 540))
            sys.exit(f"Campo do arquivo não ficou na pasta do cliente ({cod}). NÃO exportei.")
    capturar("contas_dialogo.png", regiao=(680, 390, 570, 370))     # conferência
    clicar(h, 1075, 714)         # Exportar
    log("Exportar clicado")

    fim = time.time() + 30
    ok = False
    while time.time() < fim:
        if os.path.exists(destino) and os.path.getmtime(destino) > antes and os.path.getsize(destino) > 0:
            ok = True
            break
        time.sleep(0.5)
    time.sleep(2)                # aparece o aviso "Fim da exportação das contas!"
    clicar(h, 1056, 604)         # OK no aviso (um clique só; clicar mais faz o aviso reabrir)
    time.sleep(1)
    clicar(h, 1180, 714)         # Cancelar fecha o diálogo (o Domínio não fecha sozinho)
    if not ok:
        capturar("erro_plano_contas.png", reduzir=(960, 540))
        sys.exit(f"Arquivo não foi gravado em 30 s: {destino}")
    errados = [f for f, m in outros.items() if os.path.exists(f) and os.path.getmtime(f) != m]
    if errados:
        sys.exit(f"ATENÇÃO: o Domínio também alterou {errados}. Confira e restaure de 99 Originais e duplicados.")
    log(f"salvo: {destino} ({os.path.getsize(destino)} bytes)")


main()
