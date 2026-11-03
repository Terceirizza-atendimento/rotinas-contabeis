# Guarda as credenciais da API do Gclick em variáveis de ambiente (só neste usuário do Windows).
# Nada é gravado em arquivo e o segredo não aparece na tela.
function Ler($rotulo, $secreto) {
    if ($secreto) {
        $s = Read-Host $rotulo -AsSecureString
        $p = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
        $v = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($p)
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p)
    } else { $v = Read-Host $rotulo }
    return $v.Trim().Trim('"').Trim("'")
}
$id  = Ler "ID de cliente" $false
$sec = Ler "Segredo de cliente (nao aparece)" $true
if ($id.Length -lt 10 -or $sec.Length -lt 10) { Write-Host "Valores muito curtos." -ForegroundColor Red; Read-Host "ENTER"; exit 1 }
[Environment]::SetEnvironmentVariable('GCLICK_CLIENT_ID', $id, 'User')
[Environment]::SetEnvironmentVariable('GCLICK_CLIENT_SECRET', $sec, 'User')
Write-Host "Pronto! Credenciais salvas. Abra um novo terminal e avise no chat." -ForegroundColor Green
Read-Host "ENTER para fechar"
