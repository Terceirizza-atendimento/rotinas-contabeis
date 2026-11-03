"""Emite NFS-e a partir de dados/notas_<SIGLA>.csv, sem duplicar (registro em dados/emitidas.csv).

Uso:  python -I emitir.py RJ homolog           (teste, sem efeito fiscal)
      python -I emitir.py RJ prod              (simulação: só mostra o que seria emitido)
      python -I emitir.py RJ prod --confirmo   (emite de verdade)
CSV (;): data;documento;nome;cep;numero;complemento;descricao;valor[;logradouro;bairro]   (data = competência dd/mm/aaaa;
     logradouro/bairro opcionais: só para CEP único de cidade pequena, quando o ViaCEP devolve vazio)
"""
import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
import base64, csv, gzip, hashlib, json, os, re, subprocess, sys
from datetime import datetime
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
DADOS = os.path.join(AQUI, "dados")


def env(n):
    if os.environ.get(n):
        return os.environ[n]
    return subprocess.run(["powershell", "-NoProfile", "-Command", f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetEnvironmentVariable('{n}','User')"],
                          capture_output=True).stdout.decode("utf-8").strip()


def ler_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ("homolog", "prod"):
        sys.exit(__doc__)
    sigla, amb, confirmo = sys.argv[1].upper(), sys.argv[2], "--confirmo" in sys.argv
    cli = json.load(open(os.path.join(DADOS, "clientes.json"), encoding="utf-8"))[sigla]
    for n in (f"NFSE_PFX_{sigla}", f"NFSE_PFX_SENHA_{sigla}"):
        os.environ[n] = env(n)
    import nfse
    log_p = os.path.join(DADOS, "emitidas.csv")
    feitas = {r["chave_dedup"] for r in ler_csv(log_p) if r["ambiente"] == amb and r["sigla"] == sigla}
    notas = ler_csv(os.path.join(DADOS, f"notas_{sigla}.csv"))
    s = nfse.sessao(sigla) if (amb == "homolog" or confirmo) else None
    ndps = 1 + sum(1 for r in ler_csv(log_p) if r["ambiente"] == amb and r["sigla"] == sigla)
    novas = 0
    for n in notas:
        doc = re.sub(r"\D", "", n["documento"]); valor = float(n["valor"].replace(".", "").replace(",", "."))
        d, m, a = n["data"].split("/"); compet = f"{a}-{m}-{d}"
        chave = hashlib.sha1(f"{sigla}|{compet}|{doc}|{valor:.2f}|{n['descricao'].strip().upper()}".encode()).hexdigest()[:16]
        rotulo = f"{n['nome']} | {n['data']} | R$ {valor:.2f}"
        if chave in feitas:
            print(f"  já emitida, pulando: {rotulo}"); continue
        if amb == "prod" and not confirmo:
            print(f"  [simulação] emitiria: {rotulo}"); novas += 1; continue
        end = nfse.viacep(re.sub(r"\D", "", n["cep"]))
        tom = dict(doc=doc, nome=n["nome"].strip().upper(), cep=re.sub(r"\D", "", n["cep"]), cMun=end["cMun"], logradouro=(n.get("logradouro") or end["logradouro"]).strip().upper(),
                   numero=n["numero"], bairro=(n.get("bairro") or end["bairro"]).strip().upper(), complemento=n["complemento"])
        extra = "<finNFSe>0</finNFSe>" if amb == "homolog" else ""
        xml = nfse.montar_dps(amb=2 if amb == "homolog" else 1, prest_cnpj=cli["cnpj"], fone=cli["fone"], email=cli["email"], serie=cli["serie"],
                              ndps=ndps, data_compet=compet, tomador=tom, descricao=n["descricao"], valor=valor, extra_emit=extra,
                              cloc=cli["cloc"], ctrib=cli["ctrib"], cnbs=cli["cnbs"], p_tot_trib_sn=cli["aliquota_sn"], ctrib_mun=cli.get("ctrib_mun", ""))
        st, r = nfse.emitir(s, amb, nfse.assinar(xml, sigla))
        if "nfseXmlGZipB64" not in r:
            print(f"  FALHA {st}: {rotulo}\n    {str(r.get('erros', r))[:400]}\n  Parando para não gerar numeração fora de ordem."); break
        x = gzip.decompress(base64.b64decode(r["nfseXmlGZipB64"])).decode("utf-8")
        nnfse = re.findall(r"<nNFSe>(\d+)", x)[0]
        with open(log_p, "a", encoding="utf-8-sig", newline="") as f:
            csv.writer(f, delimiter=";").writerow([chave, sigla, amb, nnfse, r["chaveAcesso"], datetime.now().isoformat(timespec="seconds")])
        print(f"  EMITIDA nº {nnfse}: {rotulo} | {r['chaveAcesso']}"); ndps += 1; novas += 1
    print(f"Fim. {novas} nota(s) {'a emitir' if amb == 'prod' and not confirmo else 'emitida(s)'}.")


main()
