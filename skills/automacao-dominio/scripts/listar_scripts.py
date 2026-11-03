"""Lista os scripts da automação do Domínio com o 'Uso:' de cada um (lê o docstring; não executa nada).
Uso: python listar_scripts.py [--completo]
  sem argumentos: nome + primeiras linhas do docstring (inclui a linha 'Uso:')
  --completo:     docstring inteiro de cada script
A skill iniciar-fechamento roda isto no começo para ler os scripts atuais (eles mudam entre sessões).
"""
import ast
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
completo = "--completo" in sys.argv

for caminho in sorted(glob.glob(os.path.join(AQUI, "*.py"))):
    nome = os.path.basename(caminho)
    if nome == os.path.basename(__file__):
        continue
    try:
        with open(caminho, encoding="utf-8") as f:
            doc = ast.get_docstring(ast.parse(f.read())) or "(sem docstring)"
    except Exception as e:  # arquivo com erro de sintaxe: avisa e segue
        doc = f"(erro ao ler: {e})"
    linhas = doc.splitlines()
    if not completo:
        linhas = linhas[:6]
    print(f"== {nome}")
    for ln in linhas:
        print("   " + ln)
print(f"\n{len(glob.glob(os.path.join(AQUI, '*.py'))) - 1} scripts em {AQUI}")
