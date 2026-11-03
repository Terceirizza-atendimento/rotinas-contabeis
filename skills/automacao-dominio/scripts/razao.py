"""Favoritos -> Razão -> datas -> OK (gera o relatório).

Uso: python razao.py [data_inicial ddmmaaaa] [data_final ddmmaaaa]
Pré-requisito: sistema aberto (abrir_contabilidade.py), empresa já selecionada.
As duas datas são obrigatórias. Lê o campo por OCR e só digita se for diferente.
"""
import os
import sys
import time

from dominio_lib import abrir_favorito, achar_sistema, capturar, clicar, clicar_texto, data_por_rotulo, exigir_empresa, foco, log


def main():
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto")
    if len(sys.argv) < 3:
        sys.exit("Uso: razao.py ddmmaaaa ddmmaaaa  (as duas datas são obrigatórias)")
    foco(h, maximizar=True)
    time.sleep(0.5)
    if os.environ.get("DOMINIO_EMPRESA"):
        exigir_empresa(os.environ["DOMINIO_EMPRESA"])
    abrir_favorito(h, "Razão", titulo="Razão")     # espera o menu e a janela pelo título (sem tempo fixo)
    log("janela Razão aberta")

    data_por_rotulo(h, "Inicial", sys.argv[1])     # acha o campo pelo rótulo (sem coordenada fixa); só digita se diferente
    data_por_rotulo(h, "Final", sys.argv[2])
    capturar("razao_datas.png", reduzir=(960, 540))                  # conferência
    clicar_texto(h, lambda s: s == "OK", descricao="botão OK")
    log("OK clicado; aguardando relatório")
    time.sleep(8)
    capturar("razao_relatorio.png", reduzir=(960, 540))


main()
