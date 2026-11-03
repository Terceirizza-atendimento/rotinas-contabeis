---
name: sieg-baixar-diagnosticos
description: Baixa do SIEG (iris.sieg.com) os Diagnósticos Fiscais e as Certidões dos clientes com débito, organiza em pastas datadas e VALIDA os arquivos com um script (CNPJ, data da consulta, validade, certidão positiva/negativa, arquivos que faltaram no ZIP). Use quando pedirem para "baixar diagnósticos/certidões do SIEG", "ver quem está com débito" ou "validar os arquivos baixados". NÃO envia nada ao cliente e não mexe no Gclick/Digisac.
---

# Baixar e validar Diagnóstico Fiscal + Certidões do SIEG

Escopo: **só baixar, organizar e validar**. Envio ao cliente, Gclick e Digisac ficam fora (a pessoa faz ou usa outra skill).

## Regras de precisão (valem sempre)
- Só afirmar débito/regularidade com o que o **PDF ou a planilha desta rodada** mostram. Nada de "o cliente costuma ter débito" nem reaproveitar rodada antiga.
- Arquivo que é página de erro/captcha **não é certidão**: avisar, não dizer regular nem irregular. O script marca como `ERRO` ou `REVISAR`.
- Tipo "Outros" na planilha Visão Geral = consulta que falhou, não é débito.
- Documento com CNPJ diferente do cliente da pasta: parar e avisar.
- Qualquer tela diferente do descrito, erro do SIEG ou dúvida: **parar e avisar a pessoa**; não improvisar.
- Nunca digitar senha nem clicar em "Entrar" pela pessoa. Ela faz o login.

## Pré-requisitos (checar antes de começar)
1. Python 3 instalado (`python --version` no terminal). Se faltar, pedir para a pessoa instalar em python.org (marcar "Add to PATH").
2. Leitor de PDF: ter `pdftotext` (Poppler) **ou** instalar `pypdf` (`python -m pip install pypdf`). O script avisa se faltar.
3. Claude in Chrome ativo (o navegador do app Claude bloqueia o download do SIEG).
4. Pasta de trabalho: perguntar à pessoa onde guardar (ex.: `Documentos\DIAGNOSTICO FISCAL`). Chamar de `<PASTA>` abaixo. O caminho do script é `scripts\validar_sieg.py` dentro da pasta desta skill (`%USERPROFILE%\.claude\skills\sieg-baixar-diagnosticos`).

## Passo 1: baixar no SIEG (Claude in Chrome)
Os elementos de tela mudam; localize cada botão por `find`/screenshot, nunca por coordenada antiga.
1. A pessoa entra no SIEG e faz login. Esperar ela avisar.
2. **Certidões**: abrir `https://iris.sieg.com/Certidoes?Filtro=visao-geral`.
   - "Adicionar filtro" > Situação > **Irregular**.
   - Clicar **"Baixar Todos"** (ZIP de certidões `Certidoes_...zip`).
   - Clicar **"Exportar Todos"** (planilha `Certidao-VisaoGeral-...xlsx`).
3. **Diagnóstico Fiscal**: abrir `https://iris.sieg.com/DiagnosticoFiscal`, mesmo filtro (Situação > Irregular) e **"Baixar Todos"** (ZIP `Diagnóstico_...zip`).
4. Só clientes COM débito interessam; regulares não entram.
5. Conferir na pasta Downloads que os 3 arquivos chegaram.

## Passo 2: organizar
```
python -I "<skill>\scripts\validar_sieg.py" receber --pasta "<PASTA>"
```
Pega os 3 arquivos recentes de Downloads, extrai em `<PASTA>\Diagnosticos_AAAA-MM-DD` e `<PASTA>\Certidoes_AAAA-MM-DD` (nunca sobrescreve pasta existente) e copia a planilha. Se faltar algum, ele avisa.

## Passo 3: validar (obrigatório antes de usar os arquivos)
```
python -I "<skill>\scripts\validar_sieg.py" validar --pasta "<PASTA>"
```
O que o script confere:
- **MANIFESTO.txt** dos ZIPs: arquivos que o SIEG não colocou no ZIP (baixar de novo).
- **Diagnóstico**: é mesmo um diagnóstico? CNPJ do arquivo = CNPJ da pasta = CNPJ dentro do PDF (ignora o CNPJ do certificado digital do escritório); data/hora da consulta (aviso se mais velha que 10 dias, ajustável com `--max-idade`); se há pendência (Receita/PGFN) e quais; se há parcelamento (aviso).
- **Certidões** (federal, estadual, municipal, trabalhista, FGTS): NEGATIVA / POSITIVA / POSITIVA COM EFEITOS DE NEGATIVA / REVISAR / ERRO, validade e se está vencida, CNPJ do PDF.
- **Cruzamento com a Visão Geral**: irregular federal sem diagnóstico baixado; diagnóstico com pendência que a planilha não mostra; tipo "Outros".
- Saída: relatório na tela e arquivos `resumo_<rodada>.csv` e `.txt` em `<PASTA>`. Código de saída 1 se houver ERRO.

## Passo 4: relatar à pessoa
Mostrar, em linguagem simples:
1. Quantos diagnósticos/certidões foram baixados e quantos clientes têm pendência.
2. **ERROS** primeiro (arquivos que faltaram, CNPJ divergente, PDF inválido): dizer o que precisa ser refeito.
3. **AVISOS** (consulta antiga, parcelamento, não classificado): listar e dizer que precisam de conferência humana.
4. Lista de clientes com pendência federal (diagnóstico) e de clientes com certidão positiva em outro âmbito.
5. Onde ficaram os arquivos e o `resumo_*.csv`.
Não afirmar valores de débito, multa ou juros: valores só como estão no PDF, e o script não os soma.

## Limites conhecidos do script
- Classifica por texto dos PDFs. Layout novo de certidão (outro estado/município) cai em `REVISAR`: abrir o PDF e conferir; não inferir.
- Não valida assinatura digital nem autenticidade do documento.
- Se a consulta da Visão Geral falhou para um cliente (tipo "Outros"), é preciso refazer a consulta no SIEG.
