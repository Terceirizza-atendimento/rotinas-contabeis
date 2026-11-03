---
name: importar-csv-dominio
description: Importa o CSV de lançamentos do cliente no Domínio Contabilidade (Favoritos → Importação csv) por importar_csv.py, com ensaio sem gravar e Gravar uma única vez. Use quando a usuária mandar importar o CSV de "02 Pendente de importar" ou o extrato do banco de um fechamento.
---

# Importar CSV no Domínio

Script: `automacao-domino\scripts\importar_csv.py` (rode dentro de `automacao-domino\scripts`, sem `-I`). POP completo, handoff e fluxo de 19 passos: `automacao-domino\automacao-importacao-csv.md`. **Leia o handoff antes de rodar**: ele diz onde a última tentativa parou.

```
python importar_csv.py "<pasta do cliente>"            # ensaio: lê até o Resumo e responde No; nada grava
python importar_csv.py "<pasta do cliente>" --gravar   # grava UMA vez
```
Pré-requisitos: Contabilidade aberta, **empresa certa ativa** (skill `trocar-empresa-dominio`; confira nome e CNPJ na aba Geral da janela), **um único CSV** em `<pasta>\Arquivos de importação\02 Pendente de importar`, e exclusões de lançamentos errados já feitas.

## Ordem
1. Ensaio (sem `--gravar`). Confira o **Resumo dos Dados**: quantidade de lançamentos e totais batem com o CSV (reabra o CSV e some).
2. **Gravar só com a ordem expressa da usuária** (grava lançamentos; repetir duplica). O estado em `saida\estado_NNN.json` bloqueia repetir pelo `fechar.py`; rodando o script direto, **você** é a trava: nunca rode `--gravar` duas vezes.
3. O aviso de "erros de estrutura" é sempre o cabeçalho do CSV (linha 00001): confirmar Yes é normal. Sucesso = "Dados gravados com sucesso!".
4. Depois: mover o CSV para `01 Importados` (confira), reexportar Balancete/Razão/Plano e rodar o sensor (`fechar_exportar.py` ou `fechar.py --de conferir`). Reconciliar o que entrou contra o que foi enviado; nunca assumir.

## Regras
- Janela "Importação de Arquivo": Tipo **TXT**, Conjunto de dados "Lançamentos Contábeis (Partida Simples/Múltiplas) (3.1) (2) (Excel (3.1) (2))"; manter "Importar somente registros inexistentes". A "Seleção de arquivos" abre com filtro `*.txt`: trocar para **Todos os arquivos (*.*)**.
- **Caminho nunca é digitado** (truncou/corrompeu em 30/10/2026): navega-se por clique na árvore (Client C (M:) → Users → atend → OneDrive → Documentos → ROTINAS CONTÁBIL → IMPORTAÇÃO DOMINIO → cliente → Arquivos de importação → 02 Pendente de importar).
- **Estado do script**: `importar_csv.py` falhou ao vivo em 30/10/2026 no "Procurar Pasta" ("não achei 'atend'"). **Use `dominio_ops.importar_pendente()`** (o Domínio lembra a pasta; se não lembrar, a navegação manual validada está na seção "Navegação manual validada" abaixo). Correção de conta em lançamento existente **não é por CSV**: ver skill `alterar-lancamentos-dominio`. Histórico do script antigo: Se o ensaio falhar achando "Arquivos de importação"/"02 Pendente" por OCR, o ajuste está descrito no POP (separar a navegação em duas etapas). Falhou duas vezes: pare e relate as últimas linhas; não improvise cliques.
- Avisos do Google Drive ("arquivos removidos de pasta compartilhada") podem cobrir Gravar/Cancelar: o script clica o OK do toast; se reaparecer, avise a usuária. O Domínio fecha sozinho com o tempo parado.
- Esc na tela de Resumo abre "Deseja gravar os dados?": responda **No**, nunca Yes fora do `--gravar`.


## Diálogo "Selecione o arquivo" (EXPORTAR) x importação do CSV: não confundir [regra da usuária, 30/10/2026]
- Ao **exportar** Balancete/Razão para Excel, o diálogo abre na pasta do cliente (confira o "Save in"). No campo **File name digite SÓ o nome** (`Razão.xlsx`), **nunca o caminho completo** (dá "file name is not valid" / caminho truncado). `exportar_excel.py` já faz isso e confere o "Save in" por OCR; se não bater, navegue por clique até a pasta do cliente.
- O caminho/pasta do diálogo de **importação do CSV** é outra coisa: lá a pasta se escolhe por clique na árvore (nunca digitada). Um fluxo não se mistura com o outro.
- Se o diálogo "Selecione o arquivo" já estiver aberto, `exportar_excel.py` não clica no ícone Excel de novo; só preenche o nome e salva.
- Se `balancete.py`/`razao.py` falharem com "janela ... não abriu" mas a captura `saida\erro_menu.png` mostrar a janela aberta, é só o detector de título: clique OK na janela e rode `exportar_excel.py`.

## Navegação manual validada ao vivo (30/10/2026, empresa 013, 98 lançamentos gravados) [usuária aprovou]
Se o ensaio do script falhar no "Procurar Pasta" (ex.: "não achei 'atend'"), faça à mão com `dominio_lib` (`achar_titulo("Procurar Pasta")`, `foco`, `pyautogui`; tela 1920x1080, o print reduzido a 960x540 tem coordenadas x2):
- **Duplo clique** na pasta expande a árvore (seta direita e Enter **não** expandem).
- **Digitar o começo do nome** seleciona a pasta (Users, atend, OneDrive, Documentos, ROTINAS, IMPORTA, 013, Arquivos, 02); depois duplo clique na linha selecionada para expandir e digitar o próximo nível. Em "02 Pendente de importar", **OK** (só selecionar, não expandir).
- Aviso "Não existem arquivos TXT" → OK. Tipo → **Todos os arquivos (*.*)** (só o CSV pendente deve aparecer, marcado) → OK → **Importar** (~20 s) → tela **Resumo dos Dados**: conferir "Lançamentos contábeis (N)" = linhas do CSV.
- **Gravar** → aviso "Existem erros de estrutura... Confirma a gravação" → **Yes** (normal, é o cabeçalho) → "Dados gravados com sucesso! N registro(s) importado(s)" → OK. Gravar só com ordem expressa, uma vez.
- **Economia de tokens [C: usuária]:** pode usar Enter, setas e teclado à vontade; **não tirar print a cada passo**, só nos pontos de decisão (Procurar Pasta aberto, Resumo, aviso de gravação).
- Depois: mover o CSV para `01 Importados`, reexportar Balancete/Razão/Plano e reconciliar.

## PADRÃO: corrigir lançamento ERRADO alterando-o no Domínio, não por CSV de reclassificação [C: usuária, 30/10/2026; validado ao vivo na 013, lote 3042]
Para deixar o balancete limpo, **conta errada em lançamento já existente se corrige na origem** (Utilitários → Alteração de Lançamentos), sem lote de reclassificação (que deixa o par de lançamentos sujando o Razão). CSV só para o que **falta** lançar.
1. Utilitários → **Alteração de Lançamentos** → **Busca avançada** → Coluna (lista: Lote, SCP, Número, Data, Tipo...) = **Lote**, Condição "Igual a", Valor com **5 dígitos** (`03042`; `3042` não achou) → **OK**. O OK da busca já pesquisa: **não clicar em Buscar depois** (limpa a lista).
2. Conferir a linha (lote, data, débito, crédito, valor) → **Todos** → **Alterar...** → "Somente os lançamentos selecionados" → marcar só o campo a mudar (Conta débito / Conta crédito / Data / Valor / Histórico) e digitar o código (o sistema mostra o nome da conta: conferir) → **Alterar**.
3. "Tem certeza que deseja alterar o lançamento selecionado?" → **Yes**. Se o lançamento for conciliado, aparece "Este lançamento já está conciliado. Deseja continuar?" → **Yes** (usuária: "sempre sim") → "Lançamentos alterados com sucesso." → OK → Fechar.
4. Se der qualquer outro erro/aviso diferente: **parar e explicar à usuária** antes de seguir.
5. Se já existir um CSV pendente ou lote de reclassificação gravado para o mesmo lançamento, tirar do CSV / excluir o lote para não duplicar.
Coordenadas (print 960x540, x2 na tela): menu Utilitários (309,33) → Alteração de Lançamentos (343,157); Busca avançada (713,457); dropdown Coluna (360,253), "Lote" (307,264); Valor (490,253); OK da busca (643,297); Todos (421,457); Alterar... (647,457); checkbox Conta débito (313,257) e campo (417,257); Alterar (597,389); Yes (506,302 / 481,302). Pode variar com a janela: conferir por print nos pontos de decisão.

### Complemento do PADRÃO (013, 30/10/2026) — exclusão, datas travadas, vários lotes, sem prints
- **Vários lotes/critérios:** na Busca avançada, depois da 1ª linha, **Adicionar** abre outra linha; preencher Coluna (teclado: abrir a lista e `Down` N vezes + Enter; ordem: Lote, SCP, Número, Data, Tipo, **Debitar**=6 Down, **Creditar**=7 Down, Valor…), Condição (Igual a, Diferente de, Entre, Maior e igual a, Maior que…) e **Operador E/Ou na linha de cima**. Ex.: `Debitar = 5 E Data >= 01/04/2026`. Data no valor: clicar na célula, `Home`, digitar `01042026`. Sem Adicionar a busca por conta traz todos os anos (veio 2022).
- **A janela "Alteração de Lançamentos" fica aberta**: depois de uma pesquisa o botão Busca avançada fica desabilitado; para nova pesquisa fechar no X e reabrir pelo menu.
- **Excluir lote:** Utilitários → Exclusão → **Lançamentos** (não "Lançamentos Simples"); marcar Lote Inicial/Final (5 dígitos) ou Data + "Apenas com conta crédito/débito"; OK → "Confirma exclusão?" Yes → "Excluídos: N". **NUNCA clicar em "Reiniciar": é "Reincluir" ("Deseja re-incluir lançamentos excluídos?"); se aparecer, responder No.** Data inicial: clicar no segmento do dia, Home, digitar `01042026`.
- **Data de fechamento:** lançamento anterior à data de fechamento da empresa não pode ser excluído/alterado ("Data inferior à data de fechamento. Exclusão cancelada"): parar e pedir à usuária para mudar a data de fechamento (ela mesma muda e depois volta).
- **Mudar o par de um lançamento só serve quando o par continua válido**: lançamento D banco/C 830 não se "altera", se exclui.
- **Alterações de lançamentos de integração (Tipo "Serviços EF") ficam perdidas se o fiscal for regerado**: avisar a usuária antes de qualquer Regerar.
- **Sem prints**: ler a tela por OCR local (`dominio_lib.ler_area`) nos pontos de decisão (linha da grade, texto dos diálogos); print só quando aparecer algo novo [C: usuária, 30/10/2026].
- Resultado 013: Banco 5.162,86 = extrato; Caixa 5 zerado de movimento; 374 com 2.651,78; balancete fecha.

### Vários lotes de uma vez (013, 30/10/2026)
- Busca avançada com N lotes: criar **todas** as linhas primeiro (Adicionar, coluna Lote, valor com 5 dígitos) e **só depois** preencher o Operador "Ou" da linha de cima (preencher antes dá "Você precisa informar o campo Operador"). Limite prático: ~5 linhas visíveis; usar grupos de até 5 lotes.
- **Dividir um lançamento** (um Pix = pró-labore + lucros): na Alteração marcar **Valor** (parte maior) + **Conta débito**; a parte restante entra por CSV pequeno (D 188/C 8). Conferir o valor lendo o campo antes de Alterar.
- Atalhos do menu **Favoritos**: "Alteração de lançamentos" e "Importação csv" (a Importação lembra a pasta da última vez e já lista o CSV de `02 Pendente de importar`: OK, Importar, Gravar). Se o foco do Domínio falhar (usuária mexendo na máquina), repetir o clique.
- Notas do fiscal (Entradas EF) na conta errada se corrigem pela Alteração (ex.: Terceirizza -> 361 Assistência Contábil, por decisão dela).
