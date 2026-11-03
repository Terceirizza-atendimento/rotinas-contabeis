"""Cliente mínimo da API do Gclick (api.gclick.com.br).

Credenciais vêm de GCLICK_CLIENT_ID / GCLICK_CLIENT_SECRET (ver configurar_gclick.ps1).
O token OAuth dura ~1h e é renovado automaticamente.
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

BASE = "https://api.gclick.com.br"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"
_cache = {"token": None, "exp": 0}


def _token():
    if _cache["token"] and time.time() < _cache["exp"] - 60:
        return _cache["token"]
    cid, sec = os.environ.get("GCLICK_CLIENT_ID"), os.environ.get("GCLICK_CLIENT_SECRET")
    if not cid or not sec:
        sys.exit("GCLICK_CLIENT_ID/SECRET não definidos. Rode configurar_gclick.ps1 e abra um novo terminal.")
    data = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}).encode()
    req = urllib.request.Request(BASE + "/oauth/token", data=data, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    _cache.update(token=d["access_token"], exp=time.time() + d.get("expires_in", 3600))
    return _cache["token"]


def req(method, path, body=None, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + _token(), "Accept": "application/json",
        "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:200]}") from None


def tarefas(categoria="Obrigacao", inicio=None, fim=None, size=100, **filtros):
    """Lista tarefas. /tarefas exige 'categoria' (senão dá erro 500)."""
    p = {"categoria": categoria, "size": size, **filtros}
    if inicio: p["dataInicio"] = inicio
    if fim: p["dataFim"] = fim
    return req("GET", "/tarefas", params=p).get("content", [])


def tarefas_por_nome(trecho, inicio, fim, status="A", categoria="Obrigacao"):
    """Todas as tarefas cujo nome contém `trecho` (sem acento/caixa não tratada: use 'Débitos'). Pagina sozinho."""
    achadas, pg = [], 0
    while True:
        c = req("GET", "/tarefas", params={"categoria": categoria, "dataAcaoInicio": inicio, "dataAcaoFim": fim,
                                           "status": status, "size": 200, "page": pg}).get("content", [])
        achadas += [t for t in c if trecho.lower() in (t.get("nome") or "").lower()]
        if len(c) < 200:
            return achadas
        pg += 1


def atividades(tarefa_id):
    """Atividades (etapas) de uma tarefa: id, ordem, tipo (C=check, P=anexo, 16=envio), respondida, arquivos."""
    a = req("GET", f"/tarefas/{tarefa_id}/atividades")
    return a if isinstance(a, list) else a.get("content", [])

# Endpoint de escrita: POST /atividades/resposta (multipart: arquivo, idAtividade, competencia AAAAMM, inscricao, usuario, sistema).
# É "exclusivo para parceiros" e exige o código 'sistema' do parceiro. Não testado (grava em tarefa real).
