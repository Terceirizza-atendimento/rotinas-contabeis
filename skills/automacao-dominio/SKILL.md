---
name: automacao-dominio
description: Automação do Domínio Contabilidade (Thomson Reuters) da Terceirizza por scripts Python com OCR e controle de tela: abrir o sistema e logar, trocar de empresa, integrar fiscal/folha, exportar Balancete, Razão e Plano de contas, validar as exportações, classificar lançamentos e montar o CSV, importar o CSV, alterar/excluir lançamentos já gravados e fechar um cliente de ponta a ponta. Use SEMPRE que o usuário falar em "Domínio", "fechamento", "fechar o cliente NNN", "balancete", "razão", "plano de contas", "importar CSV", "integrar fiscal/folha", "alterar lançamentos" ou "trocar empresa". Esta skill é o índice: ela escolhe o script e lê a referência certa em references/.
---

# Automação do Domínio (importação e fechamento)

Scripts em `scripts/` (Python + pyautogui + OCR local, sem custo de tokens). Cada etapa tem uma referência detalhada em `references/` — **leia a referência da etapa antes de rodar o script**, porque ela traz as armadilhas de tela, as posições validadas e o que conferir.

Pré-requisitos: Windows com o Domínio Web aberto, `DW_USER`/`DW_PASS` (portal) e `DW_SYS_USER`/`DW_SYS_PASS` (sistema) em variáveis de ambiente. **Nunca** grave senhas em arquivos.

## Qual etapa usar

| Pedido | Script | Referência |
|---|---|---|
| "Iniciar/retomar fechamento" (fluxo completo, com painel e validador) | vários | `references/iniciar-fechamento.md` |
| "Fechar o cliente NNN" em um comando, por etapas retomáveis | `fechar.py` | `references/fechar-cliente-dominio.md` |
| Abrir o Domínio, logar, gerar Balancete/Razão e exportar Excel | `login_portal.py`, `abrir_contabilidade.py`, `balancete.py`, `razao.py`, `exportar_excel.py`, `fechar_exportar.py` | `references/abrir-dominio-contabilidade.md` |
| Trocar a empresa ativa | `trocar_empresa.py` | `references/trocar-empresa-dominio.md` |
| Integrar fiscal e folha na competência | `integracao.py` | `references/integrar-fiscal-folha-dominio.md` |
| Exportar o plano de contas | `plano_contas.py` | `references/exportar-plano-de-contas.md` |
| Validar Balancete/Razão/Plano exportados (somente leitura) | `validar_exportacao.py` | `references/validar-exportacao-dominio.md` |
| Classificar por regras e montar o CSV de importação | `classificar.py`, `montar_csv.py` | `references/classificar-e-gerar-csv.md` |
| Importar o CSV (ensaio sem gravar, depois Gravar uma vez) | `importar_csv.py` | `references/importar-csv-dominio.md` |
| Corrigir conta/valor/data de lançamento já gravado, excluir lotes | `dominio_ops.py` (biblioteca) | `references/alterar-lancamentos-dominio.md` |
| Pendências de retorno no Digisac (somente leitura) | `digisac_pendencias.py` | — |

Bibliotecas (não rodam sozinhas): `dominio_lib.py` (controle de janelas), `dominio_ops.py` (telas do Domínio), `ocr.py` (leitura de campos). `listar_scripts.py` imprime o `Uso:` de cada script — rode no começo, pois os scripts mudam entre sessões.

## Ordem típica de um fechamento

1. `login_portal.py` e `abrir_contabilidade.py` (sessão aberta)
2. `trocar_empresa.py <código>` (confere pela barra)
3. `integracao.py <MMAAAA> --fiscal --folha` (se faltarem entradas, saídas, serviços ou folha)
4. `fechar_exportar.py` (Balancete + Razão + Plano) e `validar_exportacao.py`
5. `classificar.py` e `montar_csv.py` (CSV em "02 Pendente de importar")
6. `importar_csv.py` sem `--gravar` (ensaio) e, com OK da usuária, `--gravar`
7. Reexportar o balancete e conferir

## Regras que valem sempre

- **Gravar é irreversível**: ensaio primeiro, Gravar uma única vez e só com o OK da usuária.
- Confirme a empresa ativa pela barra do Domínio antes de exportar, integrar ou importar.
- Corrija lançamentos pela origem (Alteração de Lançamentos), não por CSV de reclassificação.
- Controle de tela é frágil: não mexa no mouse/teclado enquanto o script roda e use OCR em vez de prints.
- Dados de clientes (planilhas, PDFs, regras por cliente) ficam fora do repositório.
