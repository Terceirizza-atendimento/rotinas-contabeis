"""Cliente mínimo da API do Digisac (terceirizza.digisac.biz).

Token vem da variável de ambiente DIGISAC_TOKEN (ver configurar_token_digisac.ps1).
Imprime só resumos curtos para economizar tokens.
Uso:  python -I digisac.py buscar "nome do cliente"
"""
import base64, json, mimetypes, os, sys, urllib.parse, urllib.request, urllib.error

BASE = "https://terceirizza.digisac.biz/api/v1"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"  # sem UA a Cloudflare bloqueia (erro 1010)


def _token():
    t = os.environ.get("DIGISAC_TOKEN")
    if not t:
        sys.exit("DIGISAC_TOKEN não definido. Rode configurar_token_digisac.ps1 e abra um novo terminal.")
    return t


def _req(method, path, body=None, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + _token(), "Accept": "application/json",
        "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:200]}") from None


def buscar_contato(nome, limite=5):
    """Procura contatos/grupos pelo nome. Retorna lista de {id, nome, serviceId}."""
    r = _req("GET", "/contacts", params={"query": json.dumps({"where": {"name": {"$iLike": f"%{nome}%"}}}), "perPage": limite})
    return [{"id": c["id"], "nome": c.get("name"), "serviceId": c.get("serviceId")} for c in r.get("data", [])]


def enviar_texto(contact_id, texto):
    return _req("POST", "/messages", {"contactId": contact_id, "text": texto, "type": "chat"})


def enviar_pdf(contact_id, caminho, legenda=""):
    mime = mimetypes.guess_type(caminho)[0] or "application/pdf"
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return _req("POST", "/messages", {"contactId": contact_id, "text": legenda, "type": "chat",
                                      "file": {"base64": b64, "mimetype": mime, "name": os.path.basename(caminho)}})


def fechar_chamado(contact_id):
    return _req("POST", f"/contacts/{contact_id}/ticket/close", {})


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "buscar":
        for c in buscar_contato(" ".join(sys.argv[2:])):
            print(c["id"], "|", c["nome"])
    else:
        print(__doc__)
