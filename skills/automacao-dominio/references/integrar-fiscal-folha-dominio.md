---
name: integrar-fiscal-folha-dominio
description: Integra o fiscal (Escrita Fiscal) e a folha no contábil do Domínio para uma competência (Gerar, Regerar lançamentos contábeis, Gravar), por integracao.py. Use quando o balancete/razão estiver sem os lançamentos de entradas, saídas, serviços ou folha, ou quando a usuária mandar integrar a competência antes de exportar.
---

# Integração fiscal e folha no contábil

Script: `automacao-domino\scripts\integracao.py` (rode dentro de `automacao-domino\scripts`, sem `-I`). Procedimento completo, testes e coordenadas: `automacao-domino\NOTAS.md` e a seção "Antes de exportar" da skill `abrir-dominio-contabilidade`.

```
python integracao.py <MMAAAA | MMAAAA-MMAAAA> [--fiscal] [--folha] [--simular] [--gravar]
```
- `--simular`: preenche e captura a tela, **não** clica Gerar/Regerar. Rode antes em cliente novo.
- Sem `--gravar`: clica Gerar/Regerar e **para** imprimindo `GRAVAR PENDENTE` (nada fica gravado). Com `--gravar`: clica também Gravar e os OK/Yes/Continuar dos avisos. **`--gravar` já rodou de verdade na LICITOCON (013, 04–09/2026, 183 s)**; em NOTAS.md consta "Gravar obrigatório".
- Navega entre módulos pelo logo DOMÍNIO na mesma janela e **já termina de volta na Contabilidade** (o script troca de módulo sozinho no fim). Ainda assim, confira o módulo ativo antes de exportar: se alguma janela de aviso ficou aberta no meio do caminho, a troca final pode não ter completado.

## Antes de rodar
1. A **competência** é a do fechamento, informada pela usuária; não deduza. Confirme **empresa ativa** pela barra e pelo cabeçalho de um relatório.
2. **Só integre se faltar**: perguntar se fiscal/folha já foram integrados (regras gerais, seção 2). Gerar/Regerar altera lançamentos contábeis: a usuária autorizou esse fluxo (29/10/2026), mas só rode quando ela mandar integrar.
3. Decisões dela: em Movimentos → Integração Contábil **sempre Gerar**; em "Regerar Lançamentos Contábeis" **manter desmarcada** "Não regerar lançamentos alterados manualmente".

## Depois
- Leia as capturas `saida\int_*_depois.png` só se o script avisar erro (erro de débito/crédito → criar a conta do cliente/fornecedor em Utilitários → Alterar Cadastro de Clientes e Fornecedores: clientes = conta fechada, fornecedores = conta aberta; depois regerar só o que falhou com `--fiscal`).
- Só diga "integrado" se o script terminou com Gravar (`--gravar`) e a tela mostrou "concluída com sucesso"/"gravados com sucesso". Caso contrário relate "Gerar/Regerar clicados, Gravar pendente".
- Reexporte Balancete/Razão depois (skill `abrir-dominio-contabilidade` ou `fechar-cliente-dominio`).

## Ordem obrigatória e lançamentos não gerados [C: usuária, 03/11/2026]
1. **Primeiro o fiscal, depois a folha. Nunca a folha antes de o fiscal estar completo.** Rode `--fiscal` e confira o resultado; só então `--folha`.
2. Depois do Gerar/Regerar do fiscal, **clique em "Visualizar" os lançamentos NÃO gerados** (os que ficaram com erro, normalmente por falta de conta de cliente ou de fornecedor) e liste cada um.
3. **O Claude cria as contas que faltam**, seguindo o passo a passo do item "Erro de débito e crédito" da skill `abrir-dominio-contabilidade`: Utilitários → Alterar Cadastro de Clientes e Fornecedores; **cliente = conta fechada, fornecedor = conta aberta**. Não pedir à usuária que crie.
4. **Refaça o processo** (`--fiscal` de novo) até não restar lançamento sem gerar; só então vá para a folha (`--folha`).
5. O script `integracao.py --fiscal --gravar` faz Gerar e também Regerar; avise antes que isso ocorre (Regerar perde alterações manuais em lançamentos do fiscal).
