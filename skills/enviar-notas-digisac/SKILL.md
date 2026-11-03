---
name: enviar-notas-digisac
description: Envia PDFs de notas fiscais (DANFSe/NFS-e) e mensagens a clientes pelo Digisac da Terceirizza (terceirizza.digisac.biz), usando o usuário logado da Letícia Aguiar, e fecha o chamado depois. Use SEMPRE que o usuário pedir para "mandar as notas para o cliente", "enviar pelo Digisac", "avisar o grupo", "fechar o chamado", ou depois de emitir notas de qualquer cliente. Cobre achar o grupo/contato, escrever no tom da Letícia, colar os PDFs, conferir o envio e encerrar o chamado, incluindo as armadilhas conhecidas do Digisac e da Cloudflare.
---

# Enviar notas ao cliente pelo Digisac

Fluxo validado em 02/10/2026 com o grupo "R & J Odontologia | Terceirizza": 1 texto + 5 PDFs, depois fechar o chamado.
Regra de ouro: mensagem para cliente real é irreversível. **Mostre o texto e os arquivos e espere o "pode enviar"** antes de enviar.

## Regras de precisão
- **Destinatário, anexos e texto vêm do pedido e do que está na conversa.** Nome do grupo/contato, pasta dos PDFs, mês, datas e motivo do atraso nunca são deduzidos: se faltarem, pergunte. O motivo do atraso só entra na mensagem se estiver escrito na conversa ou o usuário disser.
- **Antes de enviar, confira e relate o que será enviado**: cabeçalho da conversa (nome, conexão, atendente), texto final e lista exata de arquivos (nomes lidos da tela de anexos, não da pasta).
- **Depois de enviar, só diga "enviado" se releu a conversa** e viu o texto e todos os arquivos com horário e remetente. Falha ao conferir = "não consegui confirmar".
- Rótulos de botão e coordenadas **mudam entre versões do Digisac**: leia a tela. Exemplo: o botão que envia os anexos foi "Salvar os arquivos para envio" em 02/10/2026 e "Enviar" nas notas de outubro; **os dois enviam na hora**.
- Os textos-modelo abaixo são exemplos de tom, **não são para copiar**: reescreva com os fatos do caso.
- Lista de assuntos de fechamento e IDs de conexão abaixo foram vistos em 02/10/2026; se a tela mostrar outra lista, vale a tela.

## Dados fixos
- Digisac: `https://terceirizza.digisac.biz/` (API: `https://terceirizza.digisac.biz/api/v1`)
- Atendente: **Letícia Aguiar** (as mensagens já saem com o nome dela; **não** assine no texto)
- Conexão usada nos grupos: "Conexão WhatsApp 1". Chamado normalmente em "Contabilidade".
- Pasta de notas do cliente (exemplo R & J): `G:\Drives compartilhados\Clientes Contabilidade\048 - R & J ODONTOLOGIA LTDA\3. Departamento Fiscal\2026\R & J ODONTOLOGIA LTDA\2026`
  Arquivos nomeados `NOME DO TOMADOR - <chave de acesso>.pdf`. Para outros clientes, **pergunte a pasta** se não souber.

## Caminho recomendado: tela web com o usuário já logado (o usuário vê tudo ao vivo)
Preferido porque o usuário quer acompanhar e porque a API é barrada pela Cloudflare (ver abaixo).

1. **Login.** O usuário loga no Digisac no Chrome. Eu nunca digito senha. Abra a URL numa aba do grupo do Claude in Chrome
   (`tabs_context_mcp{createIfEmpty:true}` → `navigate`). Se cair em login, peça para ele logar e avisar.
2. **Achar o contato/grupo.** Campo "Pesquisar por nome ou número..." (coluna de conversas). É um input React:
   use o setter nativo e dispare `input`:
   ```js
   const i=[...document.querySelectorAll('input')].find(x=>x.placeholder==='Pesquisar por nome ou número...');
   i.focus(); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i,'NOME');
   i.dispatchEvent(new Event('input',{bubbles:true}));
   ```
   Pegue o retângulo da linha do resultado e **clique com `computer left_click` nas coordenadas** (`.click()` em JS não abre a conversa).
   Se houver mais de um candidato plausível, **confirme com o usuário qual é**. Confira o cabeçalho (nome do grupo, conexão, atendente).
3. **Chamado.** Se aparecer "Abrir chamado"/chamado de outro atendente, siga: Abrir chamado → departamento Contabilidade; ou
   Transferir chamado (departamento + atendente padrão). **Não confunda** "Transferir chamado" com o ícone vermelho "Fechar chamado".
   Se mexer na posse do chamado, devolva ao atendente original no fim.
4. **Texto.** Leia o fim da conversa antes de escrever (contexto, o que o cliente perguntou, tom). Clique na caixa
   (`[role=textbox]`, achada por coordenadas), `computer type` o texto, **mostre ao usuário e pare**. Só com "pode enviar": `computer key Return`.
   Confirme que a caixa esvaziou e que o texto apareceu na conversa com o horário.
5. **PDFs: copiar e colar (funciona, sem diálogo nativo).**
   ```powershell
   $d='<PASTA>'; Set-Clipboard -Path (Get-ChildItem -LiteralPath $d -File -Filter '*.pdf' | % FullName)
   # conferir: Add-Type -AssemblyName System.Windows.Forms; [Windows.Forms.Clipboard]::GetFileDropList().Count
   ```
   Clique na caixa de mensagem, `computer key ctrl+v`. Abre a tela de anexos listando os arquivos (botões
   "Adicionar arquivos", "Descartar", **"Salvar os arquivos para envio"**). Confira os nomes (sem repetidos, sem faltar).
   **O botão de envio (em 02/10/2026 "Salvar os arquivos para envio"; depois "Enviar") já ENVIA tudo** (não há outro botão de enviar). Por isso só clique depois do ok do usuário.
   Opcional: `copiar_pdfs_para_colar.ps1 -Pasta "<PASTA>" [-Filtro "NOME*.pdf"] [-Ordem A,B]` (na pasta desta skill) copia só PDFs íntegros (`%PDF-` ... `%%EOF`) e imprime a lista; confira a lista impressa com os arquivos pedidos.
   Os PDFs vão em paralelo; a ordem no grupo pode sair diferente da fila, é normal.
   Para controlar a ordem ou enviar um a um, copie e cole um arquivo por vez.
6. **Conferência.** Releia o fim da conversa: texto + todos os arquivos, enviados por Letícia Aguiar. Relate no chat com horários.
7. **Fechar chamado (só se o usuário pedir).** Botão "Fechar chamado" (topo, ícone vermelho). Abre um modal com
   **Assunto do chamado (obrigatório)** e Resumo (opcional). Sem assunto o modal não fecha e não dá erro visível.
   Lista de assuntos vista em 02/10/2026: BPO | Emissão notas fiscais ou novos cadastros; CTB | Recálculo guias;
   CTB | Geração de relatórios, balanços, demonstrativos; CTB | Folha de Pagamento; CTB | Fechamento, dúvidas e alinhamento;
   SOCIETÁRIO | Certificado Digital; DVRS | Grupos Whatsapp; entre outros. Para envio de notas: **"BPO | Emissão notas fiscais ou novos cadastros"**.
   Sucesso aparece como "Fim do chamado - Encerrado por Letícia Aguiar - <data hora>". Informe qual assunto foi usado.

## Armadilhas conhecidas do navegador (Digisac é um SPA pesado)
- `find`, `read_page` e `screenshot` costumam travar nessa aba ("Page still loading" / timeout). **Use `javascript_tool` para ler o DOM
  e `computer left_click`/`type`/`key` por coordenadas.** Calcule as coordenadas com `getBoundingClientRect()`.
- Elementos com várias camadas de `div` iguais: escolha o de **altura < 120px** para linhas de conversa.
- Recarregar a página fecha a conversa; reabra pela busca.
- `file_upload` precisa de `ref` (vem de find/read_page, que travam). Por isso o caminho de copiar/colar acima.
- Não tente alcançar `127.0.0.1` a partir da página (o Chrome exige permissão de rede local e a chamada trava).

## Caminho alternativo: API (só se o usuário pedir, ou para consultas)
- Token: variável de ambiente de usuário `DIGISAC_TOKEN`. **Nunca** imprimir, gravar em arquivo, colocar em script ou pedir no chat.
  Para o usuário guardar o token com segurança: rodar no PowerShell dele
  `$s=Read-Host 'Token' -AsSecureString; [Environment]::SetEnvironmentVariable('DIGISAC_TOKEN',[Net.NetworkCredential]::new('',$s).Password,'User')`
  (não colar o token dentro de arquivos `.ps1` em pastas compartilhadas).
- A **Cloudflare bloqueia o User-Agent padrão do Python** (erro 1010). Funciona com UA próprio e honesto, por exemplo
  `User-Agent: terceirizza-rotinas-contabeis/1.0`. Não use UA de navegador falso.
- `Authorization: Bearer <token>`; `GET /contacts?query={"where":{"name":{"$iLike":"%R & J%"}}}` e `GET /services` funcionam (200).
  Grupos aparecem com `isGroup=true`. Conexões vistas: WhatsApp 1 `318c1cfe-7ed8-4fcf-9319-a9a5caf6e164`, Comercial 2 `c9c23548-...`.
- Envio via `POST /messages` **validado em 30/10/2026** (Studio A+): corpo JSON `{type:'chat', contactId, serviceId, text, file:{base64, mimetype:'application/pdf', name}}` (UTF-8 em bytes) manda o PDF **com o texto como legenda numa única mensagem**, já em nome do usuário do token (Letícia). Achar o contato por `GET /contacts` (o nome no painel pode diferir do da API: confirme pelo número) e conferir depois na conversa. Peça o ok do usuário antes (é irreversível).

## Texto das mensagens (tom da Letícia)
Natural, educado, curto, sem formalidade de robô. Exemplos reais dela: "Olá, boa tarde! Passando para atualizar vocês de que...",
"Bom dia, Dr. Rodrigo! Como informei ontem mesmo, ...", "Assim que normalizar será enviado." Sem assinatura no texto.
Modelo usado nas notas de setembro:
> Olá, boa tarde! Passando para avisar que o portal nacional normalizou e já conseguimos emitir as notas retroativas de setembro, todas com data de 28/09. Seguem os PDFs em anexo. Desculpem a demora, foi por conta da instabilidade do sistema. Qualquer dúvida estamos à disposição!
Ajuste mês, data, motivo do atraso e saudação (bom dia/boa tarde) a cada caso. Não invente motivo: use o que está na conversa.

## Confirmações obrigatórias
1. Antes de enviar o texto. 2. Antes de clicar no botão de envio dos anexos (envia os PDFs). 3. Antes de assumir o contato certo, se houver ambiguidade.
4. Fechar chamado só quando o usuário pedir; avisar o assunto escolhido.
