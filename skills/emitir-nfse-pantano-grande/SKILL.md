---
name: emitir-nfse-pantano-grande
description: Emite, cancela e encaminha NFS-e no portal Cidade360 ISS Digital da Prefeitura de Pantano Grande/RS (webapp1-pantanogrande.cidade360.cloud) para o prestador ANJOS SEGURANÇA E SERVIÇOS LTDA (CNPJ 54.120.380/0001-27), e distribui o PDF gerado ao emitente pelo Digisac (terceirizza.digisac.biz). Use SEMPRE que o usuário pedir para "emitir nota", "emitir NFS-e", "gerar nota fiscal", "cancelar nota" ou "cancelar NFS-e" para esse portal ou para essa prestadora, mesmo que ele não descreva os campos exatos do formulário — a skill cobre login, preenchimento, confirmação, cancelamento e o envio do PDF pelo Digisac ao contato certo.
---

# Emitir NFS-e — Pantano Grande / Anjos Segurança

> **Antes de emitir, siga a skill `emitir-nfse`** (valida o pedido, evita nDPS duplicado e registra a nota na pasta NOTAS FISCAIS EMITIDAS). Esta skill traz só os detalhes deste canal/prestador.


Automatiza a emissão de Nota Fiscal de Serviço Eletrônica (NFS-e) no portal
municipal de Pantano Grande/RS para o prestador ANJOS SEGURANÇA E SERVIÇOS
LTDA, e a distribuição do PDF gerado via Digisac. O fluxo tem três fases:
**emitir** (ou cancelar), **baixar o PDF**, **encaminhar ao emitente**.

## Regras de precisão

- **Só para o prestador ANJOS SEGURANÇA E SERVIÇOS LTDA (CNPJ 54.120.380/0001-27) neste portal.** Outro prestador ou portal: não use esta skill.
- **Nada de valores "usuais" ou de exemplo é usado na nota.** Item da LC 116, NBS, cIndOp, cClassTrib, Anexo, alíquota e as respostas dos rádios (ente governamental, destinatário) vêm **do pedido do usuário ou de uma nota anterior que ele indicou como referência**. Sem nenhuma das duas fontes, **pergunte** antes de preencher. Os exemplos do texto (`14.01`, Anexo III, `000001`, "Não / Sim") ilustram o formato e **não são padrões**.
- Cada campo é conferido **lendo a tela depois de preencher** (get_page_text/find), não pelo ato de ter digitado.
- Número da nota, nome do arquivo PDF e contato do Digisac só são informados se lidos da tela ou da pasta Downloads; os exemplos (`54120380000127_35.pdf`, "Bárbara/Anjos") são ilustrativos.
- Divergência entre pedido e tela (nome do tomador, endereço, valor): parar e perguntar.

Cada fase termina numa ação difícil de desfazer (documento fiscal, mensagem
enviada a um cliente) — por isso o fio condutor desta skill é: preencher e
mostrar, nunca clicar no botão final sem o usuário dizer "pode confirmar"
antes.

## Fase 1 — Login

URL do portal: `https://webapp1-pantanogrande.cidade360.cloud/NFSe.Portal/Prestador`

O login pede CPF e senha do prestador. **Nunca digite a senha, mesmo que o
usuário a cole no chat** — inserir credenciais em formulários é uma ação
proibida independentemente de quem forneceu a senha. Peça ao usuário para
logar manualmente e avisar quando estiver pronto. Pergunte em qual navegador
ele logou:

- **Browser pane do Claude Code**: continue com `mcp__Claude_Browser__*`.
- **Chrome real**: use as ferramentas `mcp__claude-in-chrome__*`. Como é uma
  sessão nova, comece com `tabs_context_mcp{createIfEmpty:true}` para abrir
  o grupo de abas, depois `navigate` para a URL do portal — os cookies de
  login do Chrome real são reaproveitados automaticamente.

Depois do login, confirme com `get_page_text` que a tela é "Gerar NFS-e" e
não a de login — às vezes o usuário confirma antes da sessão realmente
carregar.

## Fase 2 — Preencher e emitir

Vá em **NFS-e > Gerar NFS-e** (normalmente já é a tela inicial pós-login).
Data, país, estado e município já vêm certos por padrão (Exigível / Brasil /
Rio Grande do Sul / Pantano Grande) — não mexa a menos que o pedido diga o
contrário.

**Tomador**: digite o CPF/CNPJ (só dígitos) no campo "Número do documento" e
clique fora do campo ou no ícone de lupa. Se a pessoa/empresa já tiver
recebido nota antes deste prestador, nome e endereço autocompletam sozinhos
— confira que batem com o que o usuário pediu antes de seguir. Se o cadastro
não existir, o portal permite digitar o Nome/Razão social manualmente no
campo ao lado.

**Dados do Serviço Prestado** — os campos de código usam um padrão de
"digitar → aparece sugestão → CLICAR na sugestão" (só digitar não confirma
o valor):

1. **Item de serviço da LC 116** (ex: `14.01`): digitar, clicar na opção do
   dropdown. Isso autopreenche "Serviço municipal" e "Serviço Nacional".
2. **NBS** (Nomenclatura Brasileira de Serviços): clicar no campo, digitar o
   código, clicar na opção.
3. **Indicador de Operações (cIndOp)**: mesmo padrão.
4. **Classificação Tributária (cClassTrib)**: mesmo padrão — no caso comum,
   `000001 - Situações tributadas integralmente pelo IBS e CBS` apareceu como
   primeira opção na nota de referência; **use a classificação da nota de
   referência ou a que o usuário indicar**, não "a primeira da lista".
5. **Valor do serviço**: formato brasileiro, ex. `210,00`.
6. **Descrição**: texto livre do serviço prestado.
7. Duas perguntas obrigatórias por rádio: "Serviço prestado ao Ente
   Governamental?" e "Destinatário é o próprio tomador?" — nas notas já
   emitidas para tomadores comuns (pessoa física ou empresa privada) foram
   Não / Sim; **confirme com o usuário ou com a nota de referência** antes de marcar.

**Apurações ISSQN / IBS CBS**: escolher o campo **Anexo** (ex: Anexo III do
Simples Nacional) calcula sozinho a alíquota e o valor do ISS a partir do
valor do serviço.

> Se o usuário pedir para usar uma nota anterior como referência/exemplo,
> use o MESMO Anexo e os mesmos códigos de serviço/NBS/indicador/
> classificação tributária dela — isso mantém a nota nova consistente com o
> enquadramento fiscal já usado antes para aquele tipo de serviço.

**Navegação na página**: o formulário é longo, com várias seções
colapsáveis (RPS, Identificação do Tomador, Identificação do Intermediário,
Dados do Serviço Prestado, Discriminação Complementar, Itens do Serviço
Prestado, Deduções, Construção Civil, Carga Tributária Aproximada,
PIS/COFINS, Apurações ISSQN/IBS CBS). Prefira `find` para localizar um
elemento pelo texto em vez de calcular quantos scrolls são necessários —
`scroll_amount` tem teto de 10 por chamada e o comportamento de rolagem da
página não é totalmente previsível.

**Antes de clicar em "Gerar NFS-e"**: emitir a nota é uma ação fiscal — só
se desfaz com um cancelamento formal, com motivo e justificativa (Fase
"Cancelamento" abaixo), então trate como irreversível. Monte um resumo
curto com tomador, código de serviço, descrição, valor, anexo/alíquota e
ISS calculado, e só clique em "Gerar NFS-e" depois que o usuário confirmar
explicitamente ("pode emitir", "confirma", etc.) — nunca a partir de uma
suposição de que os dados "parecem certos".

## Fase 3 — Baixar o PDF

A tela de sucesso pós-emissão mostra o número da nota e os botões
"Visualizar", "Download PDF", "Download XML", "Gerar nova NFS-e", e um
campo para enviar por e-mail direto do portal. Clique "Download PDF" — o
arquivo cai na pasta Downloads do usuário com o nome
`{CNPJ do prestador}_{número da nota}.pdf` (ex:
`54120380000127_35.pdf`). Se estiver automatizando, confirme o download
lendo a pasta Downloads por um arquivo recente com esse padrão de nome,
já que o clique não retorna o caminho do arquivo diretamente.

## Cancelamento (nota emitida errada)

Menu **NFS-e > Consultar NFS-e**. Preencha "Número inicial da NFS-e" e
"Número final da NFS-e" com o número da nota e clique **Pesquisar**. Marque
o checkbox da linha da nota — isso revela uma barra de ações (Detalhes,
Substituir NFS-e, **Cancelar NFS-e**, Download Planilha/XML/PDF, Situação
dos e-mails). Clique **Cancelar NFS-e**: abre um modal pedindo **Motivo**
(dropdown — "Outros" cobre o caso de erro de tomador) e **Justificativa**
(texto obrigatório, explique o que houve). O modal tem dois botões
"Confirmar": o de cima (junto ao aviso amarelo) é decorativo/redundante, o
que realmente executa fica embaixo do formulário, depois da justificativa —
preencha tudo antes de clicar nele. Assim como emitir, cancelar é
irreversível: só clique com confirmação explícita do usuário.

## Fase 4 — Encaminhar o PDF pelo Digisac

Regra central desta fase: **o PDF vai sempre para o contato do EMITENTE**
(a empresa cliente da contabilidade, dona da nota — ex: Bárbara/Anjos),
**nunca para o tomador** (o cliente final que recebeu o serviço e está
sendo cobrado na nota). É fácil confundir os dois porque o tomador é quem
aparece nos dados fiscais que acabaram de ser preenchidos, mas quem recebe
o PDF por Digisac é a empresa que pediu a emissão.

URL fixa deste Digisac: `https://terceirizza.digisac.biz/`

1. Busque o contato do emitente na aba **Contatos**, pelo nome da empresa
   ou pessoa. Pode haver contatos parecidos e ambíguos (ex: um contato de
   prospecção comercial antigo, sem relação com o atendimento atual, ao
   lado do contato certo) — **confirme com o usuário qual é o contato
   correto antes de enviar** sempre que houver mais de um resultado
   plausível, em vez de escolher pela aparência do nome.
2. Se o chamado (ticket) já existir mas estiver **fechado** ("Fim do
   chamado"), clique **Abrir chamado** e escolha um departamento (ex:
   Contabilidade) para reabri-lo.
3. Se o chamado **pertencer a outro atendente** ("Chamado pertence a outro
   atendente"), use **Transferir chamado**, escolha o departamento e deixe
   o atendente em branco/padrão para assumi-lo — só depois disso a caixa
   de mensagem fica disponível para enviar.
4. Cuidado ao usar os ícones do topo da conversa: o ícone vermelho de
   **Fechar chamado** fica perto de outros ícones de ação — não é o mesmo
   que "Transferir chamado", e fechar por engano encerra o atendimento.
5. **Anexar o PDF**: clique no ícone "+" ao lado do campo de mensagem >
   **Arquivo**. Isso abre o seletor de arquivos nativo do sistema
   operacional, que as ferramentas de automação de navegador não conseguem
   controlar diretamente. (O Digisac também aceita colar o arquivo copiado: ver `enviar-notas-digisac`,
   "PDFs: copiar e colar"; use a que funcionar sem travar num diálogo nativo.) Em vez de clicar e travar num diálogo nativo:
   - use `find` para localizar o input de arquivo oculto por trás do botão
     (busca por algo como "hidden file input element for uploading
     attachment");
   - copie o PDF baixado para a pasta scratchpad da sessão — `file_upload`
     só aceita caminhos dentro de pastas às quais a sessão tem permissão de
     leitura, e a pasta Downloads do usuário normalmente não está entre
     elas;
   - chame `mcp__claude-in-chrome__file_upload` com o `ref` do input e o
     caminho do arquivo copiado.
6. Escreva uma legenda curta explicando a nota, por exemplo: *"Olá,
   [Nome]! Segue a NFS-e nº [número], emitida para [tomador], referente a
   [descrição do serviço], no valor de R$ [valor]."* Cada campo entre
   colchetes vem da tela de sucesso/da nota emitida, nunca de suposição.
7. Peça confirmação do usuário antes de clicar em **Enviar** — é uma
   mensagem indo para um cliente real.
8. Se o chamado pertencia originalmente a outro atendente antes de você
   assumir (ex: "Paulo Rhoden | Administrativo"), **devolva o chamado a
   ele** ao final via "Transferir chamado" (mesmo departamento, escolhendo
   o atendente original) — assim ele não fica preso à sua conta só porque
   você enviou um anexo por ali.

## Resumo das confirmações obrigatórias

Nunca pule a confirmação do usuário nestes quatro pontos, mesmo que os
dados pareçam óbvios ou repetitivos de uma nota anterior:

1. Antes de clicar em **Gerar NFS-e** (emissão).
2. Antes de clicar em **Confirmar** o cancelamento.
3. Antes de clicar em **Enviar** no Digisac.
4. Antes de assumir qual é o **contato certo** no Digisac, se houver mais
   de um candidato plausível.
