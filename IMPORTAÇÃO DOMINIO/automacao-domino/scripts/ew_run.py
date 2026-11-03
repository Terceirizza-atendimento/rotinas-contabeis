import json, sys, re
import ew_alt
from ew_alt import *
ORIG = {"364": "364", "5": "5"}
def fechar_msgs():
    for h, t in d.janelas_remotas():
        if t == "Alteração de Lançamentos":
            pass
def aplicar_seguro(conta, lotes):
    g = ew_alt.busca(lotes)
    def linhas(t):
        n = len(re.findall(r"\d{2}/\d{2}\D{0,2}\d{4}", t)); m = sum(str(l) in t.replace(".", "") for l in lotes)
        return len(lotes) if (m == len(lotes) or n == len(lotes)) else min(n, m)
    if linhas(g) != len(lotes):
        time.sleep(3); g = ler(408, 262, 390, 160)
    if linhas(g) != len(lotes):
        return f"ABORTADO: grade com {linhas(g)} linhas, esperado {len(lotes)} {lotes}: {g[:150]}"
    c(421, 457, 1.2); c(647, 457, 3)
    c(313, 326, 0.8); c(417, 326, 0.5); pyautogui.write(str(conta), interval=0.1); pyautogui.press("tab"); time.sleep(1.5)
    if any(tt == 'Erro' for h, tt in d.janelas_remotas()):
        return 'ERRO aberto antes de digitar: ' + ler(250, 200, 560, 200)[:200]
    time.sleep(2)
    if any(tt == 'Erro' for h, tt in d.janelas_remotas()):
        for h, tt in d.janelas_remotas():
            if tt == 'Erro': d.foco(h); pyautogui.press('enter'); time.sleep(1)
        c(645, 458, 1.5); return f"ABORTADO: conta {conta} recusada (Erro na tela)"
    nome = ""
    for _t in range(8):
        ps = ocr.palavras(pyautogui.screenshot())
        palavras = [t for t, x, y, w, h in ps if 310 < y / 2 < 335 and 400 < x / 2 < 700 and t.strip()]
        nome = " ".join(palavras)
        if str(conta) in palavras: break
        time.sleep(1.5)
    c(597, 458, 3)
    log = []
    for _ in range(150):
        t = ler(250, 200, 460, 200).lower()
        if any(tt == 'Erro' for h, tt in d.janelas_remotas()):
            return f'ERRO na tela: {t[:200]}'
        if "concili" in t or "certeza" in t:
            b = ew_alt._btn("yes")
            if b: pyautogui.click(*b); log.append("Y"); time.sleep(2.5); continue
        if "sucesso" in t:
            for h, tt in d.janelas_remotas():
                if tt == "Alteração de Lançamentos" and h != d.achar_titulo("Alteração de Lançamentos"):
                    pass
            # msgbox: enter na janela de mensagem
            wins = [h for h, tt in d.janelas_remotas() if tt == "Alteração de Lançamentos"]
            d.foco(wins[0]); pyautogui.press("enter"); time.sleep(2); log.append("OK"); break
        time.sleep(1.2)
    c(645, 458, 1.5)
    return f"{conta} {lotes}: {nome.strip()[:40]} | {''.join(log)}"
if __name__ == "__main__":
    plano = json.load(open(r"..\saida\ew_plano_alteracoes.json"))
    only = sys.argv[1:] 
    for conta, itens in plano.items():
        if conta == "PED" or (only and conta not in only): continue
        lotes = [i[1] for i in itens]
        for k in range(0, len(lotes), 5):
            lt = lotes[k:k+5]
            frente()
            if 'ltera' in ler(380,222,440,18): fechar_alt()
            ew_alt.abrir_alt2()
            r = aplicar_seguro(conta, lt)
            print(r, flush=True)
            fechar_alt()
            if r.startswith("ABORTADO"): sys.exit(1)
