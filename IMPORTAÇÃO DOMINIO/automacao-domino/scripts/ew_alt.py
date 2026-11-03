"""Auxiliar da 001: Alteração de Lançamentos com Busca avançada na posição atual (dialog 69 px abaixo do gravado em 30/10)."""
from dominio_ops import *
DY = 69
def busca(lotes):
    c(713, 457, 2.5)
    for i, lote in enumerate(lotes):
        y = 253 + DY + 14 * i
        if i > 0:
            c(643, 234 + DY, 1.2)
        c(360, y, 1.0)
        pyautogui.press("down"); pyautogui.press("enter"); time.sleep(0.6)
        c(490, y, 0.6)
        pyautogui.write("%05d" % int(lote), interval=0.08); time.sleep(0.4)
    for i in range(len(lotes) - 1):
        y = 253 + DY + 14 * i
        c(577, y, 0.8)
        pyautogui.press("down"); pyautogui.press("down"); pyautogui.press("enter"); time.sleep(0.5)
    c(643, 297 + DY, 6)
    return ler(408, 262, 390, 160)

import ocr
def _btn(txt):
    ps = ocr.palavras(pyautogui.screenshot())
    return next(((int(x+w/2), int(y+h/2)) for t,x,y,w,h in ps if t.strip().lower()==txt), None)

def aplicar2(debito=None, credito=None, valor=None):
    """Todos -> Alterar... -> campos (posição atual, +69) -> Alterar -> Yes/Yes/OK por OCR -> Fechar."""
    c(421, 457, 1.2); c(647, 457, 3)
    if valor is not None:
        c(313, 242+DY, 0.8); c(417, 242+DY, 0.5); pyautogui.write(valor, interval=0.08); pyautogui.press("tab"); time.sleep(0.8)
    if debito is not None:
        c(313, 257+DY, 0.8); c(417, 257+DY, 0.5); pyautogui.write(str(debito), interval=0.08); pyautogui.press("tab"); time.sleep(1.5)
    if credito is not None:
        c(313, 272+DY, 0.8); c(417, 272+DY, 0.5); pyautogui.write(str(credito), interval=0.08); pyautogui.press("tab"); time.sleep(1.5)
    nome = ler(440, 250+DY, 220, 14)
    c(597, 389+DY, 3)
    log = []
    for _ in range(120):
        t = ler(250, 200, 460, 160).lower()
        if "concili" in t and (b := _btn("yes")):
            pyautogui.click(*b); log.append("C"); time.sleep(2.5)
        elif "certeza" in t and (b := _btn("yes")):
            pyautogui.click(*b); log.append("Q"); time.sleep(3)
        elif "sucesso" in t and (b := _btn("ok")):
            pyautogui.click(*b); log.append("OK"); time.sleep(2); break
        else:
            time.sleep(1.5); log.append("?")
    c(645, 389+DY, 1.5)       # Fechar o diálogo Alterar
    return nome, log

def abrir_alt2():
    """Utilitários -> 'Alteração de Lançamentos', clicando pelo TEXTO lido no OCR (o menu muda de posição)."""
    frente()
    if "Data do Cadastro" in ler(0,0,960,40):
        pyautogui.hotkey("ctrl","f4"); time.sleep(2)
    if "Lançamentos" in ler(380,222,440,18) and "ltera" in ler(380,222,440,18): return
    c(309, 33, 1.5)
    ps = ocr.palavras(pyautogui.screenshot())
    linhas = {}
    for t, x, y, w, h in ps:
        linhas.setdefault(round(y/2/6), []).append((t.strip(), x/2, y/2))
    alvo = None
    for k, ws in linhas.items():
        txt = " ".join(t for t, _, _ in sorted(ws, key=lambda a: a[1]))
        if "Alteração de Lançamentos" in txt and "Data" not in txt:
            alvo = (min(x for _, x, _ in ws) + 30, ws[0][2])
    if not alvo:
        pyautogui.press("esc"); raise SystemExit("menu: item 'Alteração de Lançamentos' não encontrado")
    pyautogui.click(alvo[0]*2, alvo[1]*2); time.sleep(4)

def digitar_lotes(lotes):
    """Na tela inicial da Alteração, a coluna Lote aceita digitar um lote por linha (Enter desce)."""
    c(446, 282, 1.0)
    for l in lotes:
        pyautogui.write("%05d" % int(l), interval=0.05); pyautogui.press("enter"); time.sleep(0.25)

def aplicar_grade(conta):
    """Buscar -> Todos -> Alterar... -> conta débito -> Alterar -> Yes/Yes/OK (grade já com os lotes digitados)."""
    c(771, 454, 8)                       # Buscar: carrega os lançamentos dos lotes digitados
    c(421, 457, 1.2); c(647, 457, 3)     # Todos; Alterar...
    c(313, 326, 1.0); c(417, 326, 1.0); pyautogui.write(str(conta), interval=0.2); pyautogui.press("tab"); time.sleep(3)
    if any(t == "Erro" for h, t in d.janelas_remotas()):
        return "ERRO: conta recusada"
    c(597, 458, 3)
    log = []
    for _ in range(300):
        t = ler(250, 200, 460, 200).lower()
        if "concili" in t or "certeza" in t:
            b = _btn("yes")
            if b: pyautogui.click(*b); log.append("Y"); time.sleep(2.5); continue
        if "sucesso" in t:
            wins = [h for h, tt in d.janelas_remotas() if tt == "Alteração de Lançamentos"]
            d.foco(wins[0]); pyautogui.press("enter"); time.sleep(2); log.append("OK"); break
        time.sleep(1.2)
    c(645, 458, 1.5)
    return "".join(log)
