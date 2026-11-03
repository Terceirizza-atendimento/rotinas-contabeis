# Rotinas Contábeis – Terceirizza

Catálogo das skills do Claude e dos scripts de automação usados nos chamados da contabilidade.
Este repositório contém **apenas código e documentação**. Dados de clientes, PDFs, planilhas, certificados e senhas nunca entram aqui (veja `.gitignore`).

## Skills (`skills/`)

| Skill | Para que serve |
|---|---|
| [emitir-nfse](skills/emitir-nfse/SKILL.md) | Fluxo padrão para emitir qualquer NFS-e: escolhe o canal (API, portal nacional ou Pantano Grande), valida o pedido, evita nDPS duplicado e registra a nota. |
| [emitir-nfse-portal-nacional](skills/emitir-nfse-portal-nacional/SKILL.md) | Emissão no Emissor Nacional (nfse.gov.br) para prestadores do Simples e download dos DANFSe. |
| [emitir-nfse-gm](skills/emitir-nfse-gm/SKILL.md) | Emissão das notas da GM Comunicação e Marketing, com parâmetros fixos. |
| [emitir-nfse-pantano-grande](skills/emitir-nfse-pantano-grande/SKILL.md) | Emissão e cancelamento no portal Cidade360 de Pantano Grande/RS (Anjos Segurança). |
| [enviar-notas-digisac](skills/enviar-notas-digisac/SKILL.md) | Envio dos PDFs ao cliente pelo Digisac e fechamento do chamado. |
| [gclick-diagnostico-fiscal](skills/gclick-diagnostico-fiscal/SKILL.md) | Certidões/diagnósticos do SIEG enviados pelas tarefas "Consulta Relação Débitos" do Gclick. |
| [sieg-baixar-diagnosticos](skills/sieg-baixar-diagnosticos/SKILL.md) | Baixa e valida diagnósticos e certidões do SIEG. |

## Scripts

| Pasta | Conteúdo |
|---|---|
| `IMPORTAÇÃO DOMINIO/automacao-domino/scripts` | Automação do Domínio: importar CSV, balancete, razão, plano de contas, fechamento, exportação. |
| `INTEGRAÇÕES` | Clientes de API (NFS-e, Digisac, Gclick) e fluxos de emissão/diagnóstico. |
| `integracoes` | Certificado A1 e emissão de NFS-e por API. |
| `NOTAS FISCAIS EMITIDAS` | Registro padronizado das notas emitidas. |
| `PARCELAMENTOS` | Validação dos arquivos do SIEG. |
| `AUTOMAÇÃO SOCIETÁRIO` | Apps Script da planilha de cadastro. |

## Como usar as skills

Copie a pasta da skill desejada para `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`) e reinicie o Claude Code.

## Segredos

Senhas, tokens e certificados vêm de variáveis de ambiente (`DIGISAC_TOKEN`, `CERT_SENHA`, `NFSE_PFX_*`) ou são digitados na hora. **Nunca** coloque credenciais em arquivos deste repositório.
