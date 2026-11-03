r"""Exporta o relatório aberto (Balancete ou Razão) para Excel (.xlsx) na pasta do cliente.

Uso: python exportar_excel.py <pasta_cliente> [nome_arquivo]
  <pasta_cliente>: ex. ...\IMPORTAÇÃO DOMINIO\043 - OXFORD FORTUNE
  [nome_arquivo]: Balancete.xlsx (padrão) ou Razão.xlsx
Pré-requisito: relatório aberto (balancete.py / razao.py).

Padrão (sem depender de posição na tela): ícone Excel -> espera a JANELA "Selecione o arquivo" pelo título ->
cliques RELATIVOS à janela: tipo *.xlsx -> no "File name" digita o CAMINHO COMPLETO (M:\...\<pasta>\<nome>), o que
garante a pasta sem navegar -> Enter -> se perguntar se substitui, 'y' -> confere o arquivo novo no disco.
"""
import ctypes
import os
import sys
import time

import pyautogui
import win32gui

from dominio_lib import achar_sistema, achar_titulo, capturar, clicar, digitar_texto, foco, janelas_remotas, log, tecla

pasta = sys.argv[1]
nome = sys.argv[2] if len(sys.argv) > 2 else "Balancete.xlsx"
destino = os.path.join(pasta, nome)
remoto = "M:" + os.path.splitdrive(destino)[1]          # o C: local aparece como M: no Domínio

# posições DENTRO da janela "Selecione o arquivo" (medidas em 29/10/2026; a janela pode abrir em qualquer lugar)
TIPO_SETA = (541, 491)
NOME = (390, 457)


def esperar_janela(titulo, limite=30):
    fim = time.time() + limite
    while time.time() < fim:
        j = achar_titulo(titulo)
        if j and not ctypes.windll.user32.IsHungAppWindow(j):
            return j
        time.sleep(0.5)
    return None


def main():
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto")
    antes = os.path.getmtime(destino) if os.path.exists(destino) else 0
    ja_aberto = achar_titulo("Selecione o arquivo")
    if ja_aberto:
        log("diálogo 'Selecione o arquivo' já estava aberto: não clico no ícone Excel")
    foco(h, maximizar=True) if not ja_aberto else None
    time.sleep(0.5)
    # trava: o relatório aberto tem de ser o do arquivo pedido (senão salvaria o Balancete com nome de Razão)
    import ocr
    esperado = "RAZ" if nome.lower().startswith("raz") else "BALANCETE"
    tela = " ".join(w[0] for w in ocr.palavras(pyautogui.screenshot())).upper()
    if not ja_aberto and (esperado not in tela) or not ja_aberto and (esperado == "RAZ" and "BALANCETE" in tela and "RAZÃO" not in tela and "RAZAO" not in tela):
        capturar("erro_excel.png", reduzir=(960, 540))
        sys.exit(f"O relatório aberto não é o de {nome}. NÃO exportei.")
    # ícone Excel na barra lateral do relatório: achado pela IMAGEM (a barra muda de lugar se o relatório não está maximizado)
    pos = None
    try:
        if ja_aberto: raise RuntimeError
        pos = pyautogui.locateCenterOnScreen(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone_excel.png"))
    except Exception:
        pos = None
    if not ja_aberto:
        clicar(h, *(pos or (40, 380)))
        log(f"ícone Excel em {tuple(pos) if pos else '(40, 380) (posição antiga)'}")
    d = esperar_janela("Selecione o arquivo")
    if not d:
        capturar("erro_excel.png", reduzir=(960, 540)); sys.exit("Janela 'Selecione o arquivo' não abriu em 30 s")
    time.sleep(1.5)
    l, t, _, _ = win32gui.GetWindowRect(d)
    foco(d)
    clicar(d, l + TIPO_SETA[0], t + TIPO_SETA[1]); time.sleep(1)      # lista "Save as type"
    tecla(d, "down"); time.sleep(0.4); tecla(d, "enter"); time.sleep(1.5)   # *.xls -> *.xlsx
    # A PASTA É A DO "Save in" (o diálogo abre na última pasta usada): confere pelo OCR que é a do cliente e digita SÓ O NOME
    # do arquivo (caminho completo no campo "File name" dá "file name is not valid"; ver NOTAS.md).
    import ocr
    reg = pyautogui.screenshot(region=(max(l, 0), max(t, 0), 760, 420))  # topo do diálogo (Save in)
    topo = " ".join(w[0] for w in ocr.palavras(reg)).upper()
    cliente = os.path.basename(os.path.normpath(pasta)).upper()
    chave = cliente.split(" - ")[0]  # número NNN do cliente
    nome_cli = cliente.split(" - ", 1)[-1].split()[0]
    # o OCR não lê bem o combo "Save in"; vale o número OU a listagem típica de pasta de cliente (99 ... DUPLICADOS e Documentos <NOME>)
    if not (chave in topo or ("DUPLICADOS" in topo and nome_cli in topo)):
        capturar("erro_excel.png", reduzir=(960, 540))
        sys.exit(f"'Save in' não mostra a pasta do cliente ({cliente}); navegue por clique até ela. NÃO salvei.")
    # NÃO reescrever o nome (regra dela, 03/11/2026): o diálogo já troca o nome sozinho; salva com ele e,
    # depois, renomeia o arquivo no disco para o nome padrão.
    capturar("excel_dialogo.png", regiao=(l, t, 701, 518))
    inicio = time.time()
    tecla(d, "enter")
    log("salvar com o nome sugerido pelo diálogo; renomeio no disco depois")

    fim = time.time() + 40
    while time.time() < fim:
        novos = [f for f in os.listdir(pasta) if f.lower().endswith((".xlsx", ".xls")) and os.path.getmtime(os.path.join(pasta, f)) >= inicio - 2
                 and os.path.getsize(os.path.join(pasta, f)) > 0 and f != nome]
        if novos:
            time.sleep(1.5)
            if os.path.exists(destino): os.remove(destino)
            os.rename(os.path.join(pasta, novos[0]), destino)
        if os.path.exists(destino) and os.path.getmtime(destino) > antes and os.path.getsize(destino) > 0:
            log(f"salvo: {destino} ({os.path.getsize(destino)} bytes)")
            return
        for j, tt in janelas_remotas():   # "já existe. Deseja substituí-lo?" -> Yes
            if tt and tt not in ("Lista de Programas", "Selecione o arquivo") and j != h:
                foco(j); pyautogui.press("y"); log(f"'{tt}': Yes"); time.sleep(2)
        time.sleep(0.5)
    capturar("erro_excel.png", reduzir=(960, 540))
    sys.exit(f"Arquivo não foi gravado em 40 s: {destino}")


main()
