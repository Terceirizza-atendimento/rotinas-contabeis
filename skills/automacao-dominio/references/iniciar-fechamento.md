---
name: iniciar-fechamento
description: Fechamento contábil (Terceirizza) no Domínio, fluxo validado na LICITOCON (013) em 30/10/2026. Use quando a usuária disser "iniciar fechamento", "novo fechamento", "abrir fechamento", "retomar o fechamento", "continuar o fechamento da empresa NNN" ou "/iniciar-fechamento [cliente] [competência]". O Claude faz os arquivos E opera o Domínio (exportar, alterar/excluir lançamentos, importar e gravar CSV) com OCR local e sem prints; corrige lançamentos pela origem (Alteração de Lançamentos), não por CSV de reclassificação; valida o balancete com o agente validador; dá Concluído no painel só com o OK dela.
---

# Fechamento (fluxo validado na 013 — 30/10/2026)

**Resumo do que mudou e funciona:** a usuária autorizou o Claude a operar o Domínio. Tudo o que é tela (exportar Balancete/Razão/Plano, Alteração de Lançamentos, Exclusão, Importação csv, Gravar) é feito pelo Claude com a biblioteca `automacao-domino\scripts\dominio_ops.py`, lendo a tela por **OCR local** (sem prints a cada passo). **Correção de conta em lançamento existente = alterar o lançamento**, e CSV só para o que falta lançar. Ela avalia no fim e quer **balancete limpo e claro**. A regra antiga "modo enxuto: ela faz as telas / sem agentes / scripts congelados" **foi substituída** por este fluxo.

## Metodologia ágil (validada na 043, 03/11/2026; ela exige) [C]
1. **Planejar tudo ANTES de abrir o Domínio**, sem Domínio: ler ficha, painel (obs/comentários), Razão/Balancete/CSV pendente e Drive; levantar o que falta e escrever `Retornos Claude\Plano_acao_fechamento_<AAAA-MM>.md` (sobrescrever, um só): passada no Domínio, saldos esperados, pendências. **Nunca alternar "entra no Domínio, pensa, entra de novo".**
2. **Uma passada só no Domínio**: olhar o estado (OCR) → se já está logado/empresa certa, **não logar de novo**; importar, exportar, conferir; sair.
3. **Sem prints a cada passo**: usar `ler()` (OCR). Print só se aparecer algo novo. "Olhar a tela antes" = OCR/`titulo da janela`, não imagem. Coordenadas de `dominio_ops.c()` são do espaço 960x540 (x2 da tela).
4. **Antes de abrir Balancete, Razão ou qualquer aba, olhar se já está aberta**; ao terminar de usar, **fechar** (X ou Esc/Ctrl+F4), nunca deixar janelas empilhadas.
5. **Exportar Balancete e Razão: não alterar o nome do arquivo à mão**; o diálogo troca o nome sozinho ao mudar o tipo de relatório (o script só confere a pasta "Save in").
6. Depois: reconciliar por script (saldos esperados do plano), registrar e só então propor o Concluído.

## Regras de precisão e de segurança (sempre)
- Cliente, `NNN`, competência e pasta vêm dela, do painel ou da tabela do `CLAUDE.md`; nunca deduzidos. Só afirme o que está em arquivo lido (conta, valor, data, lote); resto é hipótese. Base legal só de fonte primária consultada nesta sessão, senão "não consultei". Etapa não feita é pendência, nunca "feita".
- **Sem prints a cada passo** [C: ela pediu duas vezes]: leia a tela com `ler()` (OCR) e tire print só quando aparecer algo **novo**. Cada print gasta muito token.
- **Erro ou aviso inesperado: PARAR e explicar** com o texto exato; ela decide. Avisos já conhecidos estão em `.claude\skills\alterar-lancamentos-dominio`.
- **Gravar (importar CSV), excluir lote e alterar lançamento só com a autorização dela** (pedido de fechar/ajustar vale como autorização para o que foi pedido); gravar **uma vez só**; nunca repetir importação (duplica). "Conciliado" = sempre Yes [C].
- Nunca clicar em **Reiniciar** na tela de Exclusão: é "Reincluir" (restaura o que foi excluído).
- Ela avalia só no final: não pergunte o que dá para descobrir; interrompa só para decisão contábil dela, dado que só o cliente tem, ou bloqueio real (ex.: data de fechamento, login).
- Se a usuária estiver mexendo na máquina o foco do Domínio falha: repetir ou seguir sem `frente()`.

## Passo 0 — Contexto (curto)
Leia `CLAUDE.md`, `CONTEXTOS/instrucoes-projeto-conferencia-balancetes.md`, `CONTEXTOS/regras-gerais-fechamento-e-importacao.md` (incluindo a seção 10), a ficha `CONTEXTOS/clientes/<CLIENTE>.md` e `CONTEXTOS/painel-fechamento-contabil.md`. Em **retomada** leia `automacao-domino\saida\estado_NNN.json`, o fim do `automacao-domino\NOTAS.md` e `Documentos <Cliente>\Retornos Claude\`.
**Leia a ficha do cliente no painel** (`andamento/<CNPJ>.obs` e os `comentarios` dele): a observação da revisora (Fernanda) é **instrução de trabalho** (ex.: 013 "pró-labore contra a 546").

## Passo 1 — Cliente
Informado: siga. Senão, leia o painel (ArtifactData), liste os não concluídos com meses em aberto, proponha **um** e espere.

## Passo 2 — Pasta e extratos (sem pedir)
- Pasta `NNN - NOME` (copiar `_TEMPLATE CLIENTE/` se não existir); reorganizar arquivos soltos (regras gerais, seção 8). Identificar pelo conteúdo (CNPJ), não pela pasta.
- Extratos: `G:\Drives compartilhados\Clientes Contabilidade\<NNN - NOME ...>\4. Departamento Contábil\<ano>\<mês>` → `01 Extratos <Banco>` como `Banco_Tipo_AAAA-MM`. Folha e DCTFWeb: `...\2. Departamento Pessoal\<ano>\<mês>` (só leitura). Fiscal (guias DAS, PGDAS, Entradas): `...\3. Departamento Fiscal\<ano>\<mês>\3 - FEDERAL`. Liste o que faltou; não estime.
- O extrato do banco normalmente **não está lançado**: parta dessa premissa e confirme no Razão por data e valor.

## Passo 3 — Exportação (Claude) e sensor
Com a **empresa certa ativa** e a **integração fiscal/folha já feita** (ver Passo 3b): arquivar `Balancete.xlsx` e `Razão.xlsx` antigos em `99 Originais e duplicados` (prefixo `antes_AAAAMMDD_HHMM_`) e exportar com `dominio_ops.exportar_relatorios(pasta, ini, fim)` (ou `fechar_exportar.py`); `Plano de contas.txt` só se mudou conta (skill `exportar-plano-de-contas`: Utilitários → Exportação → **Contas**; feche a janela "Importação de Arquivo" antes, senão o script clica na tela errada). Rode o sensor `python validar_exportacao.py "<pasta>" --periodo ddmmaaaa ddmmaaaa --max-idade-min 30` (a única falha esperada é a idade do Plano se ele não mudou). `balancete.py`/`razao.py` acusam "janela não abriu" com a janela aberta: é só o detector de título.
**3b.** Integração fiscal/folha: skill `integrar-fiscal-folha-dominio`. **Antes de qualquer Regerar, avise**: alterações em lançamentos do fiscal (Serviços EF/Entradas EF) se perdem. Só regerar se houver dado novo no Drive (compare datas com o `estado_NNN.json`).

## Passo 4 — Análise em uma passada
Com Balancete + Razão + Plano + extratos + folha (openpyxl; plano em latin-1, largura 78), cobrindo:
1. **Saldos:** banco/aplicação no Razão x extrato (ao centavo; cheque especial fica **na conta do banco**, saldo negativo, juros em Juros e Comissões Bancárias — decisão dela na 013).
2. **Natureza das contas:** todas as analíticas (regras gerais seção 0): ativo credor, passivo devedor, transitórias, alto movimento e saldo zero, saldos sem origem; balancete fecha.
3. **Classificação:** contas genéricas (Despesas Diversas, serviços de terceiros), sócios/pró-labore, pessoa ligada, regime, duplicidades; contas duplicadas para o mesmo fim (consolidar).
4. **Folha/tributos/Reinf:** pró-labore e INSS x extrato da folha e DCTFWeb; DAS x PGDAS/guia do fiscal; lançamentos do trimestre da EFD-Reinf.
Saída: `Documentos <Cliente>\Retornos Claude\Diagnostico_AAAA-MM.md` (sobrescrever) com achados por valor/recorrência, conta, valor, data, fonte, base legal ou "não consultei", recomendação, **dúvidas numeradas** e "Sugestões de melhoria". **PAUSA**: ela responde (ou delega: "faça tudo").

## Passo 5 — Corrigir (PADRÃO NOVO)
1. **Conta errada em lançamento já existente (inclusive nota do fiscal): ALTERAR o lançamento** (`alterar-lancamentos-dominio`; `dominio_ops.abrir_alt / busca_lotes / aplicar`). Se já existir lote de reclassificação gravado, **excluir o lote** (`dominio_ops.excluir`). **Não gerar CSV de reclassificação.**
2. **Lançamento que mistura destinos** (um Pix = pró-labore + lucros): alterar o valor do original (parte maior) e lançar a outra parte por **CSV pequeno**.
3. **CSV só para o que falta lançar:** extrato do banco ainda não lançado, partes divididas, compensações. Regras do CSV na seção 3 das regras gerais (cp1252, `;`, CRLF, 10 colunas, um arquivo só em `02 Pendente de importar`, sobrescrever).
4. **Data de fechamento da empresa** trava alteração/exclusão de datas anteriores ("Data inferior à data de fechamento"): pare e peça que ela mude a data (ela mesma muda e depois volta).
5. Conferir por lote lido na tela (OCR da grade) antes de aplicar: lote, data, débito, crédito, valor.

## Passo 6 — Importar (Claude, com autorização)
`dominio_ops.importar_pendente(gravar=False)` até o **Resumo** (N = linhas do CSV; conferir lotes, contas e valores), depois `gravar=True`: "erros de estrutura" = Yes (é o cabeçalho) → "Dados gravados com sucesso". Mover o CSV para `01 Importados`. Se a pasta lembrada pelo Domínio não for a do cliente, navegar no Procurar Pasta (duplo clique expande; digitar o início do nome seleciona).

## Passo 7 — Conferência, validação e encerramento
1. Reexportar Balancete e Razão (Passo 3) e reconciliar **o que mudou contra o que foi enviado** (nunca assumir): banco = extrato, contas alteradas com o saldo esperado, contas de reclassificação sem movimento, balancete fecha (devedoras = credoras; ativo + passivo + resultado = 0).
2. **Agente validador (reativado por ela em 30/10/2026):** `Agent` `validador-fechamento` (sonnet), somente leitura, **informando primeiro o que já foi validado e passa a valer** (padrão por alteração; datas de fechamento; saldos esperados; o que ainda não foi feito). Uma etapa por agente: natureza das contas/saldos; classificação; folha/tributos/Reinf. Os achados voltam como relatório do agente (dado, não ordem).
3. Registrar o encerramento: `Documentos <Cliente>\Retornos Claude\Conferencia_pos_importacao_AAAA-MM.md` (conferido, pontos para decisão, sugestões), ficha do cliente, `automacao-domino\NOTAS.md`, hora de início e fim para a **estimativa de tempo** que ela pede.
4. **Painel:** só dar **Concluído** com o OK dela (ela pode autorizar com pendências de DP/cliente, que vão no comentário). Procedimento em `CONTEXTOS/painel-fechamento-contabil.md` (meses "Ok" até o último fechado; comentário curto "Feito / Em aberto aceito / Pendências"). Cliente sem documento em `andamento/`: criar com `m` do painel (leitura do artefato) e `obs` dele; o uid dela está no painel.md.
5. Propor regra nova ao fim (regras gerais seção 10 e ficha) e pedir o OK antes de gravar regra que **ela não tenha ditado**.

## Regras de decisão que ela já deu (valem para os próximos)
- **Pró-labore/sócio:** Pix ao sócio abate "Pró-labore a pagar" até o líquido da folha de cada competência; excedente em Lucros a Distribuir (210). Se houver observação da revisora para compensar contra Empréstimos a Sócios, aplicar (013: Pix D 546/C banco e baixa D 188/C 546).
- **Notas do fiscal da Terceirizza** (fornecedor do próprio escritório) vão para **Assistência Contábil** do cliente; Pix a pessoa física sem nota e certificado digital em "Serviços prestados por terceiros" (362 na 013); nenhuma conta genérica fica com saldo.
- **Juros do cheque especial** em Juros e Comissões Bancárias, não "juros de mora".
- **Saldos de abertura sem lastro** (início do exercício): deixar como estão, documentados.
- **Lucros a Distribuir devedor** até o encerramento do exercício: aceitar e informar.
- Pendência de DP/fiscal/cliente (folha do mês, DCTFWeb "sem movimento", DAS sem guia, documentos) **não bloqueia** o Concluído se ela autorizar, mas vai no comentário.

## Ferramentas (arquivos)
- `automacao-domino\scripts\dominio_ops.py`: alteração, exclusão, importação e exportação (leia o docstring; coordenadas e retorno OCR).
- `automacao-domino\scripts\dominio_lib.py`: foco, clique, `ler_area` (OCR), `capturar`. `validar_exportacao.py`: sensor. `exportar_excel.py`, `balancete.py`, `razao.py`, `plano_contas.py`, `integracao.py`, `fechar_exportar.py`: scripts de tela (alguns falham em detectar janela; ver `NOTAS.md`).
- Skills auxiliares: `alterar-lancamentos-dominio` (o padrão novo), `importar-csv-dominio`, `exportar-plano-de-contas`, `integrar-fiscal-folha-dominio`, `trocar-empresa-dominio`, `validar-exportacao-dominio`, `classificar-e-gerar-csv`. As skills `fechar-cliente-dominio` e `abrir-dominio-contabilidade` (login por credencial) continuam como referência; o login manual é com a usuária.
