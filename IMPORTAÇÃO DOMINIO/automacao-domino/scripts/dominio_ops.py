r"""Operações de tela do Domínio validadas ao vivo na 013 (30/10/2026): Alteração de Lançamentos, Exclusão,
Importação csv (Resumo + Gravar) e exportação de Balancete/Razão. Biblioteca (importe; não tem linha de comando).

    import sys; sys.path.insert(0, r"...\automacao-domino\scripts")
    from dominio_ops import *
    abrir_alt(); g = busca_lotes([3027, 3040]); aplicar(debito=210)

Regras de uso (da usuária, 30/10/2026):
  - SEM prints a cada passo: a tela é lida por OCR local (ler) e só se tira print (d.capturar) quando aparecer algo novo.
  - Erro ou aviso que não esteja listado aqui: PARAR e explicar à usuária.
  - Gravar/excluir só com a autorização dela; gravar uma vez só.
  - Coordenadas em "pixels de print 960x540" (a tela real é 1920x1080: c() multiplica por 2). Valem para a janela
    do Domínio como estava em 30/10/2026; se uma tela abrir fora do lugar, tirar UM print e ajustar.

Estado de validação: alteração (busca por lote, vários lotes, valor+débito), exclusão por lote e por conta crédito+data,
importação do CSV pendente e gravação, exportação por exportar_excel.py: VALIDADOS na 013. As funções abaixo foram
reescritas a partir desses passos; na primeira vez de um novo cliente confira o retorno (OCR) antes de gravar.
"""
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import pyautogui  # noqa: E402
import dominio_lib as d  # noqa: E402

S = 2  # print 960x540 -> tela 1920x1080


def c(x, y, esp=1.2):
    """Clique em coordenada de print 960x540."""
    pyautogui.click(x * S, y * S)
    time.sleep(esp)


def frente():
    """Traz o Domínio para a frente. Falha se a usuária estiver mexendo na máquina: repetir ou seguir sem."""
    d.foco(d.achar_sistema())
    time.sleep(0.8)


def ler(x, y, w, h):
    """OCR local (sem tokens) de uma região em coordenadas de print 960x540."""
    return d.ler_area((x * S, y * S, w * S, h * S))


# ---------------------------------------------------------------- Alteração de Lançamentos
def abrir_alt():
    """Utilitários -> Alteração de Lançamentos (ou Favoritos -> Alteração de lançamentos). Não reabre se já aberta."""
    frente()
    if "ltera" not in ler(380, 222, 440, 18):
        c(309, 33, 1.2)
        c(343, 157, 4)


def fechar_alt():
    """Fecha a janela (X). Necessário entre pesquisas: depois de uma busca o botão Busca avançada fica desabilitado."""
    frente()
    c(808, 230, 1.5)


def busca_lotes(lotes):
    """Busca avançada por Lote (5 dígitos) com Ou entre as linhas. Até 5 lotes por busca. Retorna o OCR da grade.
    Ordem que funciona: criar TODAS as linhas (Adicionar) e só depois preencher o Operador 'Ou' das linhas de cima.
    O OK da busca já pesquisa (não clicar em Buscar depois: limpa a lista)."""
    c(713, 457, 2.5)                                   # Busca avançada
    for i, lote in enumerate(lotes):
        y = 253 + 14 * i
        if i > 0:
            c(643, 234, 1.2)                           # Adicionar
        c(360, y, 1.0)                                 # lista de colunas (1ª opção, 'Down' 1x = Lote)
        pyautogui.press("down"); pyautogui.press("enter"); time.sleep(0.6)
        c(490, y, 0.6)
        pyautogui.write("%05d" % int(lote), interval=0.08); time.sleep(0.4)
    for i in range(len(lotes) - 1):
        y = 253 + 14 * i
        c(577, y, 0.8)                                 # Operador
        pyautogui.press("down"); pyautogui.press("down"); pyautogui.press("enter"); time.sleep(0.5)  # E, Ou
    c(643, 297, 6)                                     # OK = pesquisa
    return ler(408, 262, 390, 160)


def busca_conta(coluna, conta, data_min=None):
    """Busca por Debitar ou Creditar = conta, opcionalmente E Data >= data_min (ddmmaaaa). Sem a data traz todos os anos.
    Colunas na lista (Down a partir do vazio): Lote 1, SCP 2, Número 3, Data 4, Tipo 5, Debitar 6, Creditar 7, Valor 8."""
    downs = {"debitar": 6, "creditar": 7}[coluna.lower()]
    c(713, 457, 2.5)
    c(360, 253, 1.2)
    for _ in range(downs):
        pyautogui.press("down"); time.sleep(0.25)
    pyautogui.press("enter"); time.sleep(0.8)
    c(490, 253, 0.8)
    pyautogui.write(str(conta), interval=0.08); time.sleep(0.5)
    if data_min:
        c(643, 234, 1.2)                               # Adicionar (2ª linha)
        c(360, 267, 1.2)
        for _ in range(4):
            pyautogui.press("down"); time.sleep(0.25)  # Data
        pyautogui.press("enter"); time.sleep(0.8)
        c(395, 267, 1.2)                               # Condição: Igual a, Diferente de, Entre, Maior e igual a (3x Down)
        for _ in range(3):
            pyautogui.press("down"); time.sleep(0.25)
        pyautogui.press("enter"); time.sleep(0.8)
        c(440, 267, 0.8)                               # valor da data: clicar, Home, digitar
        pyautogui.press("home"); pyautogui.write(data_min, interval=0.1); time.sleep(0.6)
        c(577, 253, 1.0)                               # Operador da linha 1 = E
        pyautogui.press("down"); pyautogui.press("enter"); time.sleep(0.8)
    c(643, 297, 6)
    return ler(408, 262, 390, 160)


def aplicar(valor=None, debito=None, credito=None):
    """Todos -> Alterar... -> marca só os campos pedidos -> Alterar -> responde os diálogos.
    Diálogos: 'tem certeza?' = Yes; 'já está conciliado' = Yes (regra dela: sempre sim); 'sucesso' = OK.
    Retorna (nome da conta lida na tela, log dos diálogos). Alterar valor: parte maior; a outra parte vai por CSV."""
    c(421, 457, 1.2)                                   # Todos (marca as linhas da grade)
    c(647, 457, 3)                                     # Alterar...
    if valor is not None:
        c(313, 242, 0.8); c(417, 242, 0.5)
        pyautogui.write(valor, interval=0.08); pyautogui.press("tab"); time.sleep(0.8)
    if debito is not None:
        c(313, 257, 0.8); c(417, 257, 0.5)
        pyautogui.write(str(debito), interval=0.08); pyautogui.press("tab"); time.sleep(1.5)
    if credito is not None:
        c(313, 272, 0.8); c(417, 272, 0.5)
        pyautogui.write(str(credito), interval=0.08); pyautogui.press("tab"); time.sleep(1.5)
    nome = ler(440, 250, 220, 14)
    c(597, 389, 3)                                     # Alterar
    log = []
    for _ in range(80):                                # lote com N lançamentos pode repetir 'conciliado'
        t = ler(380, 224, 220, 90).lower()
        if "concili" in t:
            c(481, 302, 2.5); log.append("C")
        elif "certeza" in t:
            c(506, 302, 3); log.append("Q")
        elif "sucesso" in t:
            c(537, 302, 2); log.append("OK"); break
        else:
            time.sleep(2); log.append("?" + t[:25])
    c(645, 389, 1.5)                                   # Fechar o diálogo Alterar
    return nome, log


# ---------------------------------------------------------------- Exclusão de Lançamentos
def excluir(lote_ini=None, lote_fim=None, data_ini=None, data_fim=None, conta_credito=None, conta_debito=None):
    """Utilitários -> Exclusão -> Lançamentos (NÃO 'Lançamentos Simples'). Filtros por lote OU data + conta.
    NUNCA clicar em 'Reiniciar' (é 'Reincluir': 'Deseja re-incluir lançamentos excluídos?' -> No).
    Datas: clicar no segmento do dia, Home, digitar ddmmaaaa. Retorna o OCR do resultado ('Excluídos: N').
    Lançamento anterior à data de fechamento: 'Data inferior à data de fechamento' -> parar e pedir que ela mude a data."""
    frente()
    c(309, 33, 1.2); c(318, 389, 1.5); c(563, 405, 3)
    if lote_ini:
        c(461, 139, 0.8)
        c(527, 153, 0.6); pyautogui.write("%05d" % int(lote_ini), interval=0.08)
        c(527, 168, 0.6); pyautogui.write("%05d" % int(lote_fim or lote_ini), interval=0.08)
        pyautogui.press("tab"); time.sleep(0.8)
    if data_ini:
        c(323, 139, 0.8)
        c(365, 153, 0.6); pyautogui.press("home"); pyautogui.write(data_ini, interval=0.1)
        c(365, 168, 0.6); pyautogui.press("home"); pyautogui.write(data_fim, interval=0.1)
    if conta_debito:
        c(323, 305, 0.8); c(385, 318, 0.6)   # conta_debito NÃO testado ao vivo (só conta_credito foi)
        pyautogui.write(str(conta_debito), interval=0.08); pyautogui.press("tab"); time.sleep(1.2)
    if conta_credito:
        c(323, 342, 0.8); c(385, 356, 0.6); pyautogui.write(str(conta_credito), interval=0.08); pyautogui.press("tab"); time.sleep(1.2)
    # CONFIRA o filtro (um print da região 580,190,700,560 em coords de tela) antes do OK na primeira vez.
    c(633, 133, 3)                                     # OK
    if "exclus" not in ler(390, 224, 180, 90).lower():
        return "SEM confirmação: " + ler(380, 224, 220, 100)
    c(484, 302, 6)                                     # Yes
    res = ler(400, 224, 200, 100)
    c(517, 304, 1.5)                                   # OK do 'Excluídos: N'
    c(633, 153, 1.5)                                   # Fechar a tela de Exclusão
    return res


# ---------------------------------------------------------------- Importação csv
def importar_pendente(gravar=False):
    """Favoritos -> Importação csv. A janela lembra a pasta da última vez (02 Pendente de importar da empresa ativa):
    confira que a grade mostra SÓ o CSV esperado. Importar -> Resumo ('Lançamentos contábeis (N)'; N = linhas do CSV).
    gravar=False: para no Resumo (retorna o OCR; Esc/Cancelar depois). gravar=True: Gravar -> 'erros de estrutura' Yes
    (é só o cabeçalho) -> 'Dados gravados com sucesso'. Gravar UMA vez. Depois mover o CSV para 01 Importados.
    Se a pasta lembrada for outra, navegar no Procurar Pasta: duplo clique expande, digitar o início do nome seleciona
    (Users, atend, OneDrive, Documentos, ROTINAS, IMPORTA, <NNN>, Arquivos, 02), OK, aviso 'não existem arquivos TXT' = OK,
    tipo 'Todos os arquivos (*.*)'."""
    frente()
    c(360, 33, 1.5); c(376, 91, 6)                     # Favoritos -> Importação csv
    c(720, 143, 3.5)                                   # '...' do Caminho abre a Seleção de arquivos
    lista = ler(300, 205, 380, 40)
    c(593, 385, 3)                                     # OK da Seleção (se não fechar, repetir)
    c(662, 465, 20)                                    # Importar
    resumo = ler(25, 125, 500, 40)
    if not gravar:
        return {"lista": lista, "resumo": resumo}
    c(870, 494, 3)                                     # Gravar
    t = ler(380, 224, 220, 90)
    if "estrutura" in t.lower():
        c(503, 302, 8)                                 # Yes
    res = ler(370, 224, 230, 100)
    if "sucesso" in res.lower():
        c(560, 302, 2)                                 # OK
    c(923, 494, 2)                                     # fecha o Resumo
    c(717, 465, 2)                                     # Fechar a Importação
    return {"lista": lista, "resumo": resumo, "gravacao": res}


# ---------------------------------------------------------------- Exportação
def exportar_relatorios(pasta_cliente, ini="01042026", fim="30092026"):
    """Balancete.xlsx e Razão.xlsx na raiz da pasta do cliente (arquivar os antigos em 99 antes, com prefixo antes_).
    balancete.py/razao.py costumam acusar 'janela não abriu' (detector de título) mesmo com a janela aberta: ignorar,
    clicar OK da janela e seguir com exportar_excel.py. Plano de contas: só reexportar se mudou conta (Utilitários ->
    Exportação -> Contas; ver skill exportar-plano-de-contas)."""
    import subprocess
    py = sys.executable

    def rodar(*a, limite=300):
        return subprocess.run([py, *a], cwd=AQUI, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=limite)
    rodar("balancete.py", ini, fim, limite=120)
    c(733, 143, 12)                                    # OK da janela Balancete
    r1 = rodar("exportar_excel.py", pasta_cliente, "Balancete.xlsx")
    rodar("razao.py", ini, fim, limite=120)
    c(739, 139, 15)                                    # OK da janela Razão
    r2 = rodar("exportar_excel.py", pasta_cliente, "Razão.xlsx")
    return (r1.stdout.strip().splitlines() or [""])[-1], (r2.stdout.strip().splitlines() or [""])[-1]
