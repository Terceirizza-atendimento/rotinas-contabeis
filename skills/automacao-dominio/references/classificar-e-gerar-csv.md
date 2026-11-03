---
name: classificar-e-gerar-csv
description: Reclassifica lançamentos do Razão e lança o extrato do banco por regras do cliente (classificar.py) e monta o CSV único de importação do Domínio (montar_csv.py), sem agentes. Use quando for gerar o arquivo de importação de um fechamento ou editar as regras de classificação de um cliente.
---

# Classificar e gerar o CSV de importação

**Estado atual (03/11/2026): `scripts\regras\` está vazia — nenhum cliente tem `NNN.json`.** `classificar.py` não funciona para nenhum cliente hoje (vai falhar ou não casar nada). Não invente um JSON de regras: ou (a) monte o `lotes.json`/CSV à mão a partir do diagnóstico já aprovado pela usuária (formato no docstring de `montar_csv.py`), ou (b) crie o `NNN.json` do cliente **com a usuária**, regra por regra, e só então rode `classificar.py`. Avise que esta etapa está pulando direto para o modo manual antes de começar.

Scripts: `automacao-domino\scripts\classificar.py` e `montar_csv.py` (rode dentro de `automacao-domino\scripts`). Não tocam no Domínio: só leem arquivos do cliente e gravam o CSV.

```
python classificar.py "<pasta do cliente>" regras\NNN.json
python montar_csv.py "<pasta do cliente>" <lotes.json> [nome_saida.csv]
```
- `classificar.py` lê `Razão.xlsx` (contas a reclassificar) e o extrato do banco (só linhas ainda **não** lançadas no Razão), aplica as regras (primeira que casar, por contraparte), grava `saida\lotes.json` e `saida\pendencias.json` e chama `montar_csv.py`.
- `montar_csv.py` valida e grava **um único CSV** em `<pasta>\Arquivos de importação\02 Pendente de importar` (cp1252, `;`, CRLF, vírgula decimal, 10 colunas, "Inicia Lote" só na 1ª linha de cada lote; sobrescreve o mesmo nome, nunca `_v2`). **Não grava** se houver FALHA: lote que não fecha, conta fora do `Plano de contas.txt` da pasta (99999 = conta nova pendente), `;` ou entidade HTML no histórico, data/valor inválido. Formato e regras: `CONTEXTOS\regras-gerais-fechamento-e-importacao.md`, seção 3.
- O que não casa com regra, ou espera conta nova, vira **PENDÊNCIA**: nunca chute. Apresente as pendências à usuária (dúvidas numeradas) antes de fechar o CSV.

## Regras por cliente
`automacao-domino\scripts\regras\NNN.json` (contrapartes → conta, `aguardando_conta`, padrões, `banco`). Regra nova dada pela usuária = editar o JSON, não o código, **só depois do OK dela** (manutenção do contexto, CLAUDE.md).

## Cuidados
- Conta do **plano do cliente** (códigos são por cliente; nunca reutilize de outro).
- Extrato do banco normalmente **não está lançado**: parta dessa premissa e confirme no Razão por data e valor antes de incluir.
- Reclassificação leva a data do lançamento original; histórico neutro e cita o lote de origem.
- Se o CSV **substitui** lançamentos existentes, primeiro listar os lotes errados para a usuária **excluir** (Utilitários → Exclusão → Lançamentos, filtro por período e conta; ver `automacao-importacao-csv.md`). Nunca importar por cima.
- Depois de gerar, reabra o CSV e confira linhas/lotes/soma; só um arquivo em `02 Pendente de importar`; parciais e antigos vão para `03 Substituidos (nao importar)`.
