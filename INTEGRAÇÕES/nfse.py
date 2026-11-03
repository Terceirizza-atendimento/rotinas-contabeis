"""Cliente mínimo da API Nacional da NFS-e (mTLS com certificado A1).

Credenciais: NFSE_PFX_<SIGLA> e NFSE_PFX_SENHA_<SIGLA> (ver configurar_certificado.ps1).
"""
import atexit, os, tempfile
import requests
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

HOSTS = {
    "prod": {"sefin": "https://sefin.nfse.gov.br/sefinnacional", "adn": "https://adn.nfse.gov.br"},
    "homolog": {"sefin": "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
                "adn": "https://adn.producaorestrita.nfse.gov.br"},
}


def sessao(sigla):
    caminho, senha = os.environ.get(f"NFSE_PFX_{sigla}"), os.environ.get(f"NFSE_PFX_SENHA_{sigla}")
    if not caminho or not senha:
        raise SystemExit(f"Variáveis NFSE_PFX_{sigla} não definidas. Rode configurar_certificado.ps1.")
    with open(caminho, "rb") as f:
        key, cert, extra = pkcs12.load_key_and_certificates(f.read(), senha.encode())
    d = tempfile.mkdtemp()
    cp, kp = os.path.join(d, "c.pem"), os.path.join(d, "k.pem")
    with open(cp, "wb") as f:
        f.write(cert.public_bytes(Encoding.PEM))
        for e in extra or []:
            f.write(e.public_bytes(Encoding.PEM))
    with open(kp, "wb") as f:
        f.write(key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))
    atexit.register(lambda: [os.remove(p) for p in (cp, kp)] and os.rmdir(d))
    s = requests.Session()
    s.cert = (cp, kp)
    s.headers["Accept"] = "application/json"
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"
    return s


# ---------------------------------------------------------------- emissão
import base64, gzip, json, re
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape
from lxml import etree
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

NS = "http://www.sped.fazenda.gov.br/nfse"
DSIG = "http://www.w3.org/2000/09/xmldsig#"
BRT = timezone(timedelta(hours=-3))


def viacep(cep):
    r = requests.get(f"https://viacep.com.br/ws/{re.sub(r'\D', '', cep)}/json/", timeout=20).json()
    return {"cMun": r["ibge"], "bairro": r["bairro"], "logradouro": r["logradouro"]}


def montar_dps(*, amb, prest_cnpj, fone, email, serie, ndps, data_compet, tomador, descricao, valor,
               extra_emit="", cloc="4314902", ctrib="041201", cnbs="123012300", p_tot_trib_sn="6.00", ctrib_mun=""):
    """tomador: dict(doc, nome, cep, cMun, logradouro, numero, bairro, complemento='')."""
    tag = "CNPJ" if len(tomador["doc"]) == 14 else "CPF"
    dps_id = f"DPS{cloc}2{prest_cnpj}{int(serie):05d}{int(ndps):015d}"
    dh = (datetime.now(BRT) - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    compl = f"<xCpl>{escape(tomador['complemento'])}</xCpl>" if tomador.get("complemento") else ""
    return (f'<DPS versao="1.01" xmlns="{NS}"><infDPS Id="{dps_id}"><tpAmb>{amb}</tpAmb><dhEmi>{dh}</dhEmi>'
            f'<verAplic>integracoes_1.0</verAplic><serie>{int(serie)}</serie><nDPS>{int(ndps)}</nDPS>'
            f'<dCompet>{data_compet}</dCompet><tpEmit>1</tpEmit>{extra_emit}<cLocEmi>{cloc}</cLocEmi>'
            f'<prest><CNPJ>{prest_cnpj}</CNPJ><fone>{fone}</fone><email>{escape(email)}</email>'
            f'<regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN><regEspTrib>0</regEspTrib></regTrib></prest>'
            f'<toma><{tag}>{tomador["doc"]}</{tag}><xNome>{escape(tomador["nome"])}</xNome><end><endNac>'
            f'<cMun>{tomador["cMun"]}</cMun><CEP>{tomador["cep"]}</CEP></endNac><xLgr>{escape(tomador["logradouro"])}</xLgr>'
            f'<nro>{escape(tomador["numero"])}</nro>{compl}<xBairro>{escape(tomador["bairro"])}</xBairro></end></toma>'
            f'<serv><locPrest><cLocPrestacao>{cloc}</cLocPrestacao></locPrest><cServ><cTribNac>{ctrib}</cTribNac>'
            f'{f"<cTribMun>{ctrib_mun}</cTribMun>" if ctrib_mun else ""}'
            f'<xDescServ>{escape(descricao)}</xDescServ><cNBS>{cnbs}</cNBS></cServ></serv>'
            f'<valores><vServPrest><vServ>{valor:.2f}</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN>'
            f'<tpRetISSQN>1</tpRetISSQN></tribMun><totTrib><pTotTribSN>{p_tot_trib_sn}</pTotTribSN></totTrib></trib></valores>'
            f'</infDPS></DPS>')


def assinar(xml_str, sigla):
    caminho, senha = os.environ[f"NFSE_PFX_{sigla}"], os.environ[f"NFSE_PFX_SENHA_{sigla}"]
    with open(caminho, "rb") as f:
        key, cert, _ = pkcs12.load_key_and_certificates(f.read(), senha.encode())
    root = etree.fromstring(xml_str.encode())
    inf = root.find(f"{{{NS}}}infDPS")
    c14n = lambda el: etree.tostring(el, method="c14n", exclusive=True, with_comments=False)
    digest = base64.b64encode(_sha256(c14n(inf))).decode()
    si = (f'<SignedInfo xmlns="{DSIG}"><CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>'
          f'<SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>'
          f'<Reference URI="#{inf.get("Id")}"><Transforms><Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>'
          f'<Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></Transforms>'
          f'<DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/><DigestValue>{digest}</DigestValue></Reference></SignedInfo>')
    si_c14n = etree.tostring(etree.fromstring(si), method="c14n", exclusive=True)
    sig = base64.b64encode(key.sign(si_c14n, padding.PKCS1v15(), hashes.SHA256())).decode()
    cert_b64 = base64.b64encode(cert.public_bytes(Encoding.DER)).decode()
    si_interno = si.replace(f' xmlns="{DSIG}"', "", 1)
    signature = (f'<Signature xmlns="{DSIG}">{si_interno}'
                 f'<SignatureValue>{sig}</SignatureValue><KeyInfo><X509Data><X509Certificate>{cert_b64}</X509Certificate></X509Data></KeyInfo></Signature>')
    return xml_str.replace("</DPS>", signature + "</DPS>")


def _sha256(b):
    h = hashes.Hash(hashes.SHA256()); h.update(b); return h.finalize()


def emitir(sessao_http, ambiente, xml_assinado):
    """POST /nfse. Retorna (status, json)."""
    if not xml_assinado.startswith("<?xml"):
        xml_assinado = '<?xml version="1.0" encoding="UTF-8"?>' + xml_assinado
    corpo = {"dpsXmlGZipB64": base64.b64encode(gzip.compress(xml_assinado.encode("utf-8"))).decode()}
    r = sessao_http.post(HOSTS[ambiente]["sefin"] + "/nfse", json=corpo, timeout=60)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"raw": r.text[:300]}
