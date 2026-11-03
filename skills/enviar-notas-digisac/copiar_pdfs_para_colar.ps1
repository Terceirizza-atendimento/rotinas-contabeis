# Copia PDFs de uma pasta para a área de transferência do Windows (como Ctrl+C no Explorer),
# para colar com Ctrl+V na caixa de mensagem do Digisac.
# Uso: .\copiar_pdfs_para_colar.ps1 -Pasta "G:\...\2026" [-Filtro "SILVANA*"] [-Ordem SILVANA,CLINICA,LETICIA]
param(
    [Parameter(Mandatory=$true)][string]$Pasta,
    [string]$Filtro = '*.pdf',
    [string[]]$Ordem
)

if (-not (Test-Path -LiteralPath $Pasta)) { Write-Error "Pasta não encontrada: $Pasta"; exit 1 }

$arqs = if ($Ordem) {
    foreach ($n in $Ordem) { Get-ChildItem -LiteralPath $Pasta -File -Filter "$n*.pdf" }
} else {
    Get-ChildItem -LiteralPath $Pasta -File -Filter $Filtro
}

# Só PDFs íntegros (começam com %PDF e terminam com %%EOF)
$ok = foreach ($f in $arqs) {
    $b = [System.IO.File]::ReadAllBytes($f.FullName)
    $ini = [System.Text.Encoding]::ASCII.GetString($b[0..4])
    $fim = [System.Text.Encoding]::ASCII.GetString($b[($b.Length-12)..($b.Length-1)])
    if ($ini -eq '%PDF-' -and $fim -match '%%EOF') { $f } else { Write-Warning "Ignorado (PDF inválido): $($f.Name)" }
}
if (-not $ok) { Write-Error "Nenhum PDF válido encontrado."; exit 1 }

Set-Clipboard -Path ($ok | ForEach-Object { $_.FullName })
Add-Type -AssemblyName System.Windows.Forms
$n = [System.Windows.Forms.Clipboard]::GetFileDropList().Count
Write-Host "$n arquivo(s) na área de transferência:"
$ok | ForEach-Object { Write-Host " - $($_.Name)" }
