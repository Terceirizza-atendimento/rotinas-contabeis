"""Troca a empresa ativa do Domínio e confere pela barra. Uso: python trocar_empresa.py <codigo>
Se a barra já mostra o código, não faz nada. Senão: F8 -> "Troca de empresas" -> acha por OCR o campo
Código e o botão Acessar -> digita o código -> Acessar -> confere. NÃO TESTADO ao vivo (posições via OCR)."""
import sys
import time

import pyautogui

import ocr
from dominio_lib import achar_sistema, digitar, empresa_ativa, exigir_empresa, foco, limpar_campo, log, tecla, clicar

codigo = sys.argv[1]


def achar(palavra):
    for t, x, y, w, h in ocr.palavras(pyautogui.screenshot()):
        if t.lower().strip(":") == palavra.lower():
            return int(x + w / 2), int(y + h / 2), int(w)
    return None


h = achar_sistema() or sys.exit("Sistema da Domínio não está aberto")
foco(h, maximizar=True)
try:
    exigir_empresa(codigo)
    sys.exit(0)
except SystemExit as e:
    if "EMPRESA ERRADA" not in str(e):
        raise
tecla(h, "f8")
time.sleep(2)
cod, ace = achar("Código"), achar("Acessar")
if not cod or not ace:
    sys.exit("Diálogo 'Troca de empresas' não encontrado por OCR (F8 não abriu?)")
clicar(h, cod[0] + cod[2] + 40, cod[1]); limpar_campo(h, 10); digitar(h, codigo, 0.03)
time.sleep(1)
clicar(h, ace[0], ace[1])
time.sleep(4)
exigir_empresa(codigo)
