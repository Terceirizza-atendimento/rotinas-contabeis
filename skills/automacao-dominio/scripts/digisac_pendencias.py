"""Digisac: pendências de retorno (SOMENTE LEITURA, nunca envia nada).

Lista os chamados abertos do departamento Contabilidade e os da Letícia,
indicando quem falou por último e há quanto tempo. Token em DIGISAC_TOKEN
(variável de usuário; nunca imprimir). Saída: Markdown no stdout e arquivo em
automacao-domino/saida/digisac_pendencias_AAAA-MM-DD_HHMM.md
Uso: python digisac_pendencias.py [--horas-alerta 4]
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

BASE = "https://terceirizza.digisac.biz/api/v1"
DEPTO_CONTAB = "a74a4600-69f2-44b6-9643-405d585aae2d"
USER_LETICIA = "f7ac0916-3619-42f5-b561-f8e3b97fcee9"
TZ = timezone(timedelta(hours=-3))
TOKEN = os.environ.get("DIGISAC_TOKEN") or ""
if not TOKEN and os.name == "nt":
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        TOKEN = winreg.QueryValueEx(k, "DIGISAC_TOKEN")[0]
HEAD = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "terceirizza-rotinas-contabeis/1.0"}
ALERTA_H = float(sys.argv[sys.argv.index("--horas-alerta") + 1]) if "--horas-alerta" in sys.argv else 4


def get(path, query=None):
    url = f"{BASE}/{path}"
    if query is not None:
        url += "?query=" + urllib.parse.quote(json.dumps(query))
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def tickets(where):
    out, page = [], 1
    while True:
        r = get("tickets", {"where": where, "perPage": 100, "page": page, "order": [["updatedAt", "DESC"]]})
        out += r["data"]
        if len(out) >= r.get("total", 0) or not r["data"]:
            return out
        page += 1


def dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ)


def horas(d):
    return (datetime.now(TZ) - d).total_seconds() / 3600


def fmt_h(h):
    return f"{h*60:.0f} min" if h < 1 else (f"{h:.1f} h" if h < 48 else f"{h/24:.1f} dias")


cache_c = {}


def contato(cid):
    if cid not in cache_c:
        try:
            c = get(f"contacts/{cid}")
            cache_c[cid] = c.get("name") or c.get("alternativeName") or cid[:8]
        except Exception:
            cache_c[cid] = cid[:8]
    return cache_c[cid]


def linha(t):
    d = {"t": t}
    d["contato"] = contato(t["contactId"])
    m = None
    if t.get("lastMessageId"):
        try:
            m = get(f"messages/{t['lastMessageId']}")
        except Exception:
            pass
    d["msg"] = m
    d["de_mim"] = bool(m and m.get("isFromMe"))
    base = dt(m["timestamp"]) if m and m.get("timestamp") else dt(t["updatedAt"])
    d["quando"] = base
    d["h"] = horas(base)
    txt = ((m or {}).get("text") or "").replace("\n", " ").strip()
    if not txt and m:
        txt = f"[{m.get('type','mídia')}]"
    d["txt"] = txt[:160]
    d["sem_resp"] = t.get("userId") is None
    return d


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cont = {t["id"]: t for t in tickets({"isOpen": True, "departmentId": DEPTO_CONTAB})}
    minhas = {t["id"]: t for t in tickets({"isOpen": True, "userId": USER_LETICIA})}
    # só o que diz respeito à Letícia: chamados dela + fila da Contabilidade ainda sem atendente
    # (chamados de outros atendentes ficam de fora; --todos traz tudo)
    if "--todos" in sys.argv:
        todos = {**cont, **minhas}
    else:
        todos = {**{i: t for i, t in cont.items() if not t.get("userId")}, **minhas}
    linhas = sorted((linha(t) for t in todos.values()), key=lambda d: -d["h"])
    agora = datetime.now(TZ)
    L = [f"# Digisac: pendências ({agora:%d/%m/%Y %H:%M})", ""]
    ret = [d for d in linhas if not d["de_mim"]]
    aguard = [d for d in linhas if d["de_mim"]]

    def bloco(titulo, itens):
        L.append(f"## {titulo} ({len(itens)})")
        if not itens:
            L.append("- nada")
        for d in itens:
            t = d["t"]
            onde = "Contabilidade (fila)" if t["id"] in cont and not t.get("userId") else (
                "Minha" if t.get("userId") == USER_LETICIA else "Contabilidade (de outro atendente)")
            alerta = " ⚠" if d["h"] >= ALERTA_H else ""
            L.append(f"- **{d['contato']}** · {onde} · protocolo {t['protocol']} · última msg {d['quando']:%d/%m %H:%M} ({fmt_h(d['h'])}){alerta}")
            if d["txt"]:
                L.append(f"  > {d['txt']}")
        L.append("")

    bloco("Cliente falou por último: precisa de retorno", ret)
    bloco("Eu falei por último: aguardando o cliente", aguard)
    if "--json" in sys.argv:  # documentos prontos para a coleção `chamados` do painel
        docs = []
        for d in linhas:
            t = d["t"]
            onde = "minha" if t.get("userId") == USER_LETICIA else ("fila" if not t.get("userId") else "outro")
            quem = "eu" if d["de_mim"] else "cliente"
            acao = "responder" if quem == "cliente" else ("cobrar" if d["h"] >= 48 else "aguardar")
            docs.append({"id": t["protocol"], "contato": d["contato"], "protocolo": t["protocol"], "onde": onde,
                         "quem": quem, "quandoISO": d["quando"].astimezone(timezone.utc).isoformat(),
                         "txt": d["txt"], "acao": acao, "tratado": False})
        pj = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saida", "digisac_chamados.json")
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        with open(pj, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=1)
    texto = "\n".join(L)
    print(texto)
    pasta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saida")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, f"digisac_pendencias_{agora:%Y-%m-%d_%H%M}.md"), "w", encoding="utf-8") as f:
        f.write(texto)


if __name__ == "__main__":
    main()
