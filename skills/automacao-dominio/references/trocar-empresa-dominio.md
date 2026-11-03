---
name: trocar-empresa-dominio
description: Troca a empresa ativa no Domínio Contabilidade (F8, diálogo "Troca de empresas") e confere pela barra superior. Use quando for preciso mudar de cliente no sistema antes de integrar, exportar ou importar, ou quando a empresa ativa não for a do cliente em fechamento.
---

# Trocar a empresa ativa

Script: `automacao-domino\scripts\trocar_empresa.py <codigo>` (rode dentro de `automacao-domino\scripts`, sem `-I`; raiz em `...\IMPORTAÇÃO DOMINIO\automacao-domino`). Pré-requisito: sistema aberto e logado (skill `abrir-dominio-contabilidade`).

- O código é o da **empresa no Domínio** (ex.: 43 = OXFORD FORTUNE), que **não é necessariamente o número `NNN` da pasta do Drive**: confirme com a usuária ou pela barra superior; nunca deduza.
- O script: se a barra já mostra o código, não faz nada; senão F8 → "Troca de empresas" → acha por OCR o campo Código e o botão Acessar → digita → Acessar → confere a barra. Esc fecha o diálogo.
- **Sem teste ao vivo do script em si registrado ainda.** Em 29/10 a troca **manual** (feita por uma pessoa clicando direto na tela) errou porque o clique foi calculado em cima de uma captura reduzida sem dobrar a coordenada — não é um bug do `trocar_empresa.py`, que já lê a tela cheia (1920x1080) por OCR e clica nas coordenadas reais. Mesmo assim, até rodar ao vivo uma vez: **confira a barra e o cabeçalho de um relatório (nome e CNPJ)** depois; se falhar, a troca é manual: clicar no nome da empresa (canto superior direito) ou F8, buscar por Código/Apelido, Acessar.
- A barra superior pode ficar desatualizada: para ter certeza, o cabeçalho do relatório mostra a empresa real.
- Variável `DOMINIO_EMPRESA=NN` faz os scripts de relatório abortarem se a barra não mostrar NN.
- Não digitar senha; não mexer enquanto outro script de tela roda.
