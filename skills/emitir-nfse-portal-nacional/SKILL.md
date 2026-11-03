---
name: emitir-nfse-portal-nacional
description: Emite NFS-e no Emissor Nacional (nfse.gov.br/EmissorNacional, emissão completa) para prestadores optantes pelo Simples Nacional da Terceirizza, e baixa os DANFSe (PDF) pela Consulta Pública. Use quando o usuário pedir "emitir nota", "emitir NFS-e", "emitir no portal nacional" ou mandar uma lista de tomadores/valores para emitir, mesmo sem descrever os campos. NÃO é a skill certa para a GM - COMUNICACAO E MARKETING (use emitir-nfse-gm) nem para o portal municipal de Pantano Grande/Anjos Segurança (use emitir-nfse-pantano-grande); se o prestador não estiver claro, pergunte qual é antes de abrir o portal. Cobre login manual, importar tomador do histórico, preencher as 4 etapas (Pessoas, Serviço, Valores, Emitir), confirmação antes de emitir, instabilidade do portal e download dos PDFs. Para enviar ao cliente depois, use a skill enviar-notas-digisac.
---

# Emitir NFS-e no portal nacional (Emissão completa)

> **Antes de emitir:** valide o pedido (prestador, tomador, valor, serviço), confira se a nota já não foi emitida (evita nDPS duplicado), peça o "pode emitir" e registre a nota na pasta NOTAS FISCAIS EMITIDAS. Esta skill traz os detalhes deste canal/prestador.


Validado em 02/10/2026 emitindo 5 notas da R & J ODONTOLOGIA LTDA (Porto Alegre). Emitir é fiscalmente irreversível
(só cancelando): **mostre a tela de conferência e espere o "pode emitir" antes da PRIMEIRA nota** de cada lote e sempre que algo mudar
(cliente, código, alíquota, valor fora do padrão). Depois que o usuário aprovar o padrão do lote ("pode emitir e seguir com as outras"),
siga sem pedir de novo, mas confira cada tela de conferência contra o pedido e **pare se qualquer dado divergir**.

## Regras de precisão
- **Só emita com dados que vieram do pedido ou da tela.** CNPJ do prestador, código de tributação, NBS, regime, alíquota, município, valor e competência nunca são completados de memória nem copiados de outro cliente.
- Toda conferência cita o campo **lido da tela** (texto da página), não o que foi digitado por script. O resultado de um `javascript_tool` só prova que o comando rodou; a confirmação é a releitura do campo.
- Itens marcados "observado em <data>" descrevem o comportamento do portal naquele dia; o portal muda. Se a tela divergir, **pare e relate**.
- Cliente fora da tabela de parâmetros: perguntar (ver abaixo). A GM tem skill própria com parâmetros fixos.
- Número da nota, chave de acesso e situação só são informados se lidos da tela de sucesso/consulta.

## Entrada de dados
O usuário cola linhas: `data | CPF/CNPJ | nome | CEP | endereço | descrição do serviço | valor`. A data é a **competência**
(use exatamente a informada, ex. 28/09/2026). Nunca mude a competência para a data de hoje.

## Parâmetros por cliente (confirmar quando for cliente novo)
| Cliente | CNPJ | Serviço | NBS | Regime | Alíquota SN |
|---|---|---|---|---|---|
| R & J ODONTOLOGIA LTDA (Simples, ME/EPP, Porto Alegre) | 41.629.375/0001-00 | 04.12.01 Odontologia | 123012300 Serviços odontológicos | opção 1 (federais e municipal pelo SN) | **6,00%** |
Para cliente novo, **pergunte**: CNPJ do prestador, município da prestação, código de tributação, NBS, regime de apuração e a alíquota do Simples. Não reaproveite os da R & J. (Os exemplos de código/município abaixo, como "Porto Alegre" e "odontologia", são da R & J e só ilustram o método.)
Descrição do serviço: a que o usuário mandar (ex.: "serviços odontológicos", "CONSULTA ODONTOLOGICA DE ROTINA"); se vier vazia na linha, use a do primeiro item.

## 1. Login e navegador
- O usuário loga (usuário/senha, certificado ou gov.br). **Eu nunca digito senha.** A sessão expira em poucas horas: se cair no login, peça para logar de novo.
- Use o Chrome via `mcp__claude-in-chrome__*`. Dois ou três navegadores podem estar conectados à extensão; teste qual está logado
  (`navigate` em `/EmissorNacional/` e veja se cai em `/Login` ou em `/Dashboard`). Se nenhum estiver, peça o login na aba aberta.
- Se a aba travar (CDP timeout), feche e abra outra (`tabs_context_mcp{createIfEmpty:true}`).
- **Entre SEMPRE por `https://www.nfse.gov.br/EmissorNacional/DPS/Pessoas/NovaNFSe`** (equivale a Nova NFS-e > Emissão completa).
  Abrir `/DPS/Pessoas` direto frequentemente deixa a consulta do Simples Nacional sem carregar e o servidor rejeita no Avançar
  ("Não foi possível recuperar as informações do contribuinte no Simples Nacional").

## 2. Instabilidade do portal (muito comum)
- Respostas 503 intermitentes: páginas vêm sem CSS/JS, formulário vazio. **Confira antes de preencher**: `typeof window.jQuery==='function'`
  e `document.styleSheets.length>=3`. Se não, `location.reload()` e repita (às vezes 4 a 6 vezes). Espere ~9 s após cada carga.
- Nunca preencha em página quebrada (campos desabilitados, sem jQuery). Não force por script se faltar dado do emitente.
- Cada `javascript_tool` precisa terminar em < 45 s; quebre em chamadas menores. `return` no topo do script dá `undefined`; termine com a expressão.
- `screenshot`, `find` e `read_page` podem travar; prefira ler o DOM por JS. Cliques em botões: `getElementById(...).click()` costuma servir,
  mas rádios/checkboxes estilizados exigem clicar no `label` ou usar `prop('checked',true).trigger('click').trigger('change')`.

## 3. Etapa PESSOAS (`/DPS/Pessoas`)
Receitas (jQuery da página; use sempre `const $=window.jQuery`):
```js
$('input[name=PreencherInfoIBSCBS][value="0"]').prop('checked',true).trigger('click').trigger('change');   // IBS/CBS = Não
$('#DataCompetencia').val('28/09/2026').trigger('change').trigger('blur');                                  // competência
try{$('input[name=TipoEmitente][value="1"]').prop('checked',true).trigger('click').trigger('change');}catch(e){} // Prestador (a exceção é do script deles; ignore)
await sleep(5000);   // carrega Prestador_Inscricao, Prestador_Nome e #txtOpcaoSN
```
- **Valide o emitente antes de seguir**: `#Prestador_Inscricao` = CNPJ esperado e `#txtOpcaoSN` contém "Optante". Se `txtOpcaoSN` vier vazio ou "NENHUM",
  recarregue e repita; não avance assim (o servidor devolve erro e a tela volta para Pessoas).
- Não clique no rádio "Tomador/Intermediário": abre aviso "Mensagem do Sistema" (feche em FECHAR) e atrapalha.
- Compra governamental = Não: `$('input[name=EhCompraGovernamental][value="0"]')...` e regime: `$('#SimplesNacional_RegimeApuracaoTributosSN').val('1').trigger('change')`
  (o campo de regime só aparece depois que o emitente Simples carrega).
- **Tomador: antes de digitar o CPF/CNPJ, abra o histórico** (ícone de grupo ao lado do campo, `#btn_Tomador_Inscricao_historico`) e procure o tomador
  pelo documento nas linhas `.modal tr`. Se existir: clique no `label` da linha (o rádio é escondido; `label.click()`), confira que só uma linha ficou marcada
  e clique em Importar (`.modal button` com texto Importar). Endereço e nome vêm do cadastro: **use o cadastro como está**
  (CEP/nome podem diferir do pedido; avise no resumo final, não troque sem o usuário mandar).
- Se **não** estiver no histórico: preencha `#Tomador_Inscricao` (CPF/CNPJ), `#btn_Tomador_Inscricao_pesquisar`, depois `#Tomador_Nome` (maiúsculas),
  marque "Informar endereço" (`label[for=Tomador_InformarEndereco]` ou o checkbox), `#Tomador_EnderecoNacional_CEP` + `#btn_Tomador_EnderecoNacional_CEP`
  (repita se não preencher logradouro; pode falhar na 1ª vez), depois `#Tomador_EnderecoNacional_Numero` e `..._Complemento`. O CEP completa logradouro/bairro/município.
- Avançar: `[...document.querySelectorAll('button,input[type=submit]')].find(x=>/Avançar/i.test(x.innerText||x.value)).click()`.
  (O botão "Exibir detalhes do emitente" também é submit; selecione pelo texto "Avançar".)

## 4. Etapa SERVIÇO (`/DPS/Servico`)
Município e Código de Tributação Nacional são **Select2 com busca remota** (a página precisa estar completa, `$.fn.select2` existente):
```js
$('#LocalPrestacao_CodigoMunicipioPrestacao').select2('open'); await sleep(500);
$(document.querySelector('.select2-search__field')).val('Porto Alegre').trigger('input').trigger('keyup');
// esperar aparecer a opção exata 'Porto Alegre/RS' (evita Porto Alegre do Norte/MT etc.), então:
opcao.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));
```
Mesmo para `#ServicoPrestado_CodigoTributacaoNacional` digitando `odontologia` e escolhendo a opção que começa com o código (ex. `04.12.01`).
Depois de escolher o código o portal mostra "Por favor, aguarde": espere `$.active===0` (até ~20 s) + 2,5 s. Se ficar preso, recarregue a etapa e refaça.
Depois: imunidade/exportação "Não" (`input[name$=HaExportacaoImunidadeNaoIncidencia][value="0"]`), `#ServicoPrestado_CodigoNBS` (`.val('123012300').trigger('change')`),
`#ServicoPrestado_Descricao`. Se a opção de NBS não for a conhecida, procure nas `options` por texto e **confirme com o usuário**.
Cada select2 (município, código) em chamada separada para ficar sob 45 s.

## 5. Etapa VALORES (`/DPS/Tributacao`)
```js
$('#Valores_ValorServico').val('450,00').trigger('input').trigger('change').trigger('blur');        // formato BR
$('#ValorTributos_AliquotaSN').val('6,00').trigger('input').trigger('change').trigger('blur');      // "Alíquota no Simples Nacional*" (observado em 02/10/2026: vem 15,50 por padrão; vale a alíquota informada para o cliente)
$('input[name="ISSQN.HaRetencao"][value="0"]').prop('disabled',false).prop('checked',true).trigger('click').trigger('change'); // sem retenção (obrigatório)
```
Os campos ISSQN (alíquota, base, valor) são só leitura (ISS apurado pelo Simples). A alíquota que o usuário pede ("6%") é a do **campo do Simples Nacional**.
Valor ≠ do pedido = erro grave; releia na tela de conferência.

## 6. Etapa EMITIR NFS-e (`/DPS/EmitirNFSe`)
Leia o texto da página e confira: competência, CNPJ do emitente, tomador (CPF/nome/endereço), código, NBS, descrição, valor, retenção "Não".
Monte o resumo para o usuário (primeira nota) ou valide contra o pedido (demais). Emitir: `document.getElementById('btnProsseguir').click()`.
Sucesso: página `/DPS/NFSe` com "A NFS-e foi gerada com sucesso" e **Chave de Acesso (50 dígitos)**. Registre chave, tomador e valor a cada nota.
Em seguida repita pela entrada `NovaNFSe` para a próxima (cada nota = fluxo novo; **não reutilize rascunhos antigos** nem deixe rascunhos duplicados:
cada tentativa interrompida cria um em Notas > Rascunhos; prefira retomar o rascunho existente do mesmo tomador/data, e avise o usuário dos que sobrarem).
Excluir rascunho é exclusão definitiva: **não faço; oriente o usuário** (Notas > Rascunhos > menu da linha > excluir).

## 7. Baixar os PDFs (DANFSe)
- `Notas > Emitidas > Download DANFS-e` dá **403 para o meu navegador**; não insista nem tente contornar.
- **Consulta Pública** (`https://www.nfse.gov.br/consultapublica`, "Por Chave de Acesso"): preencho `#ChaveAcesso` (input + change) e **o usuário resolve o hCaptcha
  ("Sou humano") e clica Consultar**. Eu nunca resolvo/contorno CAPTCHA, mesmo com pedido ou autorização. Diga o passo a passo simples ao usuário.
- Com o resultado na tela, clique em "Download DANFS-e" **uma vez** (cliques repetidos fazem o Chrome pedir permissão de vários downloads e travar o arquivo).
  O Chrome do usuário salva direto na pasta de download configurada (no caso da R & J, na pasta fiscal do cliente) com o nome da chave.
  Confira com PowerShell (`Test-Path`, tamanho, cabeçalho `%PDF-` e fim `%%EOF`) só nessa pasta, sem varrer o perfil.
- Depois "Nova Pesquisa" e a próxima chave. Se o clique não gerar arquivo, peça ao usuário para clicar e, se aparecer aviso de download bloqueado, permitir.
- Renomeie para `NOME DO TOMADOR - <chave>.pdf` (o usuário gosta assim) e depois use **enviar-notas-digisac**.

## Final de lote: relatório ao usuário
Tabela com tomador, valor, chave; o que foi cadastrado do zero x importado; divergências de cadastro (CEP/nome); rascunhos que sobraram; pendências.

## Confirmações e limites
1. Antes de emitir a primeira nota do lote (resumo). 2. Divergência entre tela e pedido: parar e perguntar.
3. CAPTCHA, login e senha são do usuário. 4. Nada de excluir rascunhos nem cancelar nota sem o usuário fazer/pedir explicitamente.

## Emissão por API (alternativa ao portal; validada em 30/10/2026 com o STUDIO A+)
Quando o usuário pedir "emita via API" e o certificado A1 do prestador estiver instalado no Windows (`integracoes\instalar_certificado.ps1`, repositório `Cert:\CurrentUser\My`; o .pfx é não-exportável para o Python, então tudo roda em PowerShell/.NET):
- Script: `ROTINAS CONTÁBIL\integracoes\emitir_nfse_api.ps1`. **Sem `-Enviar` só gera e assina o DPS** (conferência); com `-Enviar` faz o POST (irreversível). Parâmetros: `-Thumbprint` (escolha o certificado **vigente**; a loja pode ter vários do mesmo CNPJ, vencidos), prestador, município IBGE, tomador (CNPJ, nome, cMun, CEP, logradouro, número, bairro), `-CTribNac` (6 díg.), `-Nbs` (9 díg.), `-Descricao`, `-Valor` (ponto), `-AliquotaSN`, `-Competencia yyyy-MM-dd`, `-NumeroDps`.
- Passe textos com acento via `[char]0xED` etc. (o PS 5.1 lê o .ps1/linha de comando em ANSI e gera "BrasÃ­lia").
- Endpoint: `POST https://sefin.nfse.gov.br/sefinnacional/nfse` (produção restrita: `sefin.producaorestrita.nfse.gov.br`), mTLS com o certificado, corpo `{"dpsXmlGZipB64": gzip(base64(DPS assinado))}`. Sucesso = HTTP 201 com `chaveAcesso` e `nfseXmlGZipB64` (o script salva `<saida>_nfse.xml`; `cStat=100`, `nNFSe`).
- DPS v1.01: Id = `DPS`+cLocEmi(7)+`2`(CNPJ)+CNPJ(14)+série(5)+nDPS(15); Simples ME/EPP = `opSimpNac 3`, `regApTribSN 1`, `regEspTrib 0`; `tribISSQN 1`, `tpRetISSQN 1`; alíquota do SN em `totTrib/pTotTribSN`. Assinatura XMLDSig enveloped, c14n, RSA-SHA1/SHA1, `X509Data` no KeyInfo.
- **Erro E1229 "não está utilizando UTF-8"**: o XML enviado precisa começar com `<?xml version="1.0" encoding="UTF-8"?>` (o script já inclui).
- Série 1 / nDPS: se o prestador já emitiu pelo portal, use o próximo número livre (o servidor recusa duplicidade).
- NBS/código vêm do cartão CNPJ (atividade principal) e o usuário confirma; mesmo na API valem as regras de precisão e a confirmação antes do envio.
- DANFSe (PDF): `adn.nfse.gov.br/danfse/{chave}` deu 503 neste dia; a alternativa é a Consulta Pública (hCaptcha do usuário), seção 7.
- Parâmetros já usados: STUDIO A+ ARQUITETURA DE INTERIORES LTDA (47.030.954/0001-00, Joinville 4209102, Simples, 6,00%): cTribNac 070104, NBS 114021100, descrição "Comissão".
