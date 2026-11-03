import json, sys
import ew_alt
from ew_alt import *
lotes = json.load(open(r"..\saida\ew_lotes_362_resto.json"))
G = 18
for k in range(0, len(lotes), G):
    lt = lotes[k:k+G]
    frente()
    if "Lançamentos" in ler(380,222,440,18) and "ltera" in ler(380,222,440,18): c(808,230,1.5)
    ew_alt.abrir_alt2()
    ew_alt.digitar_lotes(lt)
    r = ew_alt.aplicar_grade(362)
    print(f"[{k//G+1}/{(len(lotes)+G-1)//G}] {len(lt)} lotes: {r}", flush=True)
    c(808,230,1.5)
    if "ERRO" in r or "OK" not in r: sys.exit(1)
print("FIM", flush=True)
