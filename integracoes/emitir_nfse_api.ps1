# Emite NFS-e pela API do Emissor Nacional (sefin.nfse.gov.br) com o certificado A1 instalado no Windows (Cert:\CurrentUser\My).
# Sem -Enviar so gera e assina o DPS (arquivo em -Saida) para conferencia. Com -Enviar faz o POST (irreversivel em producao).
# Instalar o certificado antes: instalar_certificado.ps1. Producao restrita (testes): -Ambiente 2.
param(
    [Parameter(Mandatory)][string]$Thumbprint,
    [Parameter(Mandatory)][string]$CnpjPrestador,
    [Parameter(Mandatory)][string]$CodMunEmissor,        # IBGE (Joinville = 4209102)
    [Parameter(Mandatory)][string]$CnpjTomador,
    [Parameter(Mandatory)][string]$NomeTomador,
    [Parameter(Mandatory)][string]$CodMunTomador, [Parameter(Mandatory)][string]$CepTomador,
    [Parameter(Mandatory)][string]$LogradouroTomador, [Parameter(Mandatory)][string]$NumeroTomador,
    [Parameter(Mandatory)][string]$BairroTomador,
    [Parameter(Mandatory)][string]$CTribNac,             # 6 digitos, ex. 070104
    [string]$Nbs = '',                                   # 9 digitos, ex. 114021100 (opcional: so se o codigo exigir)
    [Parameter(Mandatory)][string]$Descricao,
    [Parameter(Mandatory)][string]$Valor,                # 537.00 (ponto decimal)
    [Parameter(Mandatory)][string]$AliquotaSN,           # 6.00
    [string]$Competencia = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$Serie = '00001', [Parameter(Mandatory)][long]$NumeroDps,
    [string]$ComplementoTomador = '',
    [int]$Ambiente = 1, [string]$Saida = "$env:TEMP\dps_assinado.xml", [switch]$Enviar
)
$ErrorActionPreference = 'Stop'
$cert = Get-Item "Cert:\CurrentUser\My\$Thumbprint"
if ($cert.Subject -notmatch $CnpjPrestador) { throw "Certificado nao e do prestador $CnpjPrestador" }
if ($cert.NotAfter -lt (Get-Date)) { throw "Certificado vencido" }

$id = 'DPS' + $CodMunEmissor + '2' + $CnpjPrestador + $Serie.PadLeft(5,'0') + ([string]$NumeroDps).PadLeft(15,'0')
$agora = (Get-Date).AddMinutes(-2).ToString("yyyy-MM-dd'T'HH:mm:ssK")
$cpl = if ($ComplementoTomador) { "<xCpl>$ComplementoTomador</xCpl>" } else { '' }
$nome = [Security.SecurityElement]::Escape($NomeTomador)
$nbsXml = if ($Nbs) { "<cNBS>$Nbs</cNBS>" } else { '' }
$xml = @"
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.01"><infDPS Id="$id"><tpAmb>$Ambiente</tpAmb><dhEmi>$agora</dhEmi><verAplic>terceirizza1.0</verAplic><serie>$([int]$Serie)</serie><nDPS>$NumeroDps</nDPS><dCompet>$Competencia</dCompet><tpEmit>1</tpEmit><cLocEmi>$CodMunEmissor</cLocEmi><prest><CNPJ>$CnpjPrestador</CNPJ><regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN><regEspTrib>0</regEspTrib></regTrib></prest><toma><CNPJ>$CnpjTomador</CNPJ><xNome>$nome</xNome><end><endNac><cMun>$CodMunTomador</cMun><CEP>$CepTomador</CEP></endNac><xLgr>$LogradouroTomador</xLgr><nro>$NumeroTomador</nro>$cpl<xBairro>$BairroTomador</xBairro></end></toma><serv><locPrest><cLocPrestacao>$CodMunEmissor</cLocPrestacao></locPrest><cServ><cTribNac>$CTribNac</cTribNac><xDescServ>$([Security.SecurityElement]::Escape($Descricao))</xDescServ>$nbsXml</cServ></serv><valores><vServPrest><vServ>$Valor</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun><totTrib><pTotTribSN>$AliquotaSN</pTotTribSN></totTrib></trib></valores></infDPS></DPS>
"@
Add-Type -AssemblyName System.Security
$doc = New-Object Xml.XmlDocument; $doc.PreserveWhitespace = $true; $doc.LoadXml($xml.Trim())
$sx = New-Object Security.Cryptography.Xml.SignedXml($doc)
$sx.SigningKey = [Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$sx.SignedInfo.CanonicalizationMethod = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
$sx.SignedInfo.SignatureMethod = 'http://www.w3.org/2000/09/xmldsig#rsa-sha1'
$ref = New-Object Security.Cryptography.Xml.Reference("#$id"); $ref.DigestMethod = 'http://www.w3.org/2000/09/xmldsig#sha1'
$ref.AddTransform((New-Object Security.Cryptography.Xml.XmlDsigEnvelopedSignatureTransform))
$ref.AddTransform((New-Object Security.Cryptography.Xml.XmlDsigC14NTransform))
$sx.AddReference($ref)
$ki = New-Object Security.Cryptography.Xml.KeyInfo; $ki.AddClause((New-Object Security.Cryptography.Xml.KeyInfoX509Data($cert))); $sx.KeyInfo = $ki
$sx.ComputeSignature()
[void]$doc.DocumentElement.AppendChild($doc.ImportNode($sx.GetXml(), $true))
$final = '<?xml version="1.0" encoding="UTF-8"?>' + $doc.OuterXml   # sem a declaracao o SEFIN devolve E1229
[IO.File]::WriteAllText($Saida, $final, (New-Object Text.UTF8Encoding($false)))
Write-Host "DPS assinado: $Saida  (Id $id)"
if (-not $Enviar) { Write-Host "Nada enviado (falta -Enviar)."; return }

$ms = New-Object IO.MemoryStream
$gz = New-Object IO.Compression.GZipStream($ms, [IO.Compression.CompressionMode]::Compress); $b = [Text.Encoding]::UTF8.GetBytes($final); $gz.Write($b,0,$b.Length); $gz.Close()
$corpo = (@{ dpsXmlGZipB64 = [Convert]::ToBase64String($ms.ToArray()) } | ConvertTo-Json -Compress)
$host_ = if ($Ambiente -eq 1) { 'sefin.nfse.gov.br' } else { 'sefin.producaorestrita.nfse.gov.br' }
Add-Type -AssemblyName System.Net.Http
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$h = New-Object Net.Http.HttpClientHandler; [void]$h.ClientCertificates.Add($cert)
$resp = (New-Object Net.Http.HttpClient($h)).PostAsync("https://$host_/sefinnacional/nfse", (New-Object Net.Http.StringContent($corpo, [Text.Encoding]::UTF8, 'application/json'))).Result
$txt = $resp.Content.ReadAsStringAsync().Result
Write-Host ("HTTP " + [int]$resp.StatusCode); Write-Host $txt
if (-not $resp.IsSuccessStatusCode) { exit 1 }
$r = $txt | ConvertFrom-Json
if ($r.nfseXmlGZipB64) {
    $bytes = [Convert]::FromBase64String($r.nfseXmlGZipB64); $in = New-Object IO.MemoryStream(,$bytes)
    $g = New-Object IO.Compression.GZipStream($in, [IO.Compression.CompressionMode]::Decompress); $sr = New-Object IO.StreamReader($g)
    $nfse = $sr.ReadToEnd(); [IO.File]::WriteAllText(($Saida -replace '\.xml$','_nfse.xml'), $nfse, (New-Object Text.UTF8Encoding($false)))
    Write-Host "NFS-e salva em $($Saida -replace '\.xml$','_nfse.xml')"
}
