#Requires -Version 7.4
[CmdletBinding()]
param([switch]$Check, [switch]$OpenSettings,
    [string]$Manifest=(Join-Path (Split-Path $PSScriptRoot) 'config/windows-vlc-associations.tsv'))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'lib/windows-common.ps1')
Assert-DotfilesWindows

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "VLC association manifest missing: $Manifest" }
$extensions=[Collections.Generic.List[string]]::new()
$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($line in [IO.File]::ReadAllLines($Manifest)) {
    $entry=$line.Trim()
    if (-not $entry -or $entry.StartsWith('#') -or $entry -eq 'extension') { continue }
    if ($entry -cnotmatch '^\.[a-z0-9]+$' -or -not $seen.Add($entry)) { throw "Invalid or duplicate VLC extension: $entry" }
    $extensions.Add($entry)
}
if ($extensions.Count -eq 0) { throw 'VLC association manifest is empty.' }

$capabilities=[Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SOFTWARE\Clients\Media\VLC\Capabilities\FileAssociations')
if (-not $capabilities) { $capabilities=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('SOFTWARE\Clients\Media\VLC\Capabilities\FileAssociations') }
$missing=[Collections.Generic.List[string]]::new()
$unsupported=[Collections.Generic.List[string]]::new()
$matched=0
foreach($ext in $extensions) {
    $expected=if($capabilities){[string]$capabilities.GetValue($ext)}else{''}
    $choice=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\$ext\UserChoice")
    $actual=if($choice){[string]$choice.GetValue('ProgId')}else{''}
    if (-not $actual) {
        $fallback=[Microsoft.Win32.Registry]::ClassesRoot.OpenSubKey($ext)
        if ($fallback) { $actual=[string]$fallback.GetValue('') }
    }
    if (($expected -and $actual -ieq $expected) -or $actual -ieq 'Applications\vlc.exe') { $matched++ }
    elseif (-not $expected) { $unsupported.Add("$ext (current: $(if($actual){$actual}else{'unset'}))") }
    else { $missing.Add("$ext (current: $(if($actual){$actual}else{'unset'}))") }
}
if ($capabilities) { $capabilities.Close() }

Write-Output "VLC defaults: $matched/$($extensions.Count) matched; $($missing.Count) different; $($unsupported.Count) not advertised by this VLC installation."
if ($missing.Count) { Write-Output "Set in Windows Settings: $($missing -join ', ')" }
if ($unsupported.Count) { Write-Output "Review VLC registration or leave these manual: $($unsupported -join ', ')" }
if ($OpenSettings) {
    $registered=[Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SOFTWARE\RegisteredApplications')
    $uri=if($registered -and $registered.GetValue('VLC')){'ms-settings:defaultapps?registeredAppMachine=VLC'}else{'ms-settings:defaultapps'}
    if ($registered) { $registered.Close() }
    Start-Process $uri
    Write-Output 'Choose VLC for the listed extensions in Windows Settings, then run: dot default-apps -Check'
}
if ($Check -and ($missing.Count -or $unsupported.Count)) { throw 'VLC file associations have not converged.' }
