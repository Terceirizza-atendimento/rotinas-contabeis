"""Passos 4 e 5: Favoritos -> Balancete -> datas -> OK (gera o relatório).

Uso: python balancete.py [data_inicial ddmmaaaa] [data_final ddmmaaaa]
Pré-requisito: sistema aberto (abrir_contabilidade.py), empresa já selecionada.
"""
import sys
import time

import pyautogui

from dominio_lib import abrir_favorito, achar_sistema, capturar, clicar, clicar_texto, data_por_rotulo, exigir_empresa, foco, log

import os
if len(sys.argv) < 3:
    sys.exit("Uso: balancete.py ddmmaaaa ddmmaaaa  (as duas datas são obrigatórias)")
INICIAL, FINAL = sys.argv[1], sys.argv[2]
EMPRESA = os.environ.get("DOMINIO_EMPRESA")          # código esperado (ex.: 43); confere a barra antes de gerar


def main():
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto")
    foco(h, maximizar=True)
    time.sleep(0.5)
    if EMPRESA:
        exigir_empresa(EMPRESA)
    abrir_favorito(h, "Balancete", titulo="Balancete")     # espera o menu e a janela pelo título (sem tempo fixo)
    log("janela Balancete aberta")

    data_por_rotulo(h, "Inicial", INICIAL)     # acha o campo pelo rótulo (sem coordenada fixa); só digita se diferente
    data_por_rotulo(h, "Final", FINAL)
    time.sleep(0.6)
    capturar("balancete_datas.png", reduzir=(960, 540))                     # conferência
    clicar_texto(h, lambda s: s == "OK", descricao="botão OK")
    log("OK clicado; aguardando relatório")
    time.sleep(5)
    capturar("balancete_relatorio.png", reduzir=(960, 540))


main()
