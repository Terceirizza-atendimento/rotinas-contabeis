---
name: exportar-plano-de-contas
description: Exporta o plano de contas do cliente do Domínio Contabilidade (Utilitários → Exportação → Contas) e salva como "Plano de contas.txt" na raiz da pasta do cliente em IMPORTAÇÃO DOMINIO. Use SEMPRE que o usuário pedir para "salvar/exportar/baixar o plano de contas" de um cliente, "atualizar o plano de contas da pasta", ou quando um fechamento precisar do plano de contas do cliente e a pasta não tiver o arquivo ou ele estiver desatualizado. Complementa a skill abrir-dominio-contabilidade (o sistema precisa estar aberto e logado, com a empresa do cliente ativa).
---

# Exportar o plano de contas do cliente

Complementa **`abrir-dominio-contabilidade`**: leia essa skill primeiro para abrir o sistema, as credenciais por variável de ambiente e as armadilhas de foco e digitação. Aqui só entra o que é específico do plano de contas.

Script: `C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\automacao-domino\scripts\plano_contas.py` (mesma pasta dos outros, depende de `dominio_lib.py`). Rode dentro da pasta dos scripts, com `python plano_contas.py ...`, **sem `-I`**.

## Regras de precisão

- "Exportei o plano" só vale com: a linha `salvo: ...\Plano de contas.txt (N bytes)` do script **e** o sensor sem FALHA (`validar_exportacao.py "<pasta>" --tipo plano`). O sensor confere formato (latin-1, largura fixa, linha final de 9s, códigos únicos) e idade; **não confere a qual empresa o plano pertence** (o arquivo não traz CNPJ para o sensor ler). A identidade só é conferida indiretamente: as contas do Balancete/Razão da mesma pasta precisam existir no plano.
- A empresa ativa no Domínio **não é presumida**: confirme nome e CNPJ no cabeçalho de um relatório da empresa certa antes de exportar. Se não der para confirmar, pergunte ao usuário.
- Número de linhas, bytes e contas citados abaixo são da empresa 075 (29/10/2026); **não valem para outros clientes**.
- O que não estiver aqui nem em `abrir-dominio-contabilidade`: não improvise; relate e pergunte.

## Destino

`IMPORTAÇÃO DOMINIO\<NNN - NOME>\Plano de contas.txt`, na **raiz** da pasta do cliente (padrão do `_TEMPLATE CLIENTE`). O arquivo já existe nas pastas de vários clientes: **a exportação substitui o existente**. `plano_contas.py` **não arquiva** o arquivo atual (quem arquiva é o `fechar_exportar.py`, que move os três arquivos para `99 Originais e duplicados` com prefixo `antes_AAAAMMDD_HHMM_`). Rodando `plano_contas.py` sozinho, se o plano atual tiver sido editado à mão, copie-o para `99 Originais e duplicados` (como `duplicata_Plano de contas.txt`) antes de exportar.

## Passos

1. Sistema aberto e logado (skill `abrir-dominio-contabilidade`) e **empresa do cliente ativa** (confira nome e CNPJ no cabeçalho de um relatório). A troca de empresa ainda não tem script.
2. Rodar:
   `python plano_contas.py "C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\<NNN - NOME>"`
   O script faz: Utilitários (620,66) → Exportação (634,626) → Contas (1105,658) → diálogo "Contas" (**usa o que o diálogo já traz; o script não altera intervalo, ordem nem tipo de conta**; na 075 o diálogo exportou todas) → **Exportar** (1075,714) → espera o arquivo no disco (até 30 s) → **OK** no aviso "Fim da exportação das contas!" (1056,604) → **Cancelar** (1180,714), que fecha o diálogo.
3. Resultado esperado: `salvo: ...\Plano de contas.txt (N bytes)`. Para a empresa 075 (29/10/2026): 525 linhas de 78 colunas, 42 000 bytes (524 contas + linha final de 9s). O arquivo é ANSI (latin-1): leia com `encoding="latin-1"`; em UTF-8 os acentos saem quebrados.
4. Rodar o sensor: `python validar_exportacao.py "<pasta>" --tipo plano --max-idade-min 30`. Só dê por concluído com `APROVADO`.

## Pasta de destino

O campo "Nome do arquivo" do diálogo já vem com `M:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\<pasta>\Plano de contas.txt`, onde `<pasta>` é a **última pasta usada** pelo Domínio, não necessariamente a do cliente ativo. Por isso o script confere se o arquivo apareceu **na pasta informada**; se o Domínio gravou em outra, ele acusa erro em 30 s (e a captura `saida\erro_plano_contas.png` mostra o diálogo). Se o arquivo não aparecer na pasta informada, o Domínio gravou na pasta sugerida (a última usada): **ache esse arquivo, avise o usuário e só mova com a confirmação dele**. Opção `--digitar` troca o caminho do campo pelo da pasta informada (o C: local aparece como `M:`): **[NÃO TESTADA]**; só use se o usuário aceitar o risco.

## Armadilhas

- **O aviso "Fim da exportação das contas!" precisa de um único clique em OK.** Mais cliques (ou tentar fechar o diálogo antes) fazem o aviso abrir e fechar várias vezes. O script espera o arquivo, aguarda 2 s e clica uma vez.
- O diálogo **não fecha sozinho** depois de exportar: sem o Cancelar, ele fica aberto bloqueando o menu (modal) e o próximo script falha.
- "Contas exportadas" no diálogo pode mostrar 0 por um momento (renderização remota lenta) e depois o total (524 na 075). Conferir pelo arquivo, não pela tela.
- Durante a gravação o arquivo pode aparecer menor ou "ocupado" (OneDrive sincronizando): espere alguns segundos antes de comparar ou copiar.
- Foco: mesmas regras da skill principal; peça ao usuário para não mexer na máquina durante a execução (~13 s).
- Dados do cliente são confidenciais: não enviar o plano a serviços externos.

## Atenção (30/10/2026, 013)
Se a janela "Importação de Arquivo" ainda estiver aberta, `plano_contas.py` clica na tela errada e abre "Definição de dados" (só leitura; fechar no X). **Feche a Importação antes**. Caminho validado à mão: Utilitários → Exportação → **Contas** → conferir o fim do "Nome do arquivo" (`...\013 - LICITOCON\Plano de contas.txt`; clicar no campo e End) → Exportar → um único OK → Cancelar. `balancete.py`/`razao.py` podem acusar "janela não abriu" com a janela aberta: clicar OK e usar `exportar_excel.py`.
