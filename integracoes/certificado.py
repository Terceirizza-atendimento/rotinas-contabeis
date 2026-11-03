"""Acesso com certificado digital A1 (mTLS) para qualquer cliente configurado. Independente dos outros módulos.

Pré-requisito (uma vez por cliente): configurar_certificado.ps1  -> cria NFSE_PFX_<SIGLA> e NFSE_PFX_SENHA_<SIGLA>.

Linha de comando (use sempre `python -I`, a partir de qualquer pasta):
  python -I certificado.py listar                         siglas configuradas
  python -I certificado.py info RJ                        titular, CNPJ e validade do certificado
  python -I certificado.py GET RJ <url> [--saida arq]     GET autenticado (imprime o corpo ou salva em arquivo)
  Em qualquer comando, no lugar da sigla pode ir o caminho de QUALQUER .pfx/.p12 (a senha é pedida oculta no terminal).
  e-CAC e Regularize: o login tem hCaptcha, que só a pessoa resolve; ver `python -I certificado.py ajuda-captcha`.
  python -I certificado.py POST RJ <url> <arquivo.json>   POST autenticado com corpo JSON

Em Python:  import certificado; s = certificado.sessao("RJ"); s.get(url)   (requests.Session com o certificado)
Só leitura por padrão: POST é para o usuário pedir explicitamente (ex.: emitir nota).
"""
import atexit, os, subprocess, sys, tempfile


def _env(n):
    if os.environ.get(n):
        return os.environ[n]
    try:
        return subprocess.run(["powershell", "-NoProfile", "-Command",
                               f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetEnvironmentVariable('{n}','User')"],
                              capture_output=True).stdout.decode("utf-8").strip()
    except FileNotFoundError:
        return ""


def siglas():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "[Environment]::GetEnvironmentVariables('User').Keys | Where-Object { $_ -like 'NFSE_PFX_*' -and $_ -notlike 'NFSE_PFX_SENHA_*' }"],
                             capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        out = []
    out += [k for k in os.environ if k.startswith("NFSE_PFX_") and not k.startswith("NFSE_PFX_SENHA_")]
    return sorted({k[len("NFSE_PFX_"):] for k in out})


def _carregar(sigla):
    """`sigla` pode ser a sigla configurada (RJ) OU o caminho de qualquer arquivo .pfx/.p12.
    Para um .pfx avulso a senha vem da variável CERT_SENHA ou é pedida no terminal (oculta)."""
    from cryptography.hazmat.primitives.serialization import pkcs12
    if os.path.isfile(sigla):
        caminho = sigla
        senha = os.environ.get("CERT_SENHA") or __import__("getpass").getpass(f"Senha do certificado {os.path.basename(sigla)} (oculta): ")
    else:
        sigla = sigla.upper()
        caminho, senha = _env(f"NFSE_PFX_{sigla}"), _env(f"NFSE_PFX_SENHA_{sigla}")
        if not caminho or not senha:
            sys.exit(f"Certificado de '{sigla}' não configurado. Rode configurar_certificado.ps1, ou passe o caminho do .pfx no lugar da sigla.")
    if not os.path.isfile(caminho):
        sys.exit(f"Arquivo do certificado não encontrado: {caminho}\n(Drive G: montado? Rode configurar_certificado.ps1 de novo se o arquivo mudou de lugar.)")
    with open(caminho, "rb") as f:
        return pkcs12.load_key_and_certificates(f.read(), senha.encode())


def sessao(sigla):
    """requests.Session autenticada por mTLS com o certificado do cliente. Os PEM temporários são apagados ao sair."""
    import requests
    try:  # usa o repositório de certificados do Windows: sites do governo usam a cadeia ICP-Brasil
        import truststore; truststore.inject_into_ssl()
    except ImportError:
        pass
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
    key, cert, extra = _carregar(sigla)
    d = tempfile.mkdtemp()
    cp, kp = os.path.join(d, "c.pem"), os.path.join(d, "k.pem")
    with open(cp, "wb") as f:
        f.write(cert.public_bytes(Encoding.PEM))
        for e in extra or []:
            f.write(e.public_bytes(Encoding.PEM))
    with open(kp, "wb") as f:
        f.write(key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))

    def limpar():
        for p in (cp, kp):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(d)
        except OSError:
            pass
    atexit.register(limpar)
    s = requests.Session()
    s.cert = (cp, kp)
    s.headers.update({"Accept": "application/json",
                      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"})
    return s


def info(sigla):
    _, cert, _ = _carregar(sigla)
    print("Titular :", cert.subject.rfc4514_string())
    print("Validade:", cert.not_valid_before_utc.strftime("%d/%m/%Y"), "a", cert.not_valid_after_utc.strftime("%d/%m/%Y"))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "ajuda-captcha":
        print("O e-CAC (cav.receita.fazenda.gov.br) entra pelo gov.br e exige hCaptcha (confirmado). O Regularize (PGFN) também usa\n"
              "login gov.br; não consegui confirmar o captcha dele por script.\n"
              "Captcha não é resolvido nem contornado por automação. Caminho prático:\n"
              " 1. Instale o certificado no Windows pelo instalar_certificado.ps1 (você roda, senha oculta).\n"
              " 2. No Chrome, abra o site, resolva o captcha e escolha 'Certificado digital' no gov.br.\n"
              " 3. Com a sessão já logada, peça ao Claude para continuar a navegação (Claude in Chrome).\n"
              "Para dados do e-CAC por API oficial (sem captcha), a opção é o Integra Contador (SERPRO).")
    elif a[0] == "listar":
        print("Certificados configurados:", ", ".join(siglas()) or "(nenhum)")
    elif a[0] == "info" and len(a) == 2:
        info(a[1])
    elif a[0] in ("GET", "POST") and len(a) >= 3:
        s = sessao(a[1])
        if a[0] == "GET":
            r = s.get(a[2], timeout=60)
        else:
            import json
            r = s.post(a[2], json=json.load(open(a[3], encoding="utf-8")), timeout=60)
        print(f"HTTP {r.status_code} | {r.headers.get('content-type')} | {len(r.content)} bytes", file=sys.stderr)
        if "--saida" in a:
            open(a[a.index("--saida") + 1], "wb").write(r.content)
            print("salvo em", a[a.index("--saida") + 1], file=sys.stderr)
        else:
            print(r.text[:4000])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
