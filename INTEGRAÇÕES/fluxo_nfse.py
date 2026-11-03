"""Fluxo completo de NFS-e de um cliente: emitir -> PDF -> arquivar no Drive -> enviar pelo Digisac -> fechar chamado.

Uso:  python -I fluxo_nfse.py RJ            (começa pela simulação; cada etapa irreversível pede confirmação digitada)
      python -I fluxo_nfse.py RJ --retomar  (pula a emissão e trata notas já emitidas e ainda não enviadas)
Pré-requisito: dados/notas_<SIGLA>.csv preenchido (ver emitir.py).
"""
import base64, csv, gzip, json, os, re, shutil, subprocess, sys, time
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
DADOS = os.path.join(AQUI, "dados"); DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
PY = [sys.executable, "-W", "ignore", "-I"]


def env(n):
    if os.environ.get(n):
        return os.environ[n]
    return subprocess.run(["powershell", "-NoProfile", "-Command", f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetEnvironmentVariable('{n}','User')"],
                          capture_output=True).stdout.decode("utf-8").strip()


def ler(p):
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def confirmar(palavra, pergunta):
    r = input(f"\n{pergunta}\nDigite {palavra} para continuar (qualquer outra coisa cancela): ").strip()
    if r != palavra:
        sys.exit("Cancelado. Nada foi feito nesta etapa.")


def etapa(n, t):
    print(f"\n=== Etapa {n}: {t} ===")


def rodar_emitir(sigla, *extra):
    return subprocess.run(PY + [os.path.join(AQUI, "emitir.py"), sigla, "prod", *extra], capture_output=True).stdout.decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sigla = sys.argv[1].upper(); retomar = "--retomar" in sys.argv
    cli = json.load(open(os.path.join(DADOS, "clientes.json"), encoding="utf-8"))[sigla]
    for n in (f"NFSE_PFX_{sigla}", f"NFSE_PFX_SENHA_{sigla}", "DIGISAC_TOKEN"):
        os.environ[n] = env(n)
    import nfse, digisac

    if not retomar:
        etapa(1, "Simulação da emissão (nada é emitido)")
        sim = rodar_emitir(sigla)
        print(sim)
        if "[simulação]" in sim:
            confirmar("EMITIR", "Conferiu os dados acima? A emissão em produção só se desfaz cancelando a nota.")
            etapa(2, "Emissão em produção")
            print(rodar_emitir(sigla, "--confirmo"))
        else:
            print("Nenhuma nota nova para emitir; seguindo para as pendentes de envio.")

    enviadas = {r["chave_acesso"] for r in ler(os.path.join(DADOS, "enviadas.csv"))}
    pend = [r for r in ler(os.path.join(DADOS, "emitidas.csv"))
            if r["sigla"] == sigla and r["ambiente"] == "prod" and r["chave_acesso"] not in enviadas]
    if not pend:
        sys.exit("\nNenhuma nota pendente de envio. Fim.")
    s = nfse.sessao(sigla); h = nfse.HOSTS["prod"]; itens = []
    for r in pend:
        j = None
        for tent in range(1, 6):
            try:
                j = s.get(f"{h['sefin']}/nfse/{r['chave_acesso']}", timeout=60).json()
                if "nfseXmlGZipB64" in j:
                    break
            except Exception as e:
                print(f"  portal instável ao buscar a nota (tentativa {tent}/5): {type(e).__name__}")
            time.sleep(10)
        if not j or "nfseXmlGZipB64" not in j:
            sys.exit(f"\nO portal não respondeu. A nota {r['chave_acesso']} JÁ FOI EMITIDA. Rode de novo com --retomar mais tarde.")
        x = gzip.decompress(base64.b64decode(j["nfseXmlGZipB64"])).decode("utf-8")
        toma = re.search(r"<toma>.*?<xNome>([^<]*)</xNome>", x, re.S).group(1)
        itens.append(dict(chave=r["chave_acesso"], nome=toma.title(), valor=float(re.search(r"<vServ>([\d.]+)</vServ>", x).group(1))))

    pasta_local = os.path.join(AQUI, "..", "NFSE_" + sigla); os.makedirs(pasta_local, exist_ok=True)
    caminho = lambda i: os.path.join(pasta_local, f"{i['nome'].upper()} - {i['chave']}.pdf")

    etapa(3, f"PDFs (DANFSe) de {len(itens)} nota(s)")
    pdfs = {}
    for it in itens:
        r = s.get(f"{h['adn']}/danfse/{it['chave']}", timeout=30, headers={"Accept": "application/pdf"})
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            open(caminho(it), "wb").write(r.content); pdfs[it["chave"]] = caminho(it); print("  baixado pela API:", it["nome"])
    faltam = [i for i in itens if i["chave"] not in pdfs]
    if faltam:
        print("\n  API de PDF indisponível. Baixe pela Consulta Pública (nfse.gov.br/consultapublica; o captcha é seu) as chaves abaixo.")
        print("  O script espera os arquivos aparecerem em Downloads (até 15 min):")
        for i in faltam:
            print("   -", i["chave"], f"({i['nome']})")
        limite = time.time() + 900
        while faltam and time.time() < limite:
            for i in list(faltam):
                p = os.path.join(DOWNLOADS, i["chave"] + ".pdf")
                if os.path.exists(p) and os.path.getsize(p) > 1000:
                    b = open(p, "rb").read()
                    if b[:4] == b"%PDF" and b"%%EOF" in b[-64:]:
                        shutil.copy(p, caminho(i)); pdfs[i["chave"]] = caminho(i); faltam.remove(i); print("  recebido:", i["nome"])
            time.sleep(5)
        if faltam:
            sys.exit("Tempo esgotado sem todos os PDFs. Rode de novo com --retomar quando baixar.")

    etapa(4, "Arquivar na pasta do cliente (Drive)")
    pasta = cli.get("pasta_drive")
    if pasta and os.path.isdir(pasta):
        for p in pdfs.values():
            d = os.path.join(pasta, os.path.basename(p))
            if os.path.exists(d):
                print("  já existe:", os.path.basename(p)[:40])
            else:
                shutil.copy(p, d); print("  copiado:", os.path.basename(p)[:40])
    else:
        print("  pasta_drive não configurada ou não encontrada: pulando.")

    etapa(5, "Mensagem ao cliente (Digisac)")
    hora = datetime.now().hour
    saud = "bom dia" if hora < 12 else ("boa tarde" if hora < 18 else "boa noite")
    linhas = "\n".join(f"{i['nome']} - R$ {i['valor']:.2f}".replace(".", ",") for i in itens)
    texto = f"Olá, {saud}! Seguem em anexo as notas fiscais emitidas:\n{linhas}\nQualquer dúvida estamos à disposição!"
    print(f"\nPara: contato {cli['digisac_contato']}\n---\n{texto}\n---\nAnexos: " + ", ".join(os.path.basename(p)[:30] + "..." for p in pdfs.values()))
    print("(Atenção: leia o fim da conversa no Digisac; se a Letícia já está falando com o cliente, ajuste o cumprimento.)")
    confirmar("ENVIAR", "Enviar texto e PDFs ao cliente? Mensagem enviada não se desfaz.")
    digisac.enviar_texto(cli["digisac_contato"], texto)
    for p in pdfs.values():
        digisac.enviar_pdf(cli["digisac_contato"], p)
    with open(os.path.join(DADOS, "enviadas.csv"), "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        for i in itens:
            w.writerow([i["chave"], sigla, datetime.now().isoformat(timespec="seconds")])
    print("  enviado.")
    if input("\nFechar o chamado no Digisac? (s/N): ").strip().lower() == "s":
        digisac.fechar_chamado(cli["digisac_contato"]); print("  chamado fechado.")
    print("\nFluxo concluído.")


main()
