---
name: emitir-nfse-gm
description: Passo a passo completo para emitir NFS-e da GM - COMUNICACAO E MARKETING LTDA (Gabriella Freire) no portal nacional, salvar o PDF, enviar pelo Digisac e fechar o chamado. Use SEMPRE que o usuário colar um pedido de nota da Gabriella/GM ("Favor emitir uma nota", razão social, CNPJ, valor, serviço) ou disser "emita essa nota" no contexto da GM. Complementa emitir-nfse-portal-nacional e enviar-notas-digisac, com os parâmetros fixos da GM para não perguntar o óbvio.
---

# Notas da GM - COMUNICACAO E MARKETING LTDA

> **Antes de emitir:** valide o pedido (prestador, tomador, valor, serviço), confira se a nota já não foi emitida (evita nDPS duplicado), peça o "pode emitir" e registre a nota na pasta NOTAS FISCAIS EMITIDAS. Esta skill traz os detalhes deste canal/prestador.


Regra do usuário: **não fazer perguntas óbvias**. Tudo que está fixo abaixo é usado direto. Perguntar só se algo for realmente ambíguo (serviço fora da tabela, dado do tomador que não bate, valor que não aparece).
Detalhes técnicos de portal e Digisac: skills `emitir-nfse-portal-nacional` e `enviar-notas-digisac`. **Para a GM, esta skill tem precedência** sobre `emitir-nfse-portal-nacional` onde forem diferentes (ex.: competência = hoje, abaixo).

## Regras de precisão
- **Dados do pedido** (tomador, CNPJ, valor, descrição) são copiados exatamente do texto colado. Valor, CNPJ ou nome que não aparecem no pedido **não são completados de memória**: pergunte. Na conferência, todo campo vem da tela ou do pedido, nunca de suposição.
- **Código de tributação e NBS** só os da tabela abaixo. Serviço fora da tabela: **não use código de memória**. Procure nas opções do próprio portal, mostre ao usuário as opções encontradas (código + texto) e use na nota só a que ele escolher.
- **Competência = data de hoje** é regra da GM. Se o pedido trouxer outra data, não decida sozinho: pergunte qual vale.
- Valores fixos abaixo foram observados nas notas de 13/10 e 19/10/2026; se o portal mostrar algo diferente (alíquota, regime, endereço do prestador), pare e relate.
- Sem "pode emitir" na conferência não se emite. Número da nota e chave de acesso só são informados se lidos da tela de sucesso.

## Dados fixos
- Prestador: GM - COMUNICACAO E MARKETING LTDA, CNPJ 54.427.895/0001-74, Porto Alegre/RS, Simples Nacional ME/EPP, regime 1.
- Quem pede: Gabriella Freire (grupo "Gabriella Freire | GM Comunicação" no Digisac, Conexão WhatsApp 1, chamado em Contabilidade).
- Competência: data de hoje. Alíquota do Simples 6,00%. Sem retenção de ISSQN. IBS/CBS = Não. Local da prestação: Porto Alegre/RS.
- Campos do pedido que não entram na nota: "Órgão emissor" (referência interna).
- Pasta dos PDFs: `G:\Drives compartilhados\Clientes Contabilidade\036 - GM - COMUNICACAO E MARKETING LTDA [Gabriella Freire]\3. Departamento Fiscal\2026\<NN - Mês>\1 - MUNICIPAL\PRESTADOS`

## Código por tipo de serviço
| Serviço | Código | NBS | Descrição |
|---|---|---|---|
| Educacional/palestra/revista (IASRE, ADRA, etc.) | 08.02.01 | 122052000 | a que o pedido trouxer (ex.: "Conclusão revista ADRA 2026") |
| Consultoria de marketing | 17.01.01 (assessoria ou consultoria) | 114011400 | "Consultoria de marketing" |
Serviço novo: buscar as opções no portal, **listar para o usuário (código + descrição exata do portal) e aguardar a escolha**; só depois preencher. Registrar o código escolhido nesta tabela apenas se o usuário pedir.

## Passo a passo
1. **Login:** abrir `https://www.nfse.gov.br/EmissorNacional/Login` numa aba do Chrome e pedir ao usuário para logar na GM. Nunca digito senha. Aguardar o "já loguei".
2. **Pessoas:** entrar por `.../DPS/Pessoas/NovaNFSe`. IBS/CBS = Não; competência = hoje; emitente Prestador. O script do portal lança `Cannot read properties of undefined (reading 'Inscricao')`: ignorar, os dados carregam. Conferir `#Prestador_Inscricao`=54.427.895/0001-74 e `#txtOpcaoSN` contendo "Optante". Se vier "NENHUM"/vazio, voltar ao Dashboard e clicar no link "Emissão completa" do menu (essa rota funcionou), ou recarregar.
3. **Tomador:** abrir o histórico (`#btn_Tomador_Inscricao_historico`), procurar pelo CNPJ e importar pelo `label` da linha. Se não existir, digitar o CNPJ em `#Tomador_Inscricao` e `#btn_Tomador_Inscricao_pesquisar` (traz nome e endereço pelo CNPJ/CEP). Corrigir só o logradouro se vier cortado (ex.: "A PROFESSOR..." -> "AVENIDA PROFESSOR..."). Compra governamental = Não.
4. **Serviço:** município Porto Alegre/RS (select2, opção exata), código de tributação (select2, esperar `$.active===0`), imunidade/exportação = Não, NBS pelo valor (`.val('122052000').trigger('change')`), descrição.
5. **Valores:** marcar **"Informar alíquota do Simples Nacional"** (`ValorTributos.TipoValorTributos` = 4) ANTES de preencher; valor em formato BR (`1.500,00`), alíquota `6,00`, retenção Não. Sem a opção 4 o Avançar volta com erro.
6. **Conferência:** abrir a tela "Emitir NFS-e", montar a tabela (prestador, competência, tomador, endereço, código, NBS, descrição, valor, alíquota, retenção) e **pedir o "pode emitir"**. Emitir é irreversível. Só então `document.getElementById('btnProsseguir').click()`.
7. **Depois de emitir:** registrar a chave de acesso (50 dígitos). O DANFSe dá 403 para o meu navegador: o usuário baixa o PDF (Notas > Emitidas, ou Consulta Pública com captcha dele) e salva na pasta PRESTADOS.
8. **Renomear:** `<NOME CURTO> - <chave>.pdf` (ex.: `CORFIX - ...`, `ADRA SUL - ...`). Nome curto sempre: com o nome completo o caminho passa de 260 caracteres e o rename falha. Conferir `%PDF-` e `%%EOF`.
9. **Digisac:** abrir `https://terceirizza.digisac.biz/` (o usuário já fica logado), buscar "Gabriella Freire", abrir a conversa (clique por coordenadas), conferir que o pedido da nota aparece e o cabeçalho é Conexão WhatsApp 1 / Contabilidade.
   - Texto: **só avisar que a nota segue em anexo; sem valor, sem tomador, sem serviço.** Modelo: "Olá, bom dia, Gabriella! Segue a nota fiscal em anexo. Qualquer dúvida estamos à disposição!" (bom dia/boa tarde pelo horário).
   - Digitar na caixa, mostrar e pedir o OK; enviar com Enter. A caixa muda de altura com o texto: pegar coordenadas com `getBoundingClientRect()` antes de clicar/colar.
   - PDF: `Set-Clipboard -LiteralPath <arquivo>`, Ctrl+V na caixa, conferir que a tela de anexos lista só esse arquivo e clicar no botão de envio (**o rótulo variou entre versões do Digisac**: "Salvar os arquivos para envio" em 02/10/2026 e "Enviar" nas notas da GM; leia o rótulo na tela. Qualquer um **envia na hora**; só depois do "pode enviar" do usuário).
   - Se entrar um chamado novo, o Digisac troca a conversa aberta: reconferir o chat antes de Enter.
10. **Fechar o chamado só quando o usuário pedir:** botão "Fechar chamado" (topo), escolher o assunto **"BPO | Emissão notas fiscais ou novos cadastros"** (obrigatório; o select abre ao clicar), **deixar o Resumo vazio**, confirmar. Sucesso: "Fim do chamado - Encerrado por Letícia Aguiar - <data hora>".

## Histórico de notas (referência)
- 13/10/2026, nº 55: ADRA Sul (17.578.142/0003-03), R$ 450,00, 08.02.01.
- 19/10/2026: Corfix (92.787.050/0001-89), R$ 1.500,00, 17.01.01; chave 43149022254427895000174000000000005626103894293791.
- Pendente de confirmar: nota IASRE (87.115.838/0080-02) de R$ 6.250,00, preparada em 05/10 e nunca emitida (sem "pode emitir"); envio do PDF da ADRA Sul no Digisac. **Estes itens são histórico, não instrução**: não emita nem reenvie nada a partir desta lista sem pedido novo do usuário.
