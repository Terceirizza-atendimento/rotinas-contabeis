"""Importa o CSV de lançamentos do cliente no Domínio (Favoritos > Importação csv).

Uso: python importar_csv.py "<pasta do cliente>" [--gravar]
Pré-requisito: Contabilidade aberta, empresa certa ativa.

Sem --gravar: abre a importação, lê o arquivo até o "Resumo dos Dados" e sai respondendo No (nada é gravado).
Serve de ensaio.
Com --gravar: clica Gravar e confirma; o aviso "erros de estrutura" aparece sempre por causa do cabeçalho do
CSV (linha 00001) e é confirmado. Depois de gravar NUNCA rodar de novo (duplica os lançamentos).

Três categorias de janela nesta tela, cada uma com seu próprio hwnd para focar antes de clicar:
  - "Importação de Arquivo": painel desenhado DENTRO da janela única do sistema (achar_sistema()), sem
    hwnd próprio. Favoritos/Importação csv, Conjunto de dados, Importar e Gravar ficam aqui.
  - "Seleção de arquivos": janela nativa própria (achar_titulo), aberta pelos "..." do Caminho. O filtro de
    tipo, a marcação do CSV e o "OK da seleção" ficam aqui.
  - "Procurar Pasta": janela nativa própria (achar_titulo), aberta pelos "..." DENTRO da Seleção de arquivos.
    É aqui que se navega a árvore de pastas (Client C (M:) > Users > atend > ... > <cliente>).
Bug corrigido em 30/10/2026: a versão antiga desta automação focava sempre achar_sistema() para clicar nas
duas janelas nativas acima — o clique saía certo na coordenada da TELA, mas o foco ficava na janela errada,
então o Windows entregava o clique/tecla para o painel principal em vez da janela nativa (ela podia nem estar
em primeiro plano). Por isso a digitação de caminho (digitar_caminho, removida) também corrompia o texto: o
SendInput ia para a janela ativa errada. Daqui pra frente, caminho é sempre por clique na árvore de pastas,
nunca digitado.
Avisos do Google Drive ("arquivos removidos de pasta compartilhada") podem cobrir os botões Gravar/Cancelar: o
script clica o OK do aviso antes; se reaparecer, feche-o à mão. Ritmo lento de propósito: a Domínio trava com
muitos cliques. Capturas: saida\\imp_*.png (conferir a empresa/CNPJ, o conjunto de dados e o Resumo antes de
gravar).
"""
import sys
import time

import os
import unicodedata

import pyautogui

import ocr
from dominio_lib import achar_sistema, achar_titulo, capturar, clicar, foco, log, tecla

PAUSA = 6          # s entre cliques (janelas de importação respondem devagar)


def passo(h, x, y, descricao, espera=PAUSA):
    log(descricao)
    clicar(h, x, y)
    time.sleep(espera)


def _n(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().upper()


def tela():
    return ocr.palavras(pyautogui.screenshot())


def tela_ampliada():
    """OCR da área da árvore do 'Procurar Pasta' ampliada 3x (o OCR normal perde palavras curtas como 'Users')."""
    from PIL import Image
    x0, y0 = 690, 410
    im = pyautogui.screenshot(region=(x0, y0, 560, 240))
    big = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    return [(tx, x0 + x / 3, y0 + y / 3, w / 3, hh / 3) for tx, x, y, w, hh in ocr.palavras(big)]


def texto_tela():
    return " ".join(w[0] for w in tela())


def esperar_titulo(prefixo, limite=30):
    """hwnd da primeira janela remota cujo título comece com `prefixo` ('Seleção de arquivos', 'Procurar Pasta')."""
    fim = time.time() + limite
    while time.time() < fim:
        h = achar_titulo(prefixo)
        if h:
            return h
        time.sleep(0.5)
    return None


def nivel(h, rotulo, y_min, x_min=0):
    """Acha na árvore do 'Procurar Pasta' (janela h) o rótulo (1ª palavra) abaixo de y_min; rola a árvore se
    preciso. Seleciona (clique) e expande (seta direita). Devolve (x, y) do rótulo."""
    for _ in range(14):
        for tx, x, y, w, hh in tela() + tela_ampliada():
            if _n(tx).startswith(_n(rotulo)) and y > y_min and x >= x_min:
                clicar(h, int(x + w / 2), int(y + hh / 2)); time.sleep(1.2)
                tecla(h, "right"); time.sleep(2.5)
                return x, y
        pyautogui.scroll(-400, 960, 600); time.sleep(1.5)
    capturar("erro_procurar_pasta.png", reduzir=(960, 540))
    raise SystemExit(f"Procurar Pasta: não achei '{rotulo}'")


def ancora(h, palavra, dx, dy=0, descricao=""):
    """Clica a (dx, dy) da borda ESQUERDA de uma palavra lida por OCR (a janela muda de lugar entre sessões).
    `h` precisa ser o hwnd da janela que DEVE receber o clique (foco() é chamado antes, dentro de clicar())."""
    for tx, x, y, w, hh in tela():
        if tx.lower().startswith(palavra.lower()):
            log(descricao or f"clique relativo a '{palavra}'")
            clicar(h, int(x + dx), int(y + hh / 2 + dy)); return True
    return False


def selecionar_conjunto(h):
    """Combo 'Conjunto de dados' abre em 'Ato Cotepe 17/04': abre a lista e escolhe, por OCR, a linha
    'Lançamentos Contábeis (Partida Simples/Múltiplas) (3.1) (2) (Excel (3.1) (2))'. Fica no painel principal
    (achar_sistema()), não tem hwnd próprio."""
    cb = next(((x, y, w, hh) for tx, x, y, w, hh in tela() if tx.lower().startswith("cotepe")), None)
    if not cb:
        capturar("erro_conjunto.png", reduzir=(960, 540)); sys.exit("Combo 'Conjunto de dados' não achado por OCR")
    clicar(h, int(cb[0] + 200), int(cb[1] + cb[3] / 2)); time.sleep(2)
    for _ in range(12):
        linhas = {}
        for tx, x, y, w, hh in tela():
            linhas.setdefault(round(y / 8), []).append((x, tx))
        for k, ws in linhas.items():
            s = " ".join(tx for _, tx in sorted(ws))
            if "Simples" in s and "(2)" in s and "Excel" in s:
                x0 = min(x for x, _ in ws)
                clicar(h, int(x0 + 150), int(k * 8 + 6)); time.sleep(2)
                return
        pyautogui.scroll(-300, 700, 450); time.sleep(1.2)
    capturar("erro_conjunto.png", reduzir=(960, 540))
    sys.exit("Linha 'Lançamentos Contábeis (Partida Simples/Múltiplas) (3.1) (2) (Excel (3.1) (2))' não achada na lista")


def csv_esperado(pasta_csv):
    """Início do nome (minúsculo) do ÚNICO CSV em 02 Pendente de importar; aborta se houver 0 ou mais de 1."""
    csvs = [f for f in os.listdir(pasta_csv) if f.lower().endswith(".csv")]
    if len(csvs) != 1:
        sys.exit(f"02 Pendente de importar deve ter exatamente 1 CSV (tem {len(csvs)}). NÃO importei.")
    return os.path.splitext(csvs[0])[0][:12].lower()


def limpar_dialogos():
    """Fecha janelas empilhadas da importação (Procurar Pasta, Seleção de arquivos, Importação de Arquivo),
    cada uma focada pelo seu próprio hwnd."""
    for _ in range(6):
        h_proc = achar_titulo("Procurar Pasta")
        h_sel = achar_titulo("Seleção de arquivos") or achar_titulo("Selecao de arquivos")
        h = h_proc or h_sel
        if h:
            foco(h)
            cs = [p for p in tela() if p[0] == "Cancelar"]
            alvo = min(cs, key=lambda p: p[2]) if cs else None
            if alvo:
                clicar(h, int(alvo[1] + alvo[3] / 2), int(alvo[2] + alvo[4] / 2)); time.sleep(3); continue
            return
        h_sys = achar_sistema()
        foco(h_sys)
        txt = texto_tela()
        if "Importação" in txt and "Arquivo" in txt:
            alvo = next((p for p in tela() if p[0] == "Fechar" and p[2] > 700), None)
            if alvo:
                clicar(h_sys, int(alvo[1] + alvo[3] / 2), int(alvo[2] + alvo[4] / 2)); time.sleep(3); continue
        return


def navegar_procurar_pasta(h_proc, partes):
    """Dentro de 'Procurar Pasta' (hwnd próprio h_proc): seleciona a unidade Client C (M:) se preciso e desce
    a árvore por clique + seta direita, parte por parte, até a última entrada de `partes`. Confirma com OK."""
    foco(h_proc)
    if "Client C" not in texto_tela().replace("(", " "):   # só troca de unidade se a atual não for Client C (M:)
        if not ancora(h_proc, "Unidade", 532, 0, "Unidade: abre a lista"):
            sys.exit("Unidade não achada")
        time.sleep(2.5)
        # a lista abre com Servidor (C:), Client C (M:), Client G (N:); o OCR confundia a linha (escolheu Client G): usa a
        # posição da 2ª linha, ~(+86, +41) px do rótulo "Unidade" (confirmado ao vivo em 30/10/2026)
        if not ancora(h_proc, "Unidade", 86, 41, "Unidade: Client C (M:) por posição"):
            capturar("erro_procurar_pasta.png", reduzir=(960, 540)); sys.exit("'Client C (M:)' não achado na lista de unidades")
        time.sleep(4)
    y = 0
    for parte in partes:
        rotulo = parte.split()[0]
        _, y = nivel(h_proc, rotulo, y)
        log(f"Procurar Pasta: {parte}")
    capturar("imp_pasta_escolhida.png", reduzir=(960, 540))
    for tx, x, yy, w, hh in tela():                  # botão OK do Procurar Pasta
        if tx == "OK" and yy > y:
            clicar(h_proc, int(x + w / 2), int(yy + hh / 2)); time.sleep(6); return
    sys.exit("botão OK do Procurar Pasta não achado")


def escolher_pasta(h_sys, caminho):
    """'...' do Caminho (painel principal) -> 'Seleção de arquivos' (hwnd próprio) -> '...' dela -> 'Procurar
    Pasta' (hwnd próprio) -> navega a árvore até a pasta pedida -> OK. Cada janela é focada pelo seu próprio
    hwnd (achar_titulo), nunca por achar_sistema() — é o bug que fazia os cliques saírem na janela errada."""
    partes_cliente = [p for p in os.path.normpath(caminho).split(os.sep)[1:]]   # sem o 'C:' (vira Client C (M:))
    if not ancora(h_sys, "Caminho", 976, 0, '"..." do Caminho (abre Seleção de arquivos)'):
        capturar("erro_procurar_pasta.png", reduzir=(960, 540)); sys.exit("Janela Importação de Arquivo não achada por OCR")
    h_sel = esperar_titulo("Seleção de arquivos") or esperar_titulo("Selecao de arquivos")
    if not h_sel:
        capturar("erro_procurar_pasta.png", reduzir=(960, 540)); sys.exit("'Seleção de arquivos' não abriu em 30 s")
    foco(h_sel)
    for tentativa in range(3):                       # o 1º clique pode só ativar a janela
        if not ancora(h_sel, "Demonstr", 727, -35, f'"..." do Caminho da Seleção (abre Procurar Pasta), tentativa {tentativa + 1}'):
            capturar("erro_procurar_pasta.png", reduzir=(960, 540)); sys.exit("Seleção de arquivos: campo Caminho não achado por OCR")
        h_proc = esperar_titulo("Procurar Pasta", limite=32)
        if h_proc:
            break
    else:
        capturar("erro_procurar_pasta.png", reduzir=(960, 540)); sys.exit("Procurar Pasta não abriu")
    navegar_procurar_pasta(h_proc, partes_cliente)
    return h_sel


def main():
    gravar = "--gravar" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta_csv = os.path.join(args[0], "Arquivos de importação", "02 Pendente de importar") if args else None
    if not pasta_csv:
        sys.exit("Uso: importar_csv.py \"<pasta do cliente>\" [--gravar]  (a pasta é obrigatória: a janela lembra a de outro cliente)")
    h = achar_sistema()
    if not h:
        sys.exit("Sistema da Domínio não está aberto")
    foco(h, maximizar=True)
    time.sleep(1)
    limpar_dialogos()

    passo(h, 721, 66, "Favoritos", 3)
    passo(h, 732, 182, "Importação csv", 8)
    capturar("imp_1_janela.png", reduzir=(960, 540))             # empresa/CNPJ, TXT, conjunto de dados, opção
    if "Simples" not in texto_tela():
        selecionar_conjunto(h)
        capturar("imp_1b_conjunto.png", reduzir=(960, 540))
        if "Simples" not in texto_tela():
            sys.exit("Conjunto de dados não ficou em 'Lançamentos Contábeis (Partida Simples/Múltiplas)': escolha à mão e rode de novo")

    h_sel = escolher_pasta(h, pasta_csv)
    foco(h_sel)
    if "Não existem" in texto_tela():
        passo(h_sel, 1006, 754, "OK do aviso 'Não existem arquivos TXT' (pasta nova)", 4)
    passo(h_sel, 890, 832, 'lista "Tipo" da seleção', 3)
    log("Tipo: Todos os arquivos (*.*)")
    tecla(h_sel, "down")
    tecla(h_sel, "enter")
    time.sleep(8)
    foco(h_sel)
    capturar("imp_2_selecao.png", reduzir=(960, 540))            # o CSV deve aparecer na lista
    txt = texto_tela().lower()
    if csv_esperado(pasta_csv) not in txt:
        sys.exit("O CSV pendente do cliente não aparece na lista da pasta escolhida. NÃO importei.")
    escuro = sum(1 for px in pyautogui.screenshot(region=(636, 592, 12, 12)).getdata() if max(px[:3]) < 110)
    if escuro < 5:                                               # caixa da 1ª linha vazia: marcar
        passo(h_sel, 642, 598, "marcar o CSV", 4)
    else:
        log("CSV já marcado")
    capturar("imp_2b_marcado.png", reduzir=(960, 540))
    passo(h_sel, 1186, 910, "OK da seleção", 8)

    h = achar_sistema()
    foco(h, maximizar=True)
    capturar("imp_3_apos_selecao.png", reduzir=(960, 540))
    passo(h, 1326, 930, "Importar", 15)
    capturar("imp_4_resumo.png", reduzir=(960, 540))             # Resumo dos Dados: 55 lançamentos?

    passo(h, 1518, 970, "fechar aviso do Google Drive, se cobrir os botões (OK dele)", 2)
    if not gravar:
        log("ensaio: Esc pede 'Deseja gravar os dados?' -> No (NUNCA Yes)")
        tecla(h, "esc")
        time.sleep(6)
        capturar("imp_5_pergunta.png", reduzir=(960, 540))
        passo(h, 970, 604, "No (nada gravado)", 6)
        passo(h, 1420, 930, "Fechar a janela de importação", 5)
        capturar("imp_5_fim.png", reduzir=(960, 540))
        log("ensaio concluído; use --gravar para gravar")
        return

    passo(h, 1742, 988, "Gravar", 8)
    capturar("imp_5_confirma.png", reduzir=(960, 540))           # aviso de erros de estrutura (cabeçalho)
    passo(h, 1008, 604, "Yes (confirma gravar)", 10)
    capturar("imp_6_aviso.png", reduzir=(960, 540))              # 'Dados gravados com sucesso! N registro(s)'
    tecla(h, "enter")                                            # OK do aviso
    time.sleep(4)
    capturar("imp_7_fim.png", reduzir=(960, 540))
    log("gravado: conferir imp_6_aviso.png; mover o CSV para 01 Importados e reexportar Balancete/Razão")


main()
