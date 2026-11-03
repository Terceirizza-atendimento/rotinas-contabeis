---
name: validar-exportacao-dominio
description: Sensor/revisor que confere, sem abrir o Domínio, se o Balancete.xlsx, o Razão.xlsx e o Plano de contas.txt exportados estão corretos e na pasta do cliente certo (CNPJ do cabeçalho x cliente da pasta, período, arquivo recente e completo, coerência com o plano de contas, sinais de gravação em pasta errada). Use SEMPRE logo depois de qualquer exportação feita pelas skills abrir-dominio-contabilidade ou exportar-plano-de-contas, antes de dizer que terminou, e quando o usuário pedir para "conferir/validar/revisar" o balancete, o razão ou o plano de contas de um cliente. Somente leitura.
---

# Validar a exportação do Domínio (sensor)

Esta skill **não executa nada no Domínio**: só lê arquivos e responde "aprovado ou reprovado, e por quê". As skills `abrir-dominio-contabilidade` e `exportar-plano-de-contas` guiam a execução; esta confere o resultado. Rode **depois de cada exportação**, e só dê a tarefa como concluída com `APROVADO`.

**Como relatar (sem inventar):** reproduza as linhas `[FALHA]` e `[AVISO]` exatamente como o script imprimiu e a linha `RESULTADO:`. Não resuma "tudo certo" sem a linha `RESULTADO: APROVADO`; não interprete um `[AVISO]` como aprovação; não afirme causa da falha além do que a mensagem diz (use a seção "Quando reprovar" para sugerir, marcando como hipótese). Se o script não rodar (erro de Python, `openpyxl` ausente), diga que **não validou**.

Script: `C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\IMPORTAÇÃO DOMINIO\automacao-domino\scripts\validar_exportacao.py` (depende de `openpyxl`; não precisa de `dominio_lib` nem de tela). Rode dentro da pasta dos scripts, sem `-I`.

## Como usar

```
python validar_exportacao.py "<pasta do cliente>" [--tipo balancete razao plano] [--periodo ddmmaaaa ddmmaaaa] [--cnpj <14 dígitos>] [--max-idade-min 60]
```

- `<pasta do cliente>`: a pasta onde o arquivo **deveria** estar (`IMPORTAÇÃO DOMINIO\NNN - NOME`). É isso que o sensor confronta com o conteúdo.
- `--periodo`: passe sempre que souber o período pedido (ex.: `01012026 30092026`); sem ele o sensor só mostra o período encontrado.
- `--max-idade-min`: o arquivo precisa ter sido gravado há no máximo N minutos (padrão 60; `0` desliga a checagem; o `fechar_exportar.py` usa 30). Isso pega "a exportação não aconteceu e o arquivo velho continua lá".
- `--tipo`: valide só o que acabou de exportar (ex.: `--tipo razao`) para não reprovar por um arquivo que ainda não foi gerado.
- Código de saída 0 = aprovado, 1 = há FALHA. A última linha é `RESULTADO: APROVADO|REPROVADO (n falha(s), m aviso(s))`. Leia só as linhas `[FALHA]` e `[AVISO]`; as `[OK]` são conforto.

## O que ele confere

| Checagem | Reprova (FALHA) quando |
|---|---|
| Pasta | não existe ou não segue `NNN - NOME` |
| Arquivo | não existe na **raiz** da pasta, está vazio (gravação incompleta) ou é mais velho que o limite |
| Abre | o `.xlsx` não abre; o `.txt` não termina com a linha de 9s ou tem larguras diferentes |
| Relatório certo | falta o título BALANCETE/RAZÃO, ou não há contas |
| **Cliente certo** | o CNPJ do cabeçalho é diferente do CNPJ esperado para o número da pasta |
| Período | difere do `--periodo` informado |
| Coerência | contas do Balancete/Razão que não existem no `Plano de contas.txt` (plano de outra empresa) |
| **Pasta errada** | o mesmo arquivo foi gravado há pouco em **outra** pasta de cliente, depois do da pasta validada |

`[AVISO]`: sem CNPJ esperado para aquela pasta (o sensor mostra o CNPJ/empresa que achou: confira à mão), ou arquivos `Balancete_N_...` soltos na raiz.

CNPJ esperado: tabela "CNPJ dos clientes" de `CONTEXTOS\painel-fechamento-contabil.md` (pelo número NNN) e, na falta, `.claude\scripts\cnpj_extra.json`. Cliente novo ou ausente da tabela: acrescente em `cnpj_extra.json` (só depois de conferir o CNPJ), não chute.

## Quando reprovar

1. **Não exporte de novo às cegas.** Diga ao usuário qual checagem falhou e o que ela indica.
2. `CNPJ diferente` ou `pasta errada`: a empresa ativa no Domínio não era a do cliente, ou o diálogo gravou na última pasta usada. Mova ou apague o arquivo errado **só com a confirmação do usuário**, troque a empresa (F8) e refaça a exportação.
3. `mais velho que o limite` ou `não existe`: a exportação não rodou ou falhou; veja a captura de erro em `saida\` e releia as armadilhas da skill de execução.
4. `sentinela` ou `vazio`: o arquivo estava sendo gravado (OneDrive/Domínio); aguarde alguns segundos e rode o sensor de novo antes de concluir algo.
5. Depois de corrigir, **rode o sensor outra vez**.

## O que ele não prova

- Que os **valores** batem com a tela do Domínio: ele confere identidade (empresa, CNPJ, período), formato e coerência, não os saldos.
- Que o **Plano de contas.txt é da empresa certa**: o sensor só confere formato, idade e unicidade dos códigos; a identidade do plano só aparece indiretamente (contas do Balancete/Razão ausentes no plano).
- Que o **período está certo quando `--periodo` não é passado**: sem ele o sensor só imprime o período encontrado (`[OK] período ...`) e nunca reprova por período. **Sempre passe `--periodo`** com o período pedido.
- Que a **integração do fiscal/folha foi feita** ou que o extrato do banco foi importado.
- Que a **pasta errada** não aconteceu fora de `IMPORTAÇÃO DOMINIO`: a busca de arquivo recente em outra pasta varre só as pastas `NNN - ...` dentro dela.
- O cliente 075 (DARLENE) não está no painel: o CNPJ dele vem de `cnpj_extra.json` e foi lido do próprio relatório, então a checagem de CNPJ nesse cliente é circular até alguém confirmar o número. A pasta `039 - NEXT` tem número diferente do painel (037): o sensor avisa que não há CNPJ para 039.
- O sensor não substitui a leitura do relatório pela usuária no fechamento; ele só evita levar para a conferência um arquivo da empresa errada, velho ou incompleto.

Dados de clientes são confidenciais: o sensor roda localmente e não envia nada a serviços externos.
