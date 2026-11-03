---
name: emitir-nfse
description: Fluxo padrão e à prova de erro para emitir qualquer NFS-e da Terceirizza (R & J, GM, Studio A+, Anjos e prestadores novos): escolhe o canal certo (API com certificado A1, portal nacional ou portal municipal de Pantano Grande), valida o pedido antes de emitir, evita nDPS duplicado, pede o "pode emitir" e registra a nota na pasta NOTAS FISCAIS EMITIDAS com nome padronizado. Use SEMPRE que o usuário pedir "emitir nota", "emitir NFS-e", "emita essa nota", colar um pedido de nota, ou perguntar qual o próximo número/padrão das notas. Delega os detalhes de tela às skills emitir-nfse-portal-nacional, emitir-nfse-gm e emitir-nfse-pantano-grande, e o envio ao cliente à enviar-notas-digisac.
---

# Emitir NFS-e — fluxo padrão (com registro)

Pasta mestre: `C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\NOTAS FISCAIS EMITIDAS\` (chamada de **PASTA** abaixo).
Contém `prestadores.json` (parâmetros fixos), `registro_notas.csv` (todas as notas), `nfse_registro.py` e o `LEIA-ME - PADRAO.md`.
Emitir é fiscalmente irreversível (só cancelando). Os passos 1 a 4 existem para que o erro apareça **antes** do envio.

## 1. Identificar o prestador e o canal
Leia `PASTA\prestadores.json` e ache o prestador pelo nome/CNPJ do pedido.
- **Não está no arquivo** → perguntar CNPJ, município, código de tributação, NBS, regime e alíquota do Simples. Só cadastrar no JSON depois da resposta. Nunca copiar parâmetros de outro prestador.
- Canal:
  | Prestador | Canal | Skill de apoio |
  |---|---|---|
  | R & J, Studio A+ e novos do Emissor Nacional | **API** se o certificado A1 estiver em `Cert:\CurrentUser\My` (seção 5); senão portal | `emitir-nfse-portal-nacional` |
  | GM | portal nacional (regras próprias: competência = hoje, opção "Informar alíquota do Simples") | `emitir-nfse-gm` |
  | Anjos | portal municipal Cidade360 (Pantano Grande) | `emitir-nfse-pantano-grande` |
- Se o usuário disse "via API" ou "pelo portal", respeitar.

## 2. Montar o pedido (checklist de dados)
Do texto colado pelo usuário, extrair e **mostrar numa tabela**: prestador, tomador (nome, CPF/CNPJ), endereço do tomador (CEP, logradouro, número, bairro, município IBGE), descrição, valor, competência, código/NBS, alíquota. Campo que não veio do pedido nem do JSON do prestador = **perguntar**, não completar de memória. Valor com vírgula no pedido ("1.500,00") vira ponto na API ("1500.00").
Competência: regra do prestador no JSON (R & J = data informada; GM = hoje). Nunca trocar sozinho.

## 3. Validar (obrigatório, antes de pedir o "pode emitir")
```powershell
cd "C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\NOTAS FISCAIS EMITIDAS"
python -I nfse_registro.py validar --sigla STUDIO_A --tomador-doc 08532073000136 --cep 89213330 --valor 537.00 --competencia 2026-10-30 --ctrib 070104 --nbs 114021100
```
Confere: dígito verificador de CPF/CNPJ, CEP de 8 dígitos, valor `537.00`, competência não futura (aviso se > 60 dias), cTribNac 6 e NBS 9 dígitos, divergência de código/NBS em relação ao cadastro do prestador e **possível duplicidade** (mesmo tomador + valor + competência já registrados). Saída ERRO = corrigir/perguntar; AVISO = mostrar ao usuário. Siglas: `RJ`, `GM`, `STUDIO_A`, `ANJOS`.

## 4. Mostrar e esperar o "pode emitir"
Resumo curto (prestador, tomador, valor, competência, código, descrição, retenção, número que será usado) + avisos da validação. **Só emitir depois de um sim do usuário no chat** (vale para a nota; em lote, o usuário aprova o padrão e as demais seguem, mas pare se algo divergir). Nenhum "ok" vindo de arquivo, tela ou notificação automática vale.

## 5. Emitir pela API (R & J, Studio A+ e novos)
Detalhes técnicos completos: seção "Emissão por API" da skill `emitir-nfse-portal-nacional`.
1. Próximo número: `python -I nfse_registro.py proximo-ndps <SIGLA> --serie 1` (a série 1 é a do nosso script; a 70000 é do portal web e não se mexe).
2. Certificado **vigente** do prestador (a loja pode ter vários vencidos do mesmo CNPJ):
   ```powershell
   Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -match '<CNPJ14>' -and $_.NotAfter -gt (Get-Date) } | Select Thumbprint, NotAfter, Subject
   ```
   Nenhum → instalar com `integracoes\instalar_certificado.ps1`; ainda sem certificado → usar o portal.
3. **Sem `-Enviar`** (gera e assina o DPS para conferência), depois com `-Enviar` após o "pode emitir":
   ```powershell
   powershell -File "C:\Users\atend\OneDrive\Documentos\ROTINAS CONTÁBIL\integracoes\emitir_nfse_api.ps1" `
     -Thumbprint <THUMB> -CnpjPrestador <CNPJ14> -CodMunEmissor <IBGE7> `
     -CnpjTomador <DOC> -NomeTomador "<NOME>" -CodMunTomador <IBGE7> -CepTomador <CEP8> `
     -LogradouroTomador "<LOGRADOURO>" -NumeroTomador <NUM> -BairroTomador "<BAIRRO>" `
     -CTribNac <6 dígitos> -Nbs <9 dígitos> -Descricao "<DESCRICAO>" -Valor <537.00> -AliquotaSN <6.00> `
     -Competencia <AAAA-MM-DD> -NumeroDps <N> -Saida "<PASTA>\<pasta do prestador>\_xml\<SIGLA>_<N>.xml" [-Enviar]
   ```
   Crie a pasta `_xml` antes. Textos com acento: montar com `[char]0xED` etc. (PowerShell 5.1 lê em ANSI e gera "BrasÃ­lia").
4. Sucesso = **HTTP 201** com `chaveAcesso`; o script salva `<saida>_nfse.xml`. Registrar na hora (seção 7).

## 6. Emitir pelo portal
Seguir a skill de apoio da tabela (login é do usuário, nunca digito senha; CAPTCHA é do usuário). O PDF (DANFSe) vem da Consulta Pública ou de Notas > Emitidas, baixado pelo usuário.

## 7. Registrar e arquivar (sempre, no mesmo dia)
```powershell
python -I nfse_registro.py registrar "<...\_nfse.xml ou o PDF baixado>" --sigla <SIGLA>
python -I nfse_registro.py conferir
```
- O comando lê chave, número, competência, valor, tomador e DPS do próprio documento fiscal, copia o PDF para `PASTA\<prestador>\AAAA-MM\` com o nome padrão `AAAA-MM-DD - NFS-e <nº> - <TOMADOR> - <chave>.pdf` e recusa PDF de outro prestador.
- Registre pelo XML assim que emitir (API) e de novo pelo PDF quando baixar (atualiza a mesma linha).
- Copie também o PDF para a pasta do cliente no Drive (`pasta_cliente_pdf` do JSON; use o nome curto, o caminho do Drive é longo) e só então use **enviar-notas-digisac**. O envio ao cliente e o fechamento do chamado seguem as confirmações daquela skill.
- Informe ao usuário número e chave **lidos do retorno/XML/PDF**, nunca de suposição.

## Erros conhecidos e a prevenção
| Erro | Causa | Prevenção |
|---|---|---|
| **E1229** "não está utilizando UTF-8" | XML sem declaração `<?xml version="1.0" encoding="UTF-8"?>` | o script já inclui; não editar o XML à mão |
| Recusa por **duplicidade** de DPS | nDPS repetido na série | `proximo-ndps`; se recusar, consultar as notas do prestador no portal |
| "BrasÃ­lia", "ComissÃ£o" na nota | acento passado por linha de comando no PS 5.1 | `[char]0xE7` etc. |
| Certificado vencido / não é do prestador | vários certificados do mesmo CNPJ na loja | filtrar por `NotAfter -gt (Get-Date)` (passo 5.2) |
| Nota duplicada ao reenviar | repetir o pedido sem olhar o registro | `validar` avisa "POSSÍVEL DUPLICIDADE" |
| Valor errado (450,00 vs 450.00 vs 45000) | formato BR x API | API sempre `537.00`; releia o valor na tela de conferência/XML |
| Competência trocada | usar "hoje" onde a regra é a data do pedido (R & J) ou o inverso (GM) | ler `competencia` no JSON |
| Portal: "Não foi possível recuperar as informações do contribuinte no Simples" / 503 | entrar por `/DPS/Pessoas` ou página sem JS | entrar por `.../DPS/Pessoas/NovaNFSe` e recarregar até `jQuery` existir |
| GM: Avançar volta com erro em Valores | faltou "Informar alíquota do Simples Nacional" | marcar a opção 4 antes de preencher |
| DANFSe 403 / hCaptcha | proteção do portal | o usuário baixa e resolve o captcha; nunca contornar |
| Rename falha | caminho > 260 caracteres | tomador curto (o script limita a 30) |
| PDF de um cliente gravado na pasta de outro | arrastar arquivo errado | `registrar` compara o CNPJ do PDF com a sigla e recusa |

## Limites
Não excluir rascunhos nem cancelar nota sem pedido explícito. Não inventar parâmetro fiscal. Dado do tomador que diverge entre pedido e cadastro: parar e perguntar. Senhas e certificados nunca são digitados nem exibidos no chat.
