# Emite as notas de INTEGRACOES\dados\notas_BIOMEDICA.csv pela API do Emissor Nacional e envia pelo Digisac.
# Passo a passo: 1) simulacao  2) digitar EMITIR  3) baixa PDFs e arquiva no Drive  4) digitar ENVIAR  5) fecha chamado (s/N)
# Nova rodada: edite o notas_BIOMEDICA.csv (data;documento;nome;cep;numero;complemento;descricao;valor[;logradouro;bairro])
# Notas ja emitidas sao puladas (sem duplicar). Se parar no meio: rode com -Retomar
# Primeira vez neste PC: rode configurar_certificado.ps1 (pasta INTEGRACOES) com a sigla BIOMEDICA.
# Arquivo mantido em ASCII puro (o PowerShell 5.1 le UTF-8 sem BOM como ANSI e quebra o nome da pasta).
param([switch]$Retomar)
$raiz = Split-Path $PSScriptRoot -Parent
$dir = (Get-ChildItem -LiteralPath $raiz -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'fluxo_nfse.py') } | Select-Object -First 1).FullName
if (-not $dir) { Write-Host "Pasta INTEGRACOES nao encontrada em $raiz" -ForegroundColor Red; Read-Host "ENTER"; exit 1 }
Set-Location -LiteralPath $dir
$a = @('-I','fluxo_nfse.py','BIOMEDICA'); if ($Retomar) { $a += '--retomar' }
python @a
Read-Host "ENTER para fechar"
