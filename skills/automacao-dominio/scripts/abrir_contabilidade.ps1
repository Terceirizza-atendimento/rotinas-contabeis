# Passos 2 e 3: Lista de Programas -> Contabilidade -> login do sistema.
# Uso: $env:DW_SYS_USER='LETICIA'; $env:DW_SYS_PASS='...'; .\abrir_contabilidade.ps1 [-Captura caminho.png]
param([string]$Captura = "$PSScriptRoot\..\saida\ultima_tela.png")

Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public class W{
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
}
'@
[W]::SetProcessDPIAware() | Out-Null

function Clicar($x,$y){ [W]::SetCursorPos($x,$y)|Out-Null; Start-Sleep -Milliseconds 150; [W]::mouse_event(2,0,0,0,0); [W]::mouse_event(4,0,0,0,0); Start-Sleep -Milliseconds 300 }
function Janela($titulo){ Get-Process AppController -ErrorAction SilentlyContinue | Where-Object MainWindowTitle -like $titulo | Select-Object -First 1 }
function Capturar($arq){
  New-Item -ItemType Directory -Force (Split-Path $arq) | Out-Null
  $b=New-Object Drawing.Bitmap 1920,1080; $g=[Drawing.Graphics]::FromImage($b)
  $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save($arq)
}

# Passo 2: Contabilidade + Enter (duplo clique não funciona)
$lista = Janela 'Lista*'
if (-not $lista) { throw "Lista de Programas não está aberta" }
[W]::ShowWindow($lista.MainWindowHandle,9)|Out-Null; [W]::SetForegroundWindow($lista.MainWindowHandle)|Out-Null
Start-Sleep 1
Clicar 864 290
[Windows.Forms.SendKeys]::SendWait("{ENTER}")

# Espera o diálogo "Conectando ..." (some rápido: preencher no mesmo comando)
$t=0; $dlg=$null
while ($t -lt 90 -and -not $dlg) { $dlg = Janela 'Conectando*'; if(-not $dlg){ Start-Sleep 1; $t++ } }
if (-not $dlg) { Capturar $Captura; throw "Diálogo 'Conectando ...' não apareceu em 90 s" }
Start-Sleep 3

# Passo 3: login do sistema
if (-not (Janela 'Conectando*')) { Capturar $Captura; throw "Diálogo sumiu antes de digitar" }
[W]::SetForegroundWindow($dlg.MainWindowHandle)|Out-Null
Clicar 1000 497; [Windows.Forms.SendKeys]::SendWait("^a"); [Windows.Forms.SendKeys]::SendWait($env:DW_SYS_USER)
Clicar 1000 535; [Windows.Forms.SendKeys]::SendWait($env:DW_SYS_PASS)
Capturar $Captura
Write-Output "Diálogo preenchido; confira a captura antes do OK: $Captura"
