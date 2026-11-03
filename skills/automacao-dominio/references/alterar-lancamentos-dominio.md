---
name: alterar-lancamentos-dominio
description: Corrige conta, valor, data ou histórico de lançamentos JÁ GRAVADOS no Domínio Contabilidade pela tela Alteração de Lançamentos (e exclui lotes pela tela Exclusão), em vez de importar CSV de reclassificação. Padrão validado na LICITOCON (013) em 30/10/2026. Use sempre que um fechamento precisar mudar a conta de um lançamento, dividir um lançamento, trocar a conta de nota do fiscal, remover um lote de reclassificação ou limpar o balancete.
---

# Alterar e excluir lançamentos no Domínio (padrão validado — 013, 30/10/2026)

**Regra dela [C]:** para deixar o balancete limpo, conta errada em lançamento existente se corrige **alterando o lançamento**; reclassificação por CSV deixa pares de lançamentos sujando o Razão. CSV só para o que **falta** lançar. Ferramenta: `automacao-domino\scripts\dominio_ops.py` (`abrir_alt`, `busca_lotes`, `busca_conta`, `aplicar`, `fechar_alt`, `excluir`). **Sem prints a cada passo** (ler com OCR `ler()`); erro ou aviso novo: parar e explicar.

## 1. Achar o lançamento
- Menu **Utilitários → Alteração de Lançamentos** (ou **Favoritos → Alteração de lançamentos**). A janela mostra uma grade (Lote, SCP, Número, Data, Tipo, Debitar, Creditar, Valor) e botões Todos, Nenhum, Inverter, **Busca avançada**, Buscar, Alterar...
- **Busca avançada:** colunas da lista = Lote, SCP, Número, Data, Tipo, Debitar, Creditar, Valor (escolher com a lista aberta + `Down` N vezes + Enter). Condição: Igual a, Diferente de, Entre, Maior e igual a, Maior que, Menor e igual a, Menor que. Operador entre linhas: **E** / **Ou**.
- **Lote com 5 dígitos** (`03042`; `3042` não achou). **O OK da busca já pesquisa — não clicar em Buscar depois** (limpa a lista). Depois de uma pesquisa o botão Busca avançada fica desabilitado: feche a janela (X) e reabra para a próxima.
- **Vários lotes (até 5 por busca):** Adicionar cria a linha; **crie todas as linhas primeiro e só depois preencha o Operador "Ou"** das de cima (preencher antes dá "Você precisa informar o campo Operador").
- Busca por conta: `Debitar = 5 E Data >= 01/04/2026` (sem a data traz todos os anos). Data: clique na célula, `Home`, digitar `01042026`.
- **Confira a linha lida** (lote, data, débito, crédito, valor) antes de aplicar. Tipos que aparecem: Extrato Bancário (importado), Normal, Serviços EF / Entradas EF (integração do fiscal), Zeramento.

## 2. Alterar
`Todos` (marca as linhas da grade) → `Alterar...` → "Somente os lançamentos selecionados" → marcar **só** o que muda: Data, **Valor**, **Conta débito**, **Conta crédito**, SCP, Filial, centros, Histórico → digitar o código (o sistema mostra o nome da conta: **confira**) → `Alterar`.
Diálogos, nesta ordem: "Você tem certeza que deseja alterar o lançamento selecionado?" → **Yes**; "Este lançamento já está conciliado. Deseja continuar?" → **Yes** (regra dela: sempre sim; pode repetir uma vez por lançamento); "Lançamentos alterados com sucesso." → OK → Fechar.
- **Dividir um lançamento** (ex.: um Pix de 12.000,00 = 10.557,31 lucros + 1.442,69 pró-labore): alterar o **Valor** do original (parte maior) junto com a conta; a outra parte entra por CSV pequeno na mesma data.
- Alterar o par só serve quando o par continua válido. Lançamento D banco / C conta transitória (ex.: reclass do cheque especial) **não se altera: exclui-se**.

## 3. Excluir lote
**Utilitários → Exclusão → Lançamentos** (não "Lançamentos Simples"). Filtros: Data (inicial/final), Lote (inicial/final, 5 dígitos), Apenas com conta débito/crédito, origem, tipo, valor, usuário. Conferir o filtro (um print da região) na primeira vez → OK → "Confirma exclusão dos lançamentos?" → Yes → "Excluídos: N" (**N tem de bater com o que você levantou no Razão**) → OK → Fechar.
- Para sumir com todos os lotes de reclassificação de uma conta: `Data 01/04 a 30/09 + Apenas com conta crédito = <conta>` (ex.: crédito 5 = 26 lotes; crédito 817 = 16 lotes). Levante antes no Razão que **todo** crédito dessa conta no período é reclassificação.
- **NUNCA clicar em "Reiniciar"** (é "Reincluir": "Deseja re-incluir lançamentos excluídos?" → responder **No**).
- **"Data inferior à data de fechamento" / "Exclusão cancelada"**: o lançamento é anterior à data de fechamento da empresa (trava de período). Pare e peça que ela mude a data (ela mesma muda, e depois volta). Nada é excluído nesse caso.

## 4. Depois
Reexportar Balancete e Razão e reconciliar (conta alterada com o saldo esperado; conta de reclassificação sem movimento; balancete fecha). Se um CSV pendente repetia o que foi alterado, tire a linha dele ou mova-o para `03 Substituidos (nao importar)`.

## 5. Cuidados
- **Lançamentos do fiscal** (Serviços EF / Entradas EF) alterados **voltam ao original se o fiscal for regerado**: avisar a usuária antes de qualquer "Regerar lançamentos contábeis".
- Alterar lançamento que o ECD/ECF já entregue cobre (ano anterior): não mexer; ajuste vai no exercício atual (regras gerais, seção 7).
- Coordenadas (print 960x540, tela 1920x1080; valem para a janela como estava em 30/10/2026): menu Utilitários (309,33); Alteração (343,157); Exclusão (318,389) → Lançamentos (563,405); Busca avançada (713,457); lista Coluna (360,253); Valor (490,253); OK da busca (643,297); Todos (421,457); Alterar... (647,457); checkbox Conta débito (313,257), campo (417,257); Valor (313,242)/(417,242); botão Alterar (597,389); Yes certeza (506,302), Yes conciliado (481,302), OK sucesso (537,302); Fechar o diálogo (645,389); fechar a janela (808,230). Exclusão: Lote (461,139) e campos (527,153)/(527,168); Data (323,139) e campos (365,153)/(365,168); crédito (323,342)/(385,356); OK (633,133); Yes (484,302); Fechar (633,153). Se algo abrir fora do lugar, um print resolve e a coordenada se atualiza em `dominio_ops.py`.
