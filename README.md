# Rotinas Contábeis – Terceirizza

Catálogo das skills do Claude e dos scripts de automação usados nos chamados da contabilidade.
Este repositório contém **apenas código e documentação**. Dados de clientes, PDFs, planilhas, certificados e senhas nunca entram aqui (veja `.gitignore`).

## Skills (`skills/`)

| Skill | Para que serve |
|---|---|
| [emitir-nfse-portal-nacional](skills/emitir-nfse-portal-nacional/SKILL.md) | Emissão no Emissor Nacional (nfse.gov.br) para prestadores do Simples e download dos DANFSe. |
| [emitir-nfse-gm](skills/emitir-nfse-gm/SKILL.md) | Emissão das notas da GM Comunicação e Marketing, com parâmetros fixos. |
| [automacao-dominio](skills/automacao-dominio/SKILL.md) | Automação do Domínio Contabilidade: abrir/logar, trocar empresa, integrar fiscal/folha, exportar e validar balancete/razão/plano, classificar, importar CSV, alterar lançamentos e fechar cliente. Scripts em scripts/, passo a passo em eferences/. |
| [enviar-notas-digisac](skills/enviar-notas-digisac/SKILL.md) | Envio dos PDFs ao cliente pelo Digisac e fechamento do chamado. |
| [gclick-diagnostico-fiscal](skills/gclick-diagnostico-fiscal/SKILL.md) | Certidões/diagnósticos do SIEG enviados pelas tarefas "Consulta Relação Débitos" do Gclick. |
| [sieg-baixar-diagnosticos](skills/sieg-baixar-diagnosticos/SKILL.md) | Baixa e valida diagnósticos e certidões do SIEG. |

## Scripts

| Pasta | Conteúdo |
|---|---|
| `INTEGRAÇÕES` | Clientes de API (NFS-e, Digisac, Gclick) e fluxos de emissão/diagnóstico. |
| `integracoes` | Certificado A1 e emissão de NFS-e por API. |
| `NOTAS FISCAIS EMITIDAS` | Registro padronizado das notas emitidas. |
| `PARCELAMENTOS` | Validação dos arquivos do SIEG. |
| `AUTOMAÇÃO SOCIETÁRIO` | Apps Script da planilha de cadastro. |

## Como usar as skills

Copie a pasta da skill desejada para `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`) e reinicie o Claude Code.

## Segredos

Senhas, tokens e certificados vêm de variáveis de ambiente (`DIGISAC_TOKEN`, `CERT_SENHA`, `NFSE_PFX_*`) ou são digitados na hora. **Nunca** coloque credenciais em arquivos deste repositório.
