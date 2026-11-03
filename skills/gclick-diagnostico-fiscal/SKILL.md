---
name: gclick-diagnostico-fiscal
description: Baixa certidões e diagnósticos fiscais do SIEG (iris.sieg.com), separa só os clientes com débito e envia pelas tarefas "Consulta Relação Débitos" do Gclick da Terceirizza. Use SEMPRE que a Letícia pedir para "baixar certidões/diagnósticos do SIEG", "verificar clientes com débito" ou "enviar diagnóstico fiscal pelo Gclick", e para achar as tarefas de Consulta Relação Débitos no Gclick.
---

# Diagnóstico fiscal: SIEG -> Gclick

## Regras de precisão
- **Débito é afirmado só com fonte lida nesta rodada**: o PDF do Diagnóstico/certidão (data da consulta no topo) ou a planilha `Certidao-VisaoGeral-AAAA-MM-DD.xlsx`. Não use resultado de rodada anterior, nem "o cliente costuma ter débito".
- **A mensagem diz apenas o que foi verificado.** O âmbito (federal/estadual/municipal/trabalhista/FGTS), a data da consulta, o nome e o CNPJ vêm do documento do cliente em questão. Arquivo que é página de erro/captcha **não é certidão**: avise a Letícia, não afirme regular nem irregular.
- **Valores, datas de vencimento e "pagar até"** vêm do PDF gerado (SIEG/DAS); nunca calculados, estimados ou arredondados por mim. Multa/juros não são calculados à mão (ver 2e).
- **Conferir CNPJ do PDF = CNPJ da tarefa/cliente antes de anexar.** Divergência: parar e avisar.
- Elementos de tela citados abaixo ("ref 217/242", "ref 199", coordenadas em pixels) são **exemplos de uma sessão** e já estavam obsoletos na própria sessão: localize o elemento de novo (`find`/screenshot); nunca reutilize `ref` ou coordenada de memória.
- Seções 2d (rodada de 19/10/2026) e 1b (resultado da validação de 19/10/2026) são **histórico**: não valem para a rodada atual. Cliente "suspenso", "desativado", exceções de envio: **reconfirmar com a Letícia a cada rodada**.
- Cliente fora do fluxo descrito, tela diferente, erro do Gclick/SIEG: **parar e avisar**; não improvisar.

## 1. Baixar do SIEG (usar Claude in Chrome, não o navegador do app)
- O navegador do app bloqueia a aba de download (`down.sieg.com`). No Chrome o ZIP baixa.
- Login: a pessoa clica em "Entrar" (nunca digitar senha/clicar login por ela).
- Certidões: `https://iris.sieg.com/Certidoes?Filtro=visao-geral`. Diagnóstico: `https://iris.sieg.com/DiagnosticoFiscal`.
- Filtro: "Adicionar filtro" > Situação > Irregular, depois "Baixar Todos" (já filtrado). Só interessam clientes COM débito. Regulares não entram no envio.
- Salvar/extrair em `ROTINAS CONTÁBIL\DIAGNOSTICO FISCAL`, em subpasta datada (`Diagnosticos_AAAA-MM-DD`, `Certidoes_AAAA-MM-DD`). Ler `MANIFESTO.txt` do ZIP: lista arquivos que não entraram.
- Cliente irregular na CRFB-PGFN não tem certidão federal no ZIP: o documento a enviar é o Diagnóstico. Certidões irregulares de outro tipo (trabalhista positiva, estadual, municipal) vão junto se existirem.
- Conferir validade: data da consulta no diagnóstico (topo do PDF) e "Validade" nas certidões (`pdftotext -enc UTF-8 -layout`).

## 1b. Validar TODAS as pendências do cliente (obrigatório antes de enviar)
A mensagem deve informar **todas** as pendências do cliente, não só a federal (há clientes com débito federal + estadual, etc.).
- Fonte 1: `Certidao-VisaoGeral-AAAA-MM-DD.xlsx` (Exportar Todos da tela de Certidões): linhas com Situação = Irregular, por Tipo (CRFB_PGFN, FGTS, Trabalhista, Estadual, Municipal). Tipo "Outros" = consulta que falhou (ex.: captcha), não é débito.
- Fonte 2: ler os PDFs do ZIP de certidões (`pdftotext -enc UTF-8 -layout`): "CERTIDÃO NEGATIVA" = ok; "POSITIVA"/"CONSTA" no BNDT = pendência (anotar o validade). Arquivo que é página de erro/captcha (ex.: Liora, estadual) **não é certidão**: avisar a Letícia, não afirmar que está regular nem irregular.
- **Federal**: anexar o Diagnóstico na etapa 2. **Estadual (e demais: trabalhista, municipal, FGTS)**: NÃO anexar (o ValidaPDF ainda não suporta); apenas informar o débito no texto da mensagem.
- Ajustar o texto: "...débitos em aberto no âmbito federal" vira "no âmbito federal e estadual" (ou o conjunto real, ex.: "federal e municipal (São Paulo)"), e dizer que o diagnóstico federal segue em anexo e que as demais pendências constam nas certidões, que enviamos sob solicitação / podem ser consultadas.
- Cliente cuja única pendência é estadual/municipal (sem diagnóstico): enviar sem anexo e informar no texto.
- Resultado da validação de 19/10/2026 (24 clientes da rodada): todas as estaduais e trabalhistas dos clientes enviados estavam negativas/válidas (CNDT até 05/04/2027 ou 31/03/2027), FGTS regular; única pendência extra: LEADS (municipal SP irregular). LUTECKSOLAR e MACHBEN têm estadual irregular, mas são suspensos (dispensar).

## 2. Achar as tarefas no Gclick (passo a passo da Letícia)
1. Abrir o Dashboard do Gclick (`appp.gclick.com.br/dashboard`, já logado).
2. Rolar até o **Painel de Controle**.
3. Bloco **Obrigações** > linha **ADMINISTRATIVO** > coluna **Ação** > clicar na célula marrom (ex.: "50").
4. Abre a lista das tarefas "Consulta Relação Débitos" abertas (OUT/2026 etc.). Abrir a tarefa de cada cliente por ali.
5. Dentro da tarefa, trabalhar **só** no quadro "Atividades para realização da Tarefa" (3 etapas, botões à direita de cada linha):
   1. **Consulta Débitos em aberto**: botão verde de check (dar o check da etapa).
   2. **Débitos em aberto**: botão verde do clipe: anexar o PDF (diagnóstico/certidão; o sistema valida o PDF, tooltip "ValidaPDF").
   3. **Enviar débitos em aberto**: botão verde do wifi: é daqui que sai o envio ao cliente (mensagem pronta).
6. **NÃO usar** os botões da barra de baixo: Agendar, Email, DIGISAC e Criar Pendência (o composer de Email avulso vem vazio).
7. **Dispensar** (botão ciano à direita, abaixo do quadro): usar nas tarefas de clientes suspensos.
- A busca do topo ("Digite aqui para começar a pesquisa") por cliente só abre o cadastro; não use para achar tarefas.

## 2b. Passo a passo rápido por cliente (testado na ANJOS, 19/10/2026)
Enviar **somente pelo Digisac** (etapa 3), nunca por e-mail. Canal **sempre "WHATSAPP - Conexão WhatsApp 1"**.
1. Lista de tarefas (modal do dashboard): digitar o cliente no campo "O que você está procurando?" e clicar na linha; a tarefa abre em **nova aba** (URL `app.gclick.com.br/coListar.do?obj=coevento&coid=4&eveId=<ID>&empId=<ID>`; guardar a URL de cada cliente para reabrir sem refazer a navegação).
2. Etapa 2, clipe azul ("Anexar Arquivo") abre o modal "Anexando 1 Arquivo". Os `<input type=file>` estão ocultos: usar `find` ("input type=file hidden dropzone") e `file_upload` no **1º input** (o do modal visível; ref sobe a cada abertura). Caminho: `...\DIAGNOSTICO FISCAL\Diagnosticos_AAAA-MM-DD\<EMPRESA (CNPJ)>\Diagnostico_<CNPJ>.pdf` (conferir CNPJ do arquivo = CNPJ da tarefa). Clicar "Anexar" (botão azul no rodapé do modal). A etapa passa a mostrar "administrativo.tzz ✔".
   **Dicas de robustez (aprendidas na prática):** o tamanho da janela do Chrome muda entre abas, então coordenadas fixas falham. Preferir `find` + `ref` para os botões (clipe = "Anexar Arquivo", wifi = "Enviar mensagem multi-canais", check da etapa 1). Os refs mudam a cada recarga; refazer `find`. No modal de anexo, o `find` lista vários `input[type=file]`: usar o de **maior número de ref** (o do modal aberto) e conferir pela miniatura "Diagnostico… ✔" antes de clicar "Anexar" (ref do botão "Anexar" do modal "Anexando 1 Arquivo"). Se o upload não mostrar miniatura, tentar outro ref. Com 2+ contatos, o campo Telefone cresce e empurra Canal/Anexo/Enviar para baixo: tirar screenshot antes de clicar. Depois do envio a página recarrega; a etapa 3 mostra "administrativo.tzz ✔"; só então dar o check da etapa 1 (verde = tarefa concluída).
   Mais dicas: (a) o `find` de inputs retorna 4 refs quando o modal está limpo: usar o **primeiro**; se aparecer um 5º ref novo (maior), usar esse. (b) Quando o contato é um **grupo de WhatsApp** ("Grupo ...@g.us", ex.: M Lucas) o campo **Canal desaparece** e o formulário sobe (na sessão de 19/10/2026, tela 1536x639, o Anexo ficou em ~y=245 e o Enviar em ~y=478; **não reutilize**: tire screenshot e localize antes de clicar). (c) Fluxo mais rápido por cliente: dashboard > lista > busca > tarefa abre em nova aba (anotar o novo tabId via `tabs_context_mcp`); `find` de "Anexar Arquivo" e "Enviar mensagem multi-canais"; depois do envio, `find` do check da etapa 1 e clicar (os números de `ref` mudam a cada carga).
3. Etapa 3, wifi ("Enviar mensagem multi-canais") abre "Enviando Mensagem pelo DIGISAC":
   - **Telefone** (multi-seleção): marcar todos os contatos, **exceto "NÃO ENVIAR AQUI"**, e não repetir contatos com o mesmo número (ex.: Recepção = Bárbara).
   - **Canal**: Conexão WhatsApp 1.
   - **Anexo** (campo visual): clicar no campo e escolher `atividade 2/Diagnostico_<CNPJ>.pdf`. Setar por JS não reflete na tela; usar clique.
   - **Mensagem**: o modelo vem com o trecho `**Informar o âmbito: federal, estadual ou municipal**` e termina cortado em "esclarecimento". Substituir o textarea por JS (`value=` + eventos `input`/`change`) pelo texto abaixo, usando o nome da 1ª linha ("Prezado, <NOME>") e a data da consulta do PDF:
     ```
     Prezado, <NOME>

     Verificamos a existência de débitos em aberto no âmbito federal. Após análise, não identificamos os respectivos pagamentos. O diagnóstico fiscal (consulta de <DD/MM/AAAA>) segue em anexo.
     (Modelo aprovado pela Letícia em 19/10/2026. A frase "não identificamos os respectivos pagamentos" é o texto do modelo: se o PDF/consulta mostrar pagamento ou parcelamento em andamento, **não envie esse trecho**; pergunte à Letícia.)

     Caso já tenham sido quitados, solicitamos a gentileza de nos encaminhar os comprovantes.
     Se ainda não foram pagos e houver interesse na regularização, por favor, informe a data prevista para o pagamento.

     Ficamos no aguardo do seu retorno e permanecemos à disposição para quaisquer esclarecimentos.

     Atenciosamente,
     Atendimento Terceirizza.
     ```
     **Atenção:** o modelo do Gclick corta o nome em 32 caracteres ("...ELETRICOS L"). Sempre trocar a 1ª linha pelo nome completo (nome da pasta do cliente, sem o CNPJ). Contatos com o mesmo número (ex.: "Jaime Barbosa - Sócios" e "Recepção") valem 1 só.
     (o contador "1512 caracteres" é fixo; ignorar). Para outro âmbito (trabalhista, estadual, municipal), trocar "federal" e o documento anexado.
   - Clicar "Enviar" (verde, rodapé). Aguarda ~6 s e a página recarrega.
4. Voltar à etapa 1 e clicar o **check verde**: a tarefa fica toda verde (Data Entrega preenchida). Só aí o cliente está concluído.
5. Se algo falhar, não improvisar: parar e avisar.

## 2c. Dispensar tarefa de cliente suspenso
Abrir a tarefa (mesmo caminho do 2b), conferir o CNPJ no campo Cliente, clicar **Dispensar** (ciano, canto direito, abaixo do quadro de atividades; localizar na tela), escrever "Cliente suspenso." em **Justificativa** (obrigatória), clicar **Salvar**. A tarefa fica azul com "Data Dispensada" e a justificativa no histórico. Se o dashboard der "error page", recarregar e repetir.

## 2d. Resultado da rodada de 19/10/2026 (referência)
Enviados (Digisac, Conexão WhatsApp 1, diagnóstico anexado, tarefa concluída): ANJOS, Casa Clara, Doceria das Bittens, EW Transportes, GM, Instituto Ruppenthal, M Lucas, MCS Mentoria, MK Tratamento, Next Educação, Oxford Fortune, Studio A+, Terceirizza Soluções Digitais (só Karine), Liora, Leads (federal + municipal SP). Dispensadas (suspensos): Da Capo, LUTECKSOLAR, Machben. Pendentes de decisão: Rodrigo Simmi (desativado), Priscila Fagundes, Avanço Odontologia, CAZABEN, Oxford Capital, PBB (sem tarefa na lista do dia), mensagem para clientes regulares (sem modelo no Gclick).

## 2e. "Recalcular" débito = gerar NOVA GUIA no SIEG (nunca calcular multa/juros na mão)
Quando a Letícia pedir para recalcular o débito de um cliente do Simples Nacional (cliente pede boleto/guia atualizada):
1. SIEG (hub.sieg.com, logado) > Pendências > **SN/MEI** > **PGDAS** (não "Geração de DAS": essa é do PGMEI, só MEI).
2. Aba **Pendências** > navegar o mês (setas) até o **período do débito** (ex.: Julho 2026) > clicar no badge "1 Pendências" da empresa (abre "Declarações da empresa").
3. Linha do período > botão azul **Gerar DAS** (baixa o PDF; a "Consulta" passa a ter a data/hora de agora e o Total já vem atualizado). A aba "Gerar DAS" do PGDAS lista só o mês corrente.
4. O PDF cai em `Downloads` como `<guid>.tmp` (é um PDF válido: conferir com `pdftotext`): CNPJ, período, número do documento, **"Pagar este documento até DD/MM"** (costuma ser SÓ o dia da geração) e Valor Total. Copiar para `DIAGNOSTICO FISCAL\DAS_<CLIENTE>_<MM-AAAA>_pagar-ate-AAAA-MM-DD.pdf`.
5. Enviar pelo Digisac (conversa do contato) texto + PDF. **Texto curto, SEM detalhar principal/multa/juros nem valor** (o cliente já sabe; regra reforçada pela Letícia em 19/10/2026). Modelo: "Segue a guia recalculada, com vencimento em <DD/MM>. Posso ajudar em algo mais?" (sempre fechar perguntando se pode ajudar em algo mais e agradecer quando fizer sentido). (usar a data "pagar até" do PDF). **Antes, ler o fim da conversa no Digisac: se a Letícia já está falando com o cliente hoje, NÃO começar com "Olá/Bom dia"** (ir direto ao ponto); só cumprimentar se a conversa estiver parada.
Digisac web (enviar-notas-digisac): texto vai pela área de transferência (`Set-Clipboard -Value` + ctrl+v + Return, evita Enter nas quebras); PDF por `Set-Clipboard -Path` + ctrl+v + botão "Enviar" (canto inferior direito da tela de anexos).
Corrigir mensagem já enviada no Digisac: passar o mouse sobre ela > seta para baixo (canto superior direito do balão) > **Editar**; a mensagem sobe para a caixa; `ctrl+a`, colar o texto novo e Return. Fica com a marca "editado".
Validado em 19/10/2026 com MK Tratamento (07/2026, R$ 728,35).

## 3. Regras de envio
- Fora do envio por pedido da Letícia: IBRACEM (Instituto e S.A.), CERTIFIQUE-SE, BA2B (ela já está em contato). Confirmar a lista a cada rodada.
- Clientes **Suspensos**: dispensar a tarefa (não enviar). Desativado (ex.: Rodrigo Simmi): perguntar.
- Cliente sem tarefa na lista: avisar a Letícia, não improvisar.
- Cada tarefa já tem mensagem pronta (modelo do Gclick, etapa 3): ajustar conforme o passo 2b e enviar. A Letícia aprovou o texto do 2b em 19/10/2026; não pedir aprovação de novo a cada cliente.
- Ainda não existe modelo para clientes SEM débito ("parabéns, todos os débitos em dia"): a Letícia não achou no Gclick; propor texto e pedir aprovação.
- Demais regras de envio (anexar na etapa, olhinho verde, e-mail + Digisac exceto "NÃO ENVIAR AQUI", sem assinatura de pessoa, Terceirizza só para a Karine, conferir nome/CNPJ do PDF): seguir o fluxo de guias de parcelamento do Gclick (memória `gclick-parcelamentos-fluxo`, arquivo `feedback_gclick-parcelamentos-fluxo.md` na memória do projeto PARCELAMENTOS; só é carregada ao trabalhar nessa pasta: se não estiver disponível, **pergunte à Letícia** em vez de supor essas regras).
