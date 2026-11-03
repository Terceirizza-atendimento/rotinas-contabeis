import json, sys
import ew_alt, ew_run
from ew_alt import *
lotes = json.load(open(r"..\saida\ew_lotes_362_resto.json"))
for k in range(0, len(lotes), 5):
    lt = lotes[k:k+5]
    frente()
    if "Lançamentos" in ler(380,222,440,18) and "ltera" in ler(380,222,440,18): c(808,230,1.5)
    ew_alt.abrir_alt2()
    r = ew_run.aplicar_seguro(362, lt)
    print(f"[{k//5+1}/{(len(lotes)+4)//5}] {r}", flush=True)
    c(808,230,1.5)
    if r.startswith("ABORTADO") or "ERRO" in r:
        sys.exit(1)
print("FIM", flush=True)
