"""Integração do fiscal e da folha no contábil (condicional, antes de exportar balancete/razão).

Uso: DW_SYS_USER=LETICIA DW_SYS_PASS=... python integracao.py <competencia MMAAAA | MMAAAA-MMAAAA> [--fiscal] [--folha] [--simular]
  competencia  mês do fechamento, ex.: 102026 (outubro/2026)
  --fiscal / --folha  só um dos módulos (padrão: os dois)
  --simular    preenche tudo e captura a tela, mas NÃO clica em Gerar/Regerar
  --gravar     além de Gerar/Regerar, clica Gravar e os OK/Yes/Continuar dos avisos (sem ele o script PARA depois
               de Gerar/Regerar e imprime 'GRAVAR PENDENTE': nada fica gravado)

Pré-requisito: Contabilidade aberta e logada (abrir_contabilidade.py) com a empresa certa ativa.
Navega entre módulos pelo painel do logo DOMÍNIO, na janela já aberta (não abre instâncias novas, a não ser que
o módulo ainda não esteja aberto), e termina de volta no módulo Contabilidade.

Fiscal: Movimentos > Integração Contábil (período, Gerar) e Utilitários > Regerar > Lançamentos Contábeis
(período, Entradas/Saídas/Serviços, Regerar). Folha: Processos > Integração Contábil (competência, Gerar).
Depois de cada botão o script espera e captura a tela (pasta saida, int_*.png): ERRO de débito/crédito aparece ali.
Nesse caso criar as contas de clientes/fornecedores (ver skill) e rodar de novo só o regerar.
Coordenadas medidas em 29/10/2026 (1920x1080, janela maximizada), a partir do Gerar/Regerar/Gravar feitos à mão
pelos agentes (empresa 75). **`--gravar` já rodou de ponta a ponta e gravou de verdade na LICITOCON (013,
30/10/2026, competência 04-09/2026, 183s)**: Gerar/Regerar/Gravar e os avisos ficaram confirmados ao vivo.
"""
import calendar
import os
import sys
import time

import win32gui

from dominio_lib import (achar_sistema, capturar, clicar, digitar, esperar, foco, janelas_remotas,
                         limpar_campo, log, tecla)

PAINEL_LOGO = (60, 96)       # clicar no logo DOMÍNIO abre o painel de módulos (à esquerda, leva ~3 s)
PAINEL = {"folha": (114, 240), "fiscal": (114, 312), "contabilidade": (114, 384)}


def novas(antes):
    return [(h, t) for h, t in janelas_remotas() if h not in antes]


def login_sistema(dlg):
    time.sleep(1.5)
    foco(dlg)
    x0, y0 = win32gui.GetWindowRect(dlg)[:2]     # o diálogo muda de lugar: coordenadas relativas
    clicar(dlg, x0 + 234, y0 + 58); limpar_campo(dlg, 40); digitar(dlg, os.environ["DW_SYS_USER"])
    clicar(dlg, x0 + 234, y0 + 96); limpar_campo(dlg, 40); digitar(dlg, os.environ["DW_SYS_PASS"])
    clicar(dlg, x0 + 186, y0 + 176)


def ir_para(h, nome):
    """Troca de módulo pelo painel do logo DOMÍNIO, dentro da janela aberta (sem abrir outra instância).
    Só se o módulo ainda não estiver aberto o sistema pede login (feito aqui). Devolve o hwnd do módulo."""
    antes = {x for x, _ in janelas_remotas()}
    foco(h)
    clicar(h, *PAINEL_LOGO)
    time.sleep(3)
    clicar(h, *PAINEL[nome])
    dlg = esperar(lambda: next((x for x, t in novas(antes) if t.startswith("Conectando")), None), limite=8)
    if dlg:                                       # módulo ainda não estava aberto
        login_sistema(dlg)
        mod = esperar(lambda: next((x for x, t in novas(antes) if t == "" and win32gui.GetWindowRect(x)[2] > 1900), None),
                      limite=120, passo=0.5)
        if not mod:
            capturar(f"erro_{nome}_sem_janela.png", reduzir=(960, 540))
            sys.exit(f"janela do {nome} não apareceu")
        time.sleep(20)                            # splash + carga do módulo
    else:
        time.sleep(4)
        mod = win32gui.GetForegroundWindow()      # a janela do módulo já aberta vem para a frente
    foco(mod, maximizar=True)
    log(f"{nome}: hwnd {mod}")
    return mod


def menu(h, x, y, espera=2.5):
    clicar(h, x, y)
    time.sleep(espera)


def campo(h, x, y, texto):
    clicar(h, x, y)
    limpar_campo(h, 12)
    digitar(h, texto, 0.05)


def avisos_novos(antes, yes=(80, 152), ok=(1104, 604), espera=2):
    """Responde às janelas novas: título 'Aviso' -> OK; janela sem título ('Deseja gravar dados?') -> Yes."""
    time.sleep(espera)
    for x, t in novas(antes):
        foco(x)
        if t.startswith("Aviso"):
            clicar(x, *ok); log("Aviso: OK")
        elif t == "":
            clicar(x, *yes); log("Deseja gravar dados?: Yes")
        time.sleep(3)


def fiscal(h0, mmaaaa, simular, gravar=False):
    ini_c, fim_c = mmaaaa.split("-") if "-" in mmaaaa else (mmaaaa, mmaaaa)    # intervalo MMAAAA-MMAAAA ou um mês
    mes, ano = int(fim_c[:2]), int(fim_c[2:])
    ini = f"01{int(ini_c[:2]):02d}{int(ini_c[2:])}"
    fim = f"{calendar.monthrange(ano, mes)[1]:02d}{mes:02d}{ano}"
    h = ir_para(h0, "fiscal")

    # 1) Movimentos > Integração Contábil
    foco(h); menu(h, 395, 66); menu(h, 424, 502, 3)
    campo(h, 770, 490, ini_c); campo(h, 770, 522, fim_c)
    capturar("int_fiscal_integracao.png", reduzir=(960, 540))
    if simular:
        clicar(h, 1226, 552)                     # Fechar
    else:
        clicar(h, 1226, 472)                     # Gerar...
        log("Integração Contábil: Gerar clicado")
        time.sleep(12)
        capturar("int_fiscal_integracao_depois.png", reduzir=(960, 540))   # janela "Lançamentos gerados"
        if not gravar:
            print("GRAVAR PENDENTE: fiscal gerado, nada gravado (rode com --gravar ou grave à mão)")
            return h
        clicar(h, 1424, 986); log("Lançamentos gerados: Gravar"); time.sleep(8)
        capturar("int_fiscal_integracao_gravado.png", reduzir=(960, 540))  # aviso "Integração com a contabilidade concluída"
        clicar(h, 1094, 604); log("OK do aviso"); time.sleep(3)
        clicar(h, 1226, 552); log("Fechar Integração Contábil")
    time.sleep(2)

    # 2) Utilitários > Regerar > Lançamentos Contábeis
    foco(h); menu(h, 620, 66); menu(h, 724, 868); menu(h, 1360, 870, 3)
    campo(h, 620, 250, ini); campo(h, 620, 282, fim)
    for y in (401, 425, 449):                    # Entradas, Saídas, Serviços
        clicar(h, 439, y)
    time.sleep(0.5)
    capturar("int_fiscal_regerar.png", reduzir=(960, 540))
    if simular:
        clicar(h, 1457, 315)                     # Fechar
    else:
        antes = {x for x, _ in janelas_remotas()}
        clicar(h, 1457, 235)                     # Regerar
        log("Regerar clicado")
        time.sleep(15)
        capturar("int_fiscal_regerar_depois.png", reduzir=(960, 540))      # "Final do Processo" (ou erro de débito/crédito)
        if not gravar:
            print("GRAVAR PENDENTE: fiscal regerado, nada gravado (rode com --gravar ou grave à mão)")
            return h
        clicar(h, 1080, 604); log("OK do Final do Processo"); time.sleep(3)
        clicar(h, 1457, 315); log("Fechar Regerar (pergunta 'Deseja gravar dados?')")
        avisos_novos(antes, espera=6)            # Yes na pergunta
        avisos_novos(antes, espera=4)            # OK em "Lançamentos contábeis gravados com sucesso"
        capturar("int_fiscal_regerar_gravado.png", reduzir=(960, 540))
    return h


def folha(h0, mmaaaa, simular, gravar=False):
    ini_c, fim_c = mmaaaa.split("-") if "-" in mmaaaa else (mmaaaa, mmaaaa)
    h = ir_para(h0, "folha")
    menu(h, 376, 66); menu(h, 416, 880, 3)
    campo(h, 700, 468, ini_c); campo(h, 700, 500, fim_c)
    capturar("int_folha_integracao.png", reduzir=(960, 540))
    if simular:
        clicar(h, 1290, 580)                     # Fechar
    else:
        clicar(h, 1290, 460)                     # Gerar...
        log("Folha: Gerar clicado")
        time.sleep(15)
        capturar("int_folha_integracao_depois.png", reduzir=(960, 540))    # janela "Integração com a Contabilidade"
        if not gravar:
            print("GRAVAR PENDENTE: folha gerada, nada gravado (rode com --gravar ou grave à mão)")
            return h
        clicar(h, 1128, 812); log("Folha: Gravar"); time.sleep(6)
        capturar("int_folha_avisos.png", reduzir=(960, 540))               # 'Avisos: período com lançamentos já gravados'?
        clicar(h, 1140, 766); log("Continuar (se houve o aviso de período já gravado)"); time.sleep(8)
        clicar(h, 1132, 604); log("OK 'concluída com sucesso'"); time.sleep(3)
        capturar("int_folha_gravado.png", reduzir=(960, 540))
        clicar(h, 1292, 580); log("Fechar Integração Contábil da folha")
    return h


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    partes = args[0].split("-") if len(args) == 1 else []
    if not partes or len(partes) > 2 or any(len(x) != 6 or not x.isdigit() for x in partes):
        sys.exit(__doc__)
    mmaaaa, simular, gravar = args[0], "--simular" in flags, "--gravar" in flags
    ambos = not ({"--fiscal", "--folha"} & flags)
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto (rode abrir_contabilidade.py)")
    if ambos or "--fiscal" in flags:
        h = fiscal(h, mmaaaa, simular, gravar)
    if ambos or "--folha" in flags:
        h = folha(h, mmaaaa, simular, gravar)
    ir_para(h, "contabilidade")                  # volta ao módulo contábil, onde se faz o resto
    log("concluído" + (" (simulação: nada foi gerado)" if simular else " (gravado)" if gravar else " (SEM --gravar: GRAVAR PENDENTE)"))


main()
