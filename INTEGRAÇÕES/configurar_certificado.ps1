# Guarda caminho e senha de um certificado A1 (.pfx) em variáveis de ambiente (só neste usuário do Windows).
# Uso: informe a sigla do cliente (ex.: RJ) -> cria NFSE_PFX_RJ e NFSE_PFX_SENHA_RJ.
# A senha não aparece na tela nem é gravada em arquivo.
$sigla = (Read-Host "Sigla do cliente (ex.: RJ)").Trim().ToUpper()
$caminho = (Read-Host "Caminho completo do .pfx").Trim().Trim('"')
if (-not (Test-Path -LiteralPath $caminho)) { Write-Host "Arquivo nao encontrado." -ForegroundColor Red; Read-Host "ENTER"; exit 1 }
$s = Read-Host "Senha do certificado (nao aparece)" -AsSecureString
$p = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
$senha = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($p)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p)
try {
    $c = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($caminho, $senha)
    Write-Host "Certificado valido: $($c.Subject)  (vence em $($c.NotAfter.ToString('dd/MM/yyyy')))" -ForegroundColor Green
} catch { Write-Host "Senha incorreta ou arquivo invalido." -ForegroundColor Red; Read-Host "ENTER"; exit 1 }
[Environment]::SetEnvironmentVariable("NFSE_PFX_$sigla", $caminho, 'User')
[Environment]::SetEnvironmentVariable("NFSE_PFX_SENHA_$sigla", $senha, 'User')
Write-Host "Pronto! Salvo para $sigla. Abra um novo terminal e avise no chat." -ForegroundColor Green
Read-Host "ENTER para fechar"
