---
name: fechar-cliente-dominio
description: Roda o fechamento de UM cliente no Domínio em um comando (fechar.py): abre a sessão, integra fiscal/folha, exporta Balancete/Razão/Plano, classifica e monta o CSV, importa e confere, por etapas retomáveis. Use quando a usuária pedir "fechar o cliente NNN", "rodar o fechamento completo", "retomar o fechamento de onde parou" ou quando a skill iniciar-fechamento chegar à fase do Domínio. Para uma parte isolada use a skill da parte.
---

# Fechamento de um cliente em um comando

Scripts, notas e saídas: `C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\automacao-domino` (ver `LEIAME.md`). Rode **dentro de `automacao-domino\scripts`**, `python fechar.py ...`, sem `-I`.

Antes: leia a seção "Status" e a seção da última data do `automacao-domino\NOTAS.md` e o handoff de `automacao-importacao-csv.md`; rode `python listar_scripts.py` para ver o uso atual de cada script. Eles mudam, esta skill não substitui o docstring.

## Comando
```
python fechar.py <NNN> <ddmmaaaa> <ddmmaaaa> [--integrar] [--gravar] [--de ETAPA] [--ate ETAPA] [--forcar]
```
Etapas, nesta ordem: `sessao` → `integrar` (só com `--integrar`) → `exportar` → `classificar` → `importar` (só com `--gravar`) → `conferir`.
- Estado em `saida\estado_NNN.json`; retoma com `--de ETAPA`. A etapa `importar` já feita **não roda de novo** sem `--forcar` (importar duas vezes duplica lançamentos).
- Imprime uma linha por etapa e para na primeira falha, mostrando o motivo. **Não leia capturas nem dispare agentes** salvo falha ou pedido de análise de conteúdo.
- Credenciais: `dominio_lib` lê `DW_*` do ambiente do Windows. Se faltarem, pare e peça; nunca grave em arquivo.

## Como conduzir
1. Confirme **cliente (NNN), período e se fiscal/folha já foram integrados** (a usuária integra antes; só use `--integrar` se ela mandar).
2. Confirme que a usuária **não vai usar mouse/teclado** e que nenhuma outra sessão mexe no Domínio.
3. Rode até `classificar` sem `--gravar`: `python fechar.py NNN ini fim --ate classificar`. Mostre a ela o resumo (lotes e **PENDÊNCIAS**: o que não casou com regra ou espera conta nova; nunca é chutado).
4. **PAUSA**: ela aprova o CSV em `02 Pendente de importar`. Só com a ordem expressa dela: `--de importar --gravar` (uma vez) e depois `--de conferir`.
5. Depois: mover o CSV para `01 Importados` (o script não prova que moveu; confira), conferir o sensor `APROVADO` e os saldos dos bancos no Razão novo.

## Status: o que já foi provado e o que ainda não

**O processo em si (login, integrar, exportar, alterar/excluir lançamentos, importar CSV, Gravar) já funciona e gravou de verdade** (013 LICITOCON, 30/10/2026: fiscal+folha integrados e gravados, 98 lançamentos importados e gravados; 075 e 043 também fechados). O que ainda não tem prova é **este script (`fechar.py`) rodando essas etapas como comando único, sem intervenção**: na 013 o encadeamento automático travou e o trabalho foi concluído chamando as funções uma a uma (`dominio_ops.py`) e por navegação manual.

- `sessao`, a etapa `importar` **do próprio `fechar.py`** (via `importar_csv.py pasta --gravar` como subprocesso) **ainda não rodaram assim, de ponta a ponta, sem ajuda manual**; antes de confiar sem supervisão, rode o ensaio (sem `--gravar`) e leia o Resumo.
- `integracao.py` já **termina sozinho de volta no módulo Contabilidade** (ele troca de módulo pelo logo DOMÍNIO no fim de cada chamada). Se mesmo assim `exportar` falhar por "Favoritos sem Balancete", é sinal de que uma janela de aviso ficou aberta no meio do caminho: feche-a e troque de módulo manualmente (ver `integrar-fiscal-folha-dominio`).
- `classificar` depende de `scripts\regras\NNN.json`; a pasta está vazia hoje (nenhum cliente tem regras salvas). Sem o JSON do cliente, a etapa não roda: veja `classificar-e-gerar-csv`.
- A detecção de janela do Balancete/Razão (bug que travava `balancete.py`/`razao.py` logo depois de abrir um relatório) foi **corrigida em 03/11/2026** em `dominio_lib.py`; ainda assim confira a captura depois de cada passo.
- A troca de empresa (`trocar_empresa.py`) ainda não tem teste ao vivo do script em si registrado (ver `trocar-empresa-dominio`); a etapa `sessao` confere a empresa pela barra e para se estiver errada.

## Regras
Só afirme "feito" com a linha da etapa **e** a conferência (arquivo no disco, sensor `APROVADO`, Resumo/“Dados gravados com sucesso”). Etapa não executada = pendente. Gravar lançamentos só com a autorização dela.
