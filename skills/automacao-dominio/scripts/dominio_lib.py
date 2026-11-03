"""Funções comuns para controlar a Domínio (janelas remotas do AppController).

Regras aprendidas:
- SetProcessDPIAware antes de qualquer coordenada (tela 1920x1080).
- A janela do sistema não tem título: achar por classe DisplayClientWindowClass + PID do AppController.
- Maximizar com SW_MAXIMIZE (3), nunca restaurar (9): desloca as coordenadas.
- Antes de clicar ou digitar, garantir que a janela da Domínio está em primeiro plano.
"""
import ctypes
import os
import time


def _carregar_env():
    """DW_* ficam nas variaveis de ambiente do USUARIO (Windows); processos filhos de bash/IDE nem sempre as herdam."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            for n in ("DW_USER", "DW_PASS", "DW_SYS_USER", "DW_SYS_PASS"):
                if not os.environ.get(n):
                    try:
                        os.environ[n] = winreg.QueryValueEx(k, n)[0]
                    except OSError:
                        pass
    except Exception:
        pass


_carregar_env()

# Desktop separado (DOMINIO_DESKTOP=nome): a Domínio roda num desktop do Windows que não é o do usuário. Lá a
# janela aceita cliques/teclas por mensagem sem estar em primeiro plano, então o usuário não é afetado em nada
# (nem mouse, nem teclado, nem foco). Este processo passa a enxergar só as janelas desse desktop.
# Precisa vir ANTES dos outros imports (SetThreadDesktop falha se a thread já criou janelas).
DESK = os.environ.get("DOMINIO_DESKTOP", "")
if DESK:
    import win32con as _wc
    import win32service
    win32service.OpenDesktop(DESK, 0, False, _wc.GENERIC_ALL).SetThreadDesktop()

import win32api
import win32con
import win32ui
from PIL import Image

import psutil
import pyautogui
import win32gui
import win32process

ctypes.windll.user32.SetProcessDPIAware()
pyautogui.PAUSE = 0.05
RAIZ = os.path.join(os.path.dirname(__file__), "..")
SAIDA = os.path.abspath(os.path.join(RAIZ, "saida"))
T0 = time.time()

# Modo sem mouse (DOMINIO_BG=1, experimental; o padrão é o modo clássico, validado): clique, tecla, digitação e captura são enviados à janela da Domínio por mensagens do
# Windows (PostMessage/PrintWindow): NÃO move o cursor do usuário. Limite: a janela precisa estar ativa (primeiro
# plano) para aceitar a entrada, então o teclado do usuário é interrompido enquanto o script age.
# Sem DOMINIO_BG usa mouse/teclado reais (modo clássico).
BG = os.environ.get("DOMINIO_BG", "0") == "1" or bool(DESK)
_real = False               # força o modo antigo dentro de uma chamada (fallback)
_alvo = None                 # última janela usada: a captura em segundo plano precisa saber qual é
_VK = {"enter": 0x0D, "esc": 0x1B, "backspace": 0x08, "end": 0x23, "home": 0x24, "tab": 0x09, "down": 0x28,
       "up": 0x26, "left": 0x25, "right": 0x27, "delete": 0x2E, "f8": 0x77, "space": 0x20}


def log(msg):
    print(f"[{time.time() - T0:5.1f}s] {msg}", flush=True)


def capturar(nome="ultima_tela.png", regiao=None, reduzir=None):
    os.makedirs(SAIDA, exist_ok=True)
    caminho = os.path.join(SAIDA, nome)
    img = _shot_bg(_alvo, regiao) if BG and _alvo and win32gui.IsWindow(_alvo) else pyautogui.screenshot(region=regiao)
    if reduzir:
        img = img.resize(reduzir)
    img.save(caminho)
    log(f"captura: {caminho}")
    return caminho


def _shot_bg(h, regiao=None):
    """Imagem da janela h sem usar a tela (PrintWindow). O conteúdo sai em escala 1/DPI no canto do bitmap:
    reescala para coordenadas de tela e recorta a região pedida (também em coordenadas de tela)."""
    l, t, r, b = win32gui.GetWindowRect(h)
    w, hh = r - l, b - t
    hdc = win32gui.GetWindowDC(h)
    dc = win32ui.CreateDCFromHandle(hdc)
    mdc = dc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dc, w, hh)
    mdc.SelectObject(bmp)
    ctypes.windll.user32.PrintWindow(h, mdc.GetSafeHdc(), 2)
    img = Image.frombuffer("RGB", (w, hh), bmp.GetBitmapBits(True), "raw", "BGRX", 0, 1)
    win32gui.DeleteObject(bmp.GetHandle()); mdc.DeleteDC(); dc.DeleteDC(); win32gui.ReleaseDC(h, hdc)
    esc = ctypes.windll.user32.GetDpiForSystem() / 96
    img = img.crop((0, 0, round(w / esc), round(hh / esc))).resize((w, hh))
    if regiao:
        x, y, rw, rh = regiao
        img = img.crop((x - l, y - t, x - l + rw, y - t + rh))
    return img


def _pids_appcontroller():
    return {p.pid for p in psutil.process_iter(["name"]) if p.info["name"] == "AppController.exe"}


def janelas_remotas():
    """Janelas DisplayClientWindowClass visíveis do AppController: [(hwnd, titulo)]."""
    pids = _pids_appcontroller()
    achadas = []

    def cb(h, _):
        if (win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "DisplayClientWindowClass"
                and win32process.GetWindowThreadProcessId(h)[1] in pids):
            achadas.append((h, win32gui.GetWindowText(h)))
    win32gui.EnumWindows(cb, None)
    return achadas


def achar_titulo(prefixo):
    """Acha uma janela remota cujo título contenha `prefixo`. Era `startswith`, mas um relatório aberto (Balancete,
    Razão) não cria janela própria: ele só muda o título da janela PRINCIPAL para "Domínio ... - [Balancete]",
    que não começa com "Balancete" (achado na 013, 30/10/2026: `abrir_favorito(..., titulo="Balancete")` nunca
    encontrava nada mesmo com o relatório já aberto na tela). Substring resolve os dois casos sem quebrar os
    títulos exatos/prefixo (Lista de Programas, Conectando, Selecione o arquivo, Procurar Pasta)."""
    for h, t in janelas_remotas():
        if prefixo.lower() in t.lower():
            return h
    return None


def achar_sistema():
    """Janela principal da Contabilidade: remota e a maior. Normalmente sem título; com um relatório aberto
    (Balancete, Razão) ela GANHA título ("... - [Balancete]") em vez de abrir uma janela separada — nesse caso
    não há janela sem título para achar (achado na 013, 30/10/2026, que quebrava funções chamadas logo depois de
    abrir um relatório). Por isso: primeiro tenta a sem título (caso comum); se não achar, cai para a maior
    DisplayClientWindowClass do AppController, tenha título ou não."""
    todas = janelas_remotas()
    if not todas:
        return None
    sem_titulo = [h for h, t in todas if not t]
    candidatas = sem_titulo or [h for h, _ in todas]
    return max(candidatas, key=lambda h: (lambda r: (r[2] - r[0]) * (r[3] - r[1]))(win32gui.GetWindowRect(h)))


def esperar(buscar, limite=90, passo=0.2):
    fim = time.time() + limite
    while time.time() < fim:
        r = buscar()
        if r:
            return r
        time.sleep(passo)
    return None


def foco(h, maximizar=False, tentativas=5):
    """Traz h para a frente e confirma. Levanta erro se não conseguir (não digitar em outra janela).
    A janela remota só aceita teclas/cliques enquanto está ativa (testado: inativa ignora tudo, mesmo por
    mensagem), então o foco é sempre garantido; em BG não mexe no cursor."""
    global _alvo
    _alvo = h
    if DESK:
        if not win32gui.IsWindow(h):
            raise RuntimeError("janela da Domínio não existe mais")
        for m, w in ((win32con.WM_ACTIVATEAPP, 1), (win32con.WM_ACTIVATE, 1), (win32con.WM_SETFOCUS, 0)):
            win32gui.SendMessage(h, m, w, 0)
        if maximizar and win32gui.GetWindowPlacement(h)[1] != 3:
            win32gui.ShowWindow(h, 3)
        return
    for _ in range(tentativas):
        if not win32gui.IsWindow(h):
            raise RuntimeError("janela da Domínio não existe mais")
        if win32gui.GetForegroundWindow() != h:
            if not BG and pyautogui.position().y > 1000:   # mouse na barra de tarefas atrapalha o foco
                pyautogui.moveTo(960, 500)
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)      # Alt libera SetForegroundWindow
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
        if maximizar:
            win32gui.ShowWindow(h, 3)
        elif win32gui.IsIconic(h):
            win32gui.ShowWindow(h, 9)
        try:
            win32gui.SetForegroundWindow(h)
        except win32gui.error:
            pass
        time.sleep(0.4)
        if win32gui.GetForegroundWindow() == h:
            return
    capturar("erro_foco.png", reduzir=(960, 540))
    raise RuntimeError("não consegui colocar a janela da Domínio em primeiro plano")


def _lp(h, x, y):
    cx, cy = win32gui.ScreenToClient(h, (x, y))
    return win32api.MAKELONG(cx & 0xFFFF, cy & 0xFFFF)


def _vk_bg(h, vk):
    scan = win32api.MapVirtualKey(vk, 0)
    win32gui.PostMessage(h, win32con.WM_KEYDOWN, vk, 1 | (scan << 16))
    time.sleep(0.02)
    win32gui.PostMessage(h, win32con.WM_KEYUP, vk, 1 | (scan << 16) | (1 << 30) | (1 << 31))


def _digitavel(ch):
    v = win32api.VkKeyScan(ch)
    return ord(ch) < 128 and v != -1 and (v >> 8) in (0, 1)


def _tecla_char(h, ch):
    """Digita um caractere ASCII por eventos de tecla (o campo remoto ignora WM_CHAR). Maiúscula/símbolo: Shift."""
    v = win32api.VkKeyScan(ch)
    if v >> 8 & 1:
        win32gui.PostMessage(h, win32con.WM_KEYDOWN, win32con.VK_SHIFT, 1 | (win32api.MapVirtualKey(0x10, 0) << 16))
    _vk_bg(h, v & 0xFF)
    if v >> 8 & 1:
        win32gui.PostMessage(h, win32con.WM_KEYUP, win32con.VK_SHIFT, 1 | (win32api.MapVirtualKey(0x10, 0) << 16) | (3 << 30))


def foco_real(h):
    global _real
    _real = True
    try:
        foco(h)
    finally:
        _real = False


def clicar(h, x, y):
    foco(h)
    if BG:
        lp = _lp(h, x, y)
        win32gui.PostMessage(h, win32con.WM_MOUSEMOVE, 0, lp)
        time.sleep(0.05)
        win32gui.PostMessage(h, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
        time.sleep(0.05)
        win32gui.PostMessage(h, win32con.WM_LBUTTONUP, 0, lp)
        time.sleep(0.1)
        return
    pyautogui.click(x, y)


def digitar(h, texto, intervalo=0.02):
    foco(h)
    if BG and all(_digitavel(ch) for ch in texto):
        for ch in texto:
            _tecla_char(h, ch)
            time.sleep(max(intervalo, 0.05))
        time.sleep(0.3)                                # a entrada remota é assíncrona: sem isso o clique seguinte atropela o último caractere
        return
    if BG:
        log("texto com caracteres que o modo segundo plano não digita: usando teclado real")
        foco_real(h)
    pyautogui.write(texto, interval=intervalo)


class _KI(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class _MI(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", _KI), ("mi", _MI)]


class _IN(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _U)]


def _unicode(ch):
    for fl in (4, 4 | 2):       # KEYEVENTF_UNICODE (down, up)
        i = _IN(1, _U(ki=_KI(0, ord(ch), fl, 0, 0)))
        ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(i))


def digitar_texto(h, texto, intervalo=0.03):
    """Digita com acentos na sessão remota. A área de transferência não é compartilhada
    e SendInput-unicode troca maiúsculas ASCII por minúsculas: ASCII por pyautogui, acentos por SendInput."""
    foco(h)
    if BG:
        return digitar(h, texto, intervalo)
    for ch in texto:
        if ord(ch) < 128:
            pyautogui.write(ch, interval=0)
        else:
            _unicode(ch)
        time.sleep(intervalo)


def limpar_campo(h, maximo=250):
    """Esvazia o campo com foco (Ctrl+A não seleciona nos campos do Domínio)."""
    foco(h)
    if BG:
        _vk_bg(h, _VK["end"])
        for _ in range(maximo):
            _vk_bg(h, _VK["backspace"])
            time.sleep(0.03)                           # mais rápido que isso a entrada remota perde teclas
        return
    pyautogui.press("end")
    pyautogui.press("backspace", presses=maximo, interval=0.005)


def tecla(h, *teclas):
    foco(h)
    if BG:
        if len(teclas) > 1:
            raise RuntimeError("combinações de teclas não funcionam em segundo plano")
        return _vk_bg(h, _VK[teclas[0]])
    pyautogui.hotkey(*teclas) if len(teclas) > 1 else pyautogui.press(teclas[0])


# ---- Leitura por OCR local (sem tokens): ler antes de preencher, conferir empresa ----
def ler_area(regiao, escala=3):
    """Texto (OCR do Windows) de uma região (x, y, w, h) em coordenadas de tela. Não gasta tokens."""
    import ocr
    img = _shot_bg(_alvo, regiao) if BG and _alvo and win32gui.IsWindow(_alvo) else pyautogui.screenshot(region=regiao)
    return ocr.ler(img, escala)


def ler_data(y, x=540, w=200):
    """Data (dd/mm/aaaa) do campo na linha y da janela Balancete/Razão, ou '' se não leu."""
    d = "".join(c for c in ler_area((x, y - 13, w, 26)) if c.isdigit())
    if len(d) == 10:                      # o OCR às vezes lê as barras como "1": 01/01/2026 -> 0110112026
        d = d[0:2] + d[3:5] + d[6:10]
    return d if len(d) == 8 else ""


def preencher_data(h, x, y, valor):
    """Só digita se o campo já não tiver a data. valor = ddmmaaaa. Retorna True se digitou."""
    if ler_data(y) == valor:
        log(f"data {valor} já preenchida: não redigito")
        return False
    clicar(h, x, y); limpar_campo(h, 12); digitar(h, valor, 0.03)
    if ler_data(y) != valor:
        raise SystemExit(f"data do campo y={y} não ficou {valor} (leu '{ler_data(y)}')")
    return True


def empresa_ativa():
    """Texto da barra de empresa (canto superior direito), ex.: 'LETICIA UNICA MARKETING - 75'."""
    return " ".join(ler_area((1650, 50, 260, 80), 3).split())


def exigir_empresa(codigo):
    """Aborta se a empresa ativa não tiver o código esperado (ex.: 43 -> procura '- 43' / '-43')."""
    import re
    txt = empresa_ativa()
    if not re.search(rf"-\s*0*{int(codigo)}\b", txt):
        raise SystemExit(f"EMPRESA ERRADA: esperava código {codigo}, a barra mostra: '{txt}'")
    log(f"empresa conferida: {txt}")


# ---- Padrão sem posição fixa: esperar o TEXTO aparecer e agir relativo a ele ----
def achar_texto(pred, limite=20):
    """Espera (até `limite` s) uma palavra lida por OCR que satisfaça pred(texto); devolve (x, y, w, h) ou None."""
    import ocr
    fim = time.time() + limite
    while True:
        for t, x, y, w, hh in ocr.palavras(pyautogui.screenshot()):
            if pred(t):
                return int(x), int(y), int(w), int(hh)
        if time.time() > fim:
            return None
        time.sleep(0.8)


def clicar_texto(h, pred, limite=20, descricao=""):
    p = achar_texto(pred, limite)
    if not p:
        capturar("erro_texto.png", reduzir=(960, 540))
        raise SystemExit(f"não achei na tela: {descricao or pred}")
    clicar(h, p[0] + p[2] // 2, p[1] + p[3] // 2)
    return p


def _data_em(regiao):
    d = "".join(c for c in ler_area(regiao) if c.isdigit())
    if len(d) == 10:
        d = d[0:2] + d[3:5] + d[6:10]
    return d if len(d) == 8 else ""


def data_por_rotulo(h, rotulo, valor, limite=20):
    """Campo de data na mesma linha do rótulo (ex.: 'Inicial', 'Final'), achado por OCR: lê a data que está lá e só
    digita se for diferente; relê e tenta de novo uma vez. valor = ddmmaaaa."""
    import ocr
    eh_rot = lambda t: t.rstrip(":").lower().endswith(rotulo.lower()[1:]) and len(t.rstrip(":")) <= len(rotulo) + 1

    def linha():
        ps = ocr.palavras(pyautogui.screenshot())
        rot = next((p for p in ps if eh_rot(p[0])), None)
        if not rot:
            return None, None
        _, x, y, w, hh = rot
        data = next((p for p in ps if abs((p[2] + p[4] / 2) - (y + hh / 2)) < 10 and x + w < p[1] < x + w + 350
                     and sum(c.isdigit() for c in p[0]) >= 6), None)
        return rot, data

    fim = time.time() + limite
    rot, data = linha()
    while not rot and time.time() < fim:
        time.sleep(0.8); rot, data = linha()
    if not rot:
        capturar("erro_texto.png", reduzir=(960, 540)); raise SystemExit(f"rótulo '{rotulo}' não apareceu")
    norm = lambda s: (lambda d: d[0:2] + d[3:5] + d[6:10] if len(d) == 10 else d)("".join(c for c in s if c.isdigit()))
    if data and norm(data[0]) == valor:
        log(f"{rotulo}: {valor} já preenchida"); return False
    for _ in range(2):
        _, x, y, w, hh = rot
        cx = int(data[1] + data[3] / 2) if data else int(x + w + 180)
        clicar(h, cx, int(y + hh / 2)); time.sleep(0.4)
        limpar_campo(h, 12); digitar(h, valor, 0.05); time.sleep(1)
        rot, data = linha()
        if rot and data and norm(data[0]) == valor:
            log(f"{rotulo}: {valor} digitada"); return True
    raise SystemExit(f"{rotulo}: não ficou {valor} (leu '{data[0] if data else ''}')")



def abrir_favorito(h, item, titulo=None, limite=30):
    """Favoritos -> item, esperando o menu aparecer (OCR do texto do item) e, se `titulo`, a janela com esse título."""
    import ocr
    foco(h, maximizar=True); time.sleep(0.3)
    alvo = None
    for tentativa in range(3):                           # o 1º clique às vezes só ativa a janela
        foco(h); pyautogui.moveTo(720, 64); time.sleep(0.2)                # menu Favoritos: clique "firme" (o rápido não abre)
        pyautogui.mouseDown(); time.sleep(0.15); pyautogui.mouseUp()
        fim = time.time() + 5
        while time.time() < fim and not alvo:
            time.sleep(0.6)
            for tx, x, y, w, hh in ocr.palavras(pyautogui.screenshot(region=(650, 75, 500, 260)), escala=3):   # escala 3: lê palavras curtas soltas
                if tx.lower().startswith(item.lower()):
                    alvo = (650 + int(x + w / 2), 75 + int(y + hh / 2)); break
        if alvo:
            break
    if not alvo:
        capturar("erro_menu.png", reduzir=(960, 540)); raise SystemExit(f"item '{item}' não apareceu no menu Favoritos")
    pyautogui.moveTo(*alvo); time.sleep(0.2); pyautogui.mouseDown(); time.sleep(0.15); pyautogui.mouseUp()
    if titulo:
        # Achado ao vivo em 03/11/2026: o diálogo de parâmetros do Balancete/Razão não é uma janela própria
        # nem muda o título da janela principal (EnumWindows não acha nada com esse título) — é desenhado
        # dentro do canvas remoto. achar_titulo (janela) e OCR (texto na tela) são tentados em paralelo:
        # achar_titulo cobre o caso de outros relatórios que criem janela de verdade; OCR cobre este caso.
        fim = time.time() + limite
        while time.time() < fim:
            j = achar_titulo(titulo)
            if j:
                time.sleep(1.5); return j
            if achar_texto(lambda s: s.lower() == titulo.lower(), limite=0):
                time.sleep(1.5); return h
            time.sleep(0.5)
        capturar("erro_menu.png", reduzir=(960, 540)); raise SystemExit(f"janela '{titulo}' não abriu")
    return None
