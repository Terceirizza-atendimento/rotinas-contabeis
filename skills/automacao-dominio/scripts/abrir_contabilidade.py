"""Passos 2 e 3: Lista de Programas -> Contabilidade -> login do sistema -> sistema aberto.

Uso: DW_SYS_USER=LETICIA DW_SYS_PASS=... python abrir_contabilidade.py
Captura de tela só em caso de erro.
"""
import os
import sys
import time

import pyautogui
import win32gui

from dominio_lib import (achar_sistema, achar_titulo, capturar, clicar, digitar, esperar,
                         foco, limpar_campo, log, tecla)


def main():
    lista = esperar(lambda: achar_titulo("Lista de Programas"), limite=60)
    if not lista:
        capturar("erro_sem_lista.png", reduzir=(960, 540))
        sys.exit("Lista de Programas não apareceu")
    foco(lista)
    clicar(lista, 864, 290)          # ícone Contabilidade (duplo clique não abre)
    tecla(lista, "enter")
    log("Contabilidade + Enter")

    dlg = esperar(lambda: achar_titulo("Conectando"), limite=90)
    if not dlg:
        capturar("erro_sem_dialogo.png", reduzir=(960, 540))
        sys.exit("Diálogo 'Conectando ...' não apareceu")
    log("diálogo 'Conectando ...' apareceu")
    time.sleep(1.5)
    foco(dlg)
    # o diálogo não abre sempre no mesmo lugar (já veio 140 px mais baixo): coordenadas relativas ao canto dele
    x0, y0 = win32gui.GetWindowRect(dlg)[:2]
    clicar(dlg, x0 + 234, y0 + 58)   # usuário
    limpar_campo(dlg, 40)            # o diálogo vem com usuário/senha errados: apagar antes (Ctrl+A não funciona)
    digitar(dlg, os.environ["DW_SYS_USER"])
    clicar(dlg, x0 + 234, y0 + 96)   # senha
    limpar_campo(dlg, 40)
    digitar(dlg, os.environ["DW_SYS_PASS"])
    time.sleep(0.5)
    capturar("dialogo_login.png", regiao=(x0, y0, 388, 204))   # conferência (usuário + 6 asteriscos)
    clicar(dlg, x0 + 186, y0 + 176)  # OK
    log("OK clicado")

    sistema = esperar(achar_sistema, limite=120, passo=0.5)
    if not sistema:
        capturar("erro_sem_sistema.png", reduzir=(960, 540))
        sys.exit("Janela do sistema não apareceu")
    time.sleep(1.5)
    foco(sistema, maximizar=True)
    log(f"sistema aberto (hwnd {sistema})")


main()
