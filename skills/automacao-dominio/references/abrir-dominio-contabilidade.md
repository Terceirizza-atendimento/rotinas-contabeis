---
name: abrir-dominio-contabilidade
description: Abre e opera o Domínio Contabilidade (Thomson Reuters) no computador da Terceirizza por scripts Python: login no Domínio Web, Lista de Programas, Contabilidade, login do sistema (LETICIA), gerar Balancete e Razão pelo menu Favoritos e exportar para Excel (.xlsx) na pasta do cliente. Use SEMPRE que o usuário pedir para "abrir a Domínio", "logar na Contabilidade", "gerar/exportar o balancete ou o razão", "baixar balancete em Excel", ou qualquer tarefa que dependa do Domínio Contabilidade aberto e logado. Cobre também as armadilhas de controle de tela do Windows e da janela remota.
---

# Domínio Contabilidade por scripts

**O processo completo funciona e já foi validado ao vivo, com gravação real** (fechamento da LICITOCON/013 em 30/10/2026: login → sistema aberto → integração fiscal+folha gravada → Balancete/Razão exportados → lançamentos alterados/excluídos → CSV importado e gravado — 98 lançamentos; e o fechamento da 075/043 no mesmo período). Os avisos "[NÃO TESTADO]" abaixo são sobre **scripts de atalho específicos** que tentam encadear vários passos num comando só sem parar (`fechar.py`, `fechar_exportar.py` de ponta a ponta, `trocar_empresa.py`) — esses ainda pedem conferência passo a passo; não significam que a automação em si não funcione.

Os scripts ficam em `C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\automacao-domino\scripts` (pasta única da automação; ver `automacao-domino\LEIAME.md`). **Rode sempre pelos scripts**: eles levam poucos segundos e gastam poucos tokens. Só use captura de tela e coordenadas na mão quando um script falhar. Coordenadas, descobertas e histórico: `automacao-domino\NOTAS.md` (mesma pasta, um nível acima de `scripts`); capturas e estado em `automacao-domino\saida`. `python listar_scripts.py` mostra o uso atual de cada script.

Só funciona no Windows do usuário (atend), tela 1920x1080, com permissão para Bash/PowerShell. Dados de clientes são confidenciais: nada sai para serviços externos.

## Regras de precisão (valem para toda a skill)

1. **Só afirme o que a saída do script, o arquivo em disco ou a captura de tela mostrou.** "Exportei" só vale com: arquivo existe na raiz da pasta do cliente **e** sensor `APROVADO`. Script que terminou sem erro não prova que a tela fez o que deveria.
2. **Empresa, CNPJ, competência, período e pasta nunca são presumidos.** Se o usuário não informou, pergunte. Não deduza pelo último cliente usado, pela barra superior do sistema ou por arquivos antigos na pasta.
3. **Coordenadas, menus e botões só os escritos aqui ou no `NOTAS.md`.** Se a tela não bater com a descrição, **pare e relate o que viu**; não procure o botão por tentativa e erro.
4. Cada procedimento abaixo é rotulado **[TESTADO]** (com data) ou **[NÃO TESTADO]**. Antes de rodar algo [NÃO TESTADO], avise a usuária.
5. Nenhuma base legal ou regra contábil de memória: cite a fonte ou diga "não consultei".
6. O que não consta nesta skill nem no `NOTAS.md`: responda "não sei / não está documentado" e pergunte.

## Pré-requisitos

- Python com `playwright pywin32 pyautogui psutil` (`python -m pip install playwright pywin32 pyautogui psutil`).
- Rodar **dentro da pasta dos scripts**, com `python arquivo.py` e **sem `-I`** (senão não acha `dominio_lib.py`).
- **Credenciais só por variável de ambiente, nunca em arquivo**: pergunte ao usuário se não estiverem na conversa.
  - Portal Thomson Reuters: `DW_USER` (terceirizzacontabil@gmail.com) e `DW_PASS`.
  - Sistema (diálogo "Conectando ..."): `DW_SYS_USER` (LETICIA) e `DW_SYS_PASS`.

## Fluxo (ordem)

0. **O diálogo "Conectando ..." às vezes vem preenchido com usuário/senha errados e abre em posição diferente**: os scripts apagam os dois campos (End + Backspace) antes de digitar e usam coordenadas relativas ao canto do diálogo.
1. **`login_portal.py`** (Bash com `run_in_background: true`): Playwright em perfil persistente `C:\Users\atend\.dominio-pw-p1`; a sessão costuma ficar válida e ir direto a `/success`. Mantém o navegador aberto 25 min. Isso dispara o AppController, que abre a Lista de Programas.
2. **`abrir_contabilidade.py`**: espera a Lista de Programas, clica Contabilidade + Enter, espera "Conectando ...", digita usuário e senha, OK e espera o sistema abrir (~10 s; a primeira vez após o login do portal pode levar ~45 s). Termina com a janela principal maximizada.
2b. **Condicional: integração do fiscal e da folha no contábil** (seção abaixo). Só se ainda não estiverem integrados para a competência. Script: `integracao.py <MMAAAA>` ou `<MMAAAA-MMAAAA>` (ex.: `102026`, `012026-092026`). **O script não clica Gravar nem os OK dos avisos** (ver seção abaixo).
3. **`balancete.py [ddmmaaaa ddmmaaaa]`**: Favoritos → Balancete → datas → OK. **Sem argumentos o script DIGITA 01/01/2026 a 30/09/2026** (valores fixos no código; ele não "mantém o período lembrado"). **Sempre passe as duas datas da competência pedida.**
4. **`exportar_excel.py "<pasta do cliente>" ["Balancete.xlsx"]`**: ícone Excel → tipo `*.xlsx` → Save; se o arquivo existir, clica Yes em "já existe"; confere o arquivo no disco (até 30 s).
5. **`razao.py [ddmmaaaa ddmmaaaa]`**: Favoritos → Razão → OK. **Sem argumentos NÃO digita datas: usa o período que o Razão lembrou da última vez** (pode ser de outro cliente/mês). Com argumentos digita as datas certas (já usado em produção com competências diferentes de cliente para cliente: 013 04-09/2026, 075 01-09/2026, 043 jan-set). Passe as datas sempre que souber a competência e confirme na captura `saida\razao_datas.png`.
6. **`exportar_excel.py "<pasta do cliente>" "Razão.xlsx"`**.

**Atalho: `fechar_exportar.py "<pasta do cliente>" [ddmmaaaa ddmmaaaa]`** (passos 3 a 6 + `plano_contas.py` + sensor, parando na primeira falha). Antes de exportar ele **move** `Balancete.xlsx`, `Razão.xlsx` e `Plano de contas.txt` existentes para `99 Originais e duplicados` com prefixo `antes_AAAAMMDD_HHMM_`. Se o sistema estiver fechado, abre sozinho (login_portal + abrir_contabilidade; precisa das variáveis de ambiente). Não importa CSV nem integra fiscal/folha. **Cada passo isolado já rodou de ponta a ponta e com gravação real (013, 30/10/2026); a cadeia inteira como UM comando só ainda não foi confirmada** — na 013 o encadeamento automático travou no meio (o bug de detecção de janela do Balancete/Razão foi corrigido em 03/11/2026 no `dominio_lib.py`, o que deve ter resolvido a causa mais provável, mas sem um novo teste ao vivo trate o atalho com cautela e confira a captura depois de cada passo). Sempre passe as duas datas: sem elas o `balancete.py` digita 01/01/2026–30/09/2026.

Tempos medidos (29/10/2026): balancete ~14 s, razão ~17 s, cada exportação ~13 s. A cadeia 3→6 rodou inteira sozinha, sem intervenção **[TESTADO]**.

## Pasta do cliente

As pastas seguem `NNN - NOME` dentro de `IMPORTAÇÃO DOMINIO` (ver `CLAUDE.md`). `Balancete.xlsx`, `Razão.xlsx` e `Plano de contas.txt` ficam na **raiz** da pasta do cliente. O diálogo "Selecione o arquivo" abre **na última pasta usada**, não necessariamente a do cliente ativo; no campo **File name digite SÓ o nome do arquivo** (`Razão.xlsx`), **nunca o caminho completo** (dá "file name is not valid"). O `exportar_excel.py` já lê o "Save in" por OCR, navega até a pasta do cliente e **aborta sem salvar** se não chegar lá; se mesmo assim ele falhar por "não foi gravado", **procure o arquivo em outra pasta de cliente e avise a usuária antes de apagar/mover qualquer coisa** (já aconteceu, ver `NOTAS.md`). Navegação manual e coordenadas do diálogo: `NOTAS.md` § "Diálogo 'Selecione o arquivo'". Depois de exportar, rode a skill sensor `validar-exportacao-dominio`.

O diálogo de **importação do CSV** é outro fluxo: ali a pasta se escolhe clicando na árvore (nunca digitada) — não confundir com o diálogo de exportar.

## Antes de exportar: integração do fiscal e da folha (condicional)

Use **só se o fiscal e a folha não estiverem integrados no contábil** para a competência (balancete/razão sem os lançamentos de entradas, saídas, serviços ou folha). **Sempre confira a competência a regerar** (a do fechamento em andamento) antes de qualquer botão — altera lançamentos contábeis.

**Script: `integracao.py <MMAAAA | MMAAAA-MMAAAA> [--fiscal] [--folha] [--simular]`** (ex.: `python integracao.py 102026` ou `012026-092026`). Navega entre os módulos pelo painel do logo DOMÍNIO, na mesma janela da Contabilidade, preenche a competência, marca Entradas/Saídas/Serviços e clica Gerar/Regerar; `--simular` faz tudo menos clicar Gerar/Regerar.

**O script NÃO clica Gravar, nem "Deseja gravar dados?", nem os OK dos avisos.** Sem o Gravar nada fica salvo. Por isso, rodar sem `--simular` **não conclui a integração**: feche cada janela e clique Gravar à mão, conferindo a captura. Quem executa (inclusive agente) **não relata "integrado"**; relata "Gerar/Regerar clicados, Gravar pendente" e para. Coordenadas exatas de cada botão (Gravar, OK dos avisos etc.): `NOTAS.md` § "Testado de verdade em 29/10/2026".

Roteiro (fiscal depois folha):
1. Painel de módulos → **Escrita Fiscal**.
2. **Movimentos → Integração Contábil**: conferir/ajustar Período Inicial/Final e **sempre clicar em Gerar...** (decisão da usuária).
3. **Utilitários → Regerar → Lançamentos Contábeis**: Período; marcar **Entradas, Saídas e Serviços**; **manter desmarcada** "Não regerar lançamentos alterados manualmente" (decisão da usuária); **Regerar**.
4. **Erro de débito e crédito** ao regerar: criar a conta do cliente/fornecedor em **Utilitários → Alterar Cadastro de Clientes e Fornecedores** (clientes = conta fechada; fornecedores = conta aberta) e regerar de novo.
5. Painel de módulos → **Folha** → **Processos → Integração Contábil**: competência e **Gerar...**.

Depois, voltar ao módulo Contabilidade e seguir com `balancete.py`/`exportar_excel.py`. Os sensores de arquivo não detectam falta de integração: se o balancete sair sem os lançamentos esperados, volte a esta seção.

## Favoritos de cada módulo

A usuária reorganizou o menu **Favoritos** (Contabilidade, Escrita Fiscal e Folha têm itens diferentes, inclusive atalhos para os processos de integração). Posições exatas (y de cada item): `NOTAS.md` § "Favoritos reorganizados". `balancete.py` e `razao.py` já usam as posições atuais; se um deles clicar no item errado, confira a captura antes de seguir.

## Importar CSV (extrato do banco e demais lançamentos)

Quando usar: **em todo fechamento**, depois de gerar o CSV (o extrato do banco quase nunca está lançado). **Script: `importar_csv.py [--gravar]`**. Sem `--gravar` é só ensaio (abre, seleciona o CSV, lê o Resumo e sai respondendo **No**; nada grava). Com `--gravar` clica Gravar, confirma o aviso de "erros de estrutura" (é só o cabeçalho do CSV) e dá OK. **Nunca rodar de novo depois de gravar (duplica).** **Confirme com a usuária antes de usar `--gravar`.** Conferir depois: no Resumo, o número de lançamentos e, no fim, "Dados gravados com sucesso".
Passo a passo manual e coordenadas (se o script falhar): `NOTAS.md` § "Importação de CSV". Regra fixa: a pasta do CSV se escolhe clicando na árvore em "Seleção de arquivos" (nunca digitando o caminho).

## Estado do sistema

- Empresa ativa: canto superior direito do sistema. Trocar clicando no nome ou **F8** (diálogo "Troca de empresas": busca por Código ou Apelido, botão Acessar). **Troca de empresa ainda não tem script**: hoje tudo roda na empresa que estiver ativa. O cabeçalho do relatório mostra a empresa real; a barra superior pode ficar desatualizada, confira o cabeçalho (nome e CNPJ) antes de exportar.
- O Balancete e o Razão lembram o último período usado. O `balancete.py` **sempre digita** as datas (as dos argumentos ou, sem argumentos, 01/01/2026 a 30/09/2026); o `razao.py` só digita se receber datas. Digitar datas diferentes do período lembrado já funcionou em produção (troca de cliente/competência na mesma sessão). Depois de gerar, confira o período no cabeçalho do relatório (captura ou sensor com `--periodo`); sem `--periodo` o sensor **não reprova** período errado.

## Armadilhas (resumo — detalhes técnicos/coordenadas em `NOTAS.md` § Descobertas)

- **Foco**: os scripts exigem a janela da Domínio em primeiro plano e abortam se não conseguirem (o IDE do usuário ou o mouse sobre a barra de tarefas atrapalham). Nunca digite "no escuro". Peça à usuária para não mexer na máquina durante a execução.
- **Digitação**: Ctrl+A não seleciona nos campos do Domínio (limpar com End + Backspace); colar não funciona; acentos só via `SendInput`.
- Um `login_portal.py` antigo segura o perfil do Chrome por 25 min: nova execução falha com "Abrindo em uma sessão de navegador existente". Encerre **só** o PID desse python (e filhos), nunca `Stop-Process` em massa.
- Não usar opções que escondem a automação do navegador (`--disable-blink-features=AutomationControlled` etc.). Fechar o Chrome do usuário exige autorização explícita.
- O sistema pode demorar a abrir e o identificador da janela principal pode mudar logo após o login: os scripts sempre reacham a janela, nunca guardam o handle.

## Depois de logado

Se o usuário só pediu para abrir, tire uma captura (`dominio_lib.capturar`), confirme o estado e **aguarde a instrução** antes de clicar em qualquer coisa dentro do sistema.

## Regras novas (29/10/2026) — usar SEMPRE
- **Comando único:** `python fechar_exportar.py "<pasta do cliente>" ddmmaaaa ddmmaaaa --empresa NN` (datas obrigatórias; NN = código da empresa, ex.: 43 Oxford Fortune).
- **Trocar de cliente:** `python trocar_empresa.py NN` (F8 + OCR; confere a barra). O script lê a tela cheia (1920x1080) por OCR, então não tem o bug de escala que travou a troca manual na 013 (aquele erro foi de leitura de coordenada em captura reduzida, não do script); mesmo assim **ainda não há um teste ao vivo registrado do script em si**. Nunca gerar sem a barra mostrar o código certo (`DOMINIO_EMPRESA=NN`).
- **Datas:** `balancete.py`/`razao.py` leem o campo por OCR (`ocr.py`, local, sem tokens) e **só digitam se for diferente**. Não repreencher o que já está certo.
- **Economia de tokens:** não ler capturas de tela nem re-ler skills; confiar nas conferências por OCR dos scripts e só olhar imagem se o script falhar.
- Requer pacotes `winrt-*` (OCR do Windows).

## Entradas (confirmar antes de começar)
- Empresa: código e nome (ex.: 43 - OXFORD FORTUNE) → pasta `NNN - NOME` em IMPORTAÇÃO DOMINIO.
- Período inicial e final (ddmmaaaa ddmmaaaa) e pasta de destino. O diálogo de salvar abre na **última pasta usada**, não na do cliente: o script navega e confere o "Save in" antes do Save.

## Verificação e cuidados
- Conferir `Balancete.xlsx`, `Razão.xlsx` e `Plano de contas.txt` com data recente; cabeçalho com empresa, CNPJ e período certos (sensor `validar_exportacao.py`).
- Se houver `Balancete.xls` antigo, avisar a Letícia; não apagar. Só substituir arquivo existente se for a versão a trocar (o script arquiva o anterior em `99 Originais e duplicados`).
- Não gerar nem inventar dados por outro meio. Sem controle do Domínio, a Letícia exporta e a conferência começa dos arquivos.
- Se `balancete.py`/`razao.py` falharem com "janela ... não abriu" mas a captura `saida\erro_menu.png` mostrar a janela aberta, é só o detector de título: clique OK na janela e rode `exportar_excel.py` mesmo assim.
