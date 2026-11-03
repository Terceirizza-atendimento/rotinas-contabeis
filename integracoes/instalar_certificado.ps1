# Instala um certificado A1 (.pfx) no repositório PESSOAL do seu usuário do Windows, para o Chrome oferecê-lo
# nos logins por certificado (gov.br, e-CAC, Regularize). Você roda; a senha é digitada aqui e não aparece na tela.
# Para tirar depois:  .\instalar_certificado.ps1 -Remover
param([switch]$Remover)

if ($Remover) {
    $c = Get-ChildItem Cert:\CurrentUser\My | Select-Object Subject, Thumbprint, NotAfter
    $c | Format-Table -AutoSize
    $t = (Read-Host "Cole o Thumbprint do certificado a remover").Trim()
    if ($t) { Remove-Item "Cert:\CurrentUser\My\$t" -DeleteKey -Confirm:$true; Write-Host "Removido." -ForegroundColor Green }
    Read-Host "ENTER para fechar"; exit
}

$caminho = (Read-Host "Caminho completo do .pfx").Trim().Trim('"')
if (-not (Test-Path -LiteralPath $caminho)) { Write-Host "Arquivo nao encontrado." -ForegroundColor Red; Read-Host "ENTER"; exit 1 }
$senha = Read-Host "Senha do certificado (nao aparece)" -AsSecureString
try {
    $r = Import-PfxCertificate -FilePath $caminho -CertStoreLocation Cert:\CurrentUser\My -Password $senha -ErrorAction Stop
    Write-Host "Instalado: $($r.Subject)  (vence em $($r.NotAfter.ToString('dd/MM/yyyy')))" -ForegroundColor Green
    Write-Host "Feche o uso quando terminar: rode este script com -Remover para tirar o certificado do Windows." -ForegroundColor Yellow
} catch { Write-Host "Senha incorreta ou arquivo invalido." -ForegroundColor Red }
Read-Host "ENTER para fechar"
