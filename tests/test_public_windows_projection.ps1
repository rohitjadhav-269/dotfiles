#Requires -Version 7.4
# Public-owned fixtures for projection-specific Windows behavior.
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) {
    Write-Output 'SKIP: public Windows projection fixtures require native Windows.'
    exit 0
}

$root = Split-Path $PSScriptRoot -Parent
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('public-projection-' + [guid]::NewGuid().ToString('N'))

function Assert([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

try {
    # Exercise the package manifest contract against disposable Brewfile data.
    $packageRoot = Join-Path $fixture 'packages'
    $config = Join-Path $packageRoot 'config'
    New-Item -ItemType Directory -Path $fixture -Force | Out-Null
    New-Item -ItemType Directory -Path $config -Force | Out-Null
    $encoding = [Text.UTF8Encoding]::new($false)
    [IO.File]::WriteAllText((Join-Path $packageRoot 'Brewfile'), 'brew "fixture-mapped"' + "`n", $encoding)
    $header = "Key`tMode`tSource`tId`tNote`n"
    $rows = @(
        "brew:fixture-mapped`tmanual`t`t`tFixture disposition`n",
        "windows:rsync`tmanual`t`t`tManual WSL disposition`n"
    ) -join ''
    $manifest = Join-Path $config 'windows-packages.tsv'
    [IO.File]::WriteAllText($manifest, $header + $rows, $encoding)

    . (Join-Path $root 'scripts/lib/windows-packages.ps1')
    $publicPackages = @(Get-DotfilesWindowsPackages -Root $root)
    $publicRsync = @($publicPackages | Where-Object Key -EQ 'windows:rsync')
    Assert ($publicRsync.Count -eq 1 -and $publicRsync[0].Mode -eq 'manual') 'The public package manifest must retain its manual windows:rsync disposition.'
    $packages = @(Get-DotfilesWindowsPackages -Root $packageRoot)
    $rsync = @($packages | Where-Object Key -EQ 'windows:rsync')
    Assert ($rsync.Count -eq 1 -and $rsync[0].Mode -eq 'manual') 'The explicit windows:rsync manual disposition was rejected.'

    [IO.File]::WriteAllText((Join-Path $packageRoot 'Brewfile'), "brew `"fixture-mapped`"`nbrew `"fixture-unmapped`"`n", $encoding)
    $unmappedRejected = $false
    try { Get-DotfilesWindowsPackages -Root $packageRoot | Out-Null }
    catch { $unmappedRejected = $_.Exception.Message -like '*Unmapped Brewfile entry: brew:fixture-unmapped*' }
    Assert $unmappedRejected 'An unmapped Brewfile entry was accepted.'

    # Exercise real dispatch with a process spy; never launch Settings or touch
    # the host's file associations from a fixture.
    $mediaScripts = Join-Path $fixture 'media/scripts'
    New-Item -ItemType Directory -Path (Join-Path $mediaScripts 'lib') -Force | Out-Null
    foreach ($name in @('dot-windows.ps1', 'check-windows-vlc-associations.ps1')) {
        Copy-Item (Join-Path $root "scripts/$name") (Join-Path $mediaScripts $name)
    }
    [IO.File]::WriteAllText((Join-Path $mediaScripts 'lib/windows-common.ps1'), @'
function Assert-DotfilesWindows {}
function Resolve-DotfilesPwsh { 'fixture-pwsh' }
function Invoke-DotfilesNative($Executable, $Arguments) { $global:PublicMediaArguments = $Arguments }
'@, $encoding)
    & (Join-Path $mediaScripts 'dot-windows.ps1') -Command default-apps -Arguments @('-Check')
    Assert ($global:PublicMediaArguments[-1] -eq '-Check') 'The media command lost its Check switch.'
    Assert ($global:PublicMediaArguments[-2] -eq (Join-Path (Split-Path $mediaScripts) 'scripts/check-windows-vlc-associations.ps1')) 'The media command selected the wrong helper.'
    Remove-Variable PublicMediaArguments -Scope Global

    $mediaManifest = Join-Path $fixture 'media.tsv'
    foreach ($case in @(
        @{Text="extension`n.mp4`n.mp4`n"; Error='Invalid or duplicate VLC extension:*'},
        @{Text="extension`n../mp4`n"; Error='Invalid or duplicate VLC extension:*'},
        @{Text="extension`n"; Error='VLC association manifest is empty.'}
    )) {
        [IO.File]::WriteAllText($mediaManifest, $case.Text, $encoding)
        $rejected = $false
        try { & (Join-Path $mediaScripts 'check-windows-vlc-associations.ps1') -Manifest $mediaManifest -Check | Out-Null }
        catch { $rejected = $_.Exception.Message -like $case.Error }
        Assert $rejected 'An invalid media manifest reached association inspection.'
    }

    # Extract the actual doctor check, stub its two read-only Git results, and
    # hide the launcher from command discovery.
    $tokens = $null
    $parseErrors = $null
    $doctorPath = Join-Path $root 'scripts/doctor-windows.ps1'
    $doctorAst = [Management.Automation.Language.Parser]::ParseFile($doctorPath, [ref]$tokens, [ref]$parseErrors)
    Assert ($parseErrors.Count -eq 0) 'The public Windows doctor does not parse.'
    $doctorCheck = $doctorAst.Find({ param($node)
        $node -is [Management.Automation.Language.CommandAst] -and
        $node.GetCommandName() -eq 'Check-Dotfiles' -and
        $node.CommandElements[1].Value -eq 'Windows Git overlay'
    }, $true)
    Assert ($null -ne $doctorCheck) 'The Windows Git overlay doctor check was not found.'
    $checkBlock = ($doctorCheck.CommandElements | Where-Object {
        $_ -is [Management.Automation.Language.ScriptBlockExpressionAst]
    } | Select-Object -First 1).ScriptBlock
    $checkText = $checkBlock.Extent.Text
    $checkText = $checkText.Replace(
        '$helper = & git.exe config --global --includes --get credential.helper',
        '$helper = ''manager''; $global:LASTEXITCODE = 0'
    )
    $checkText = $checkText.Replace(
        '$ssh = & git.exe config --global --includes --get core.sshCommand',
        '$ssh = ''dotfiles-ssh.cmd''; $global:LASTEXITCODE = 0'
    )
    Assert ($checkText -notmatch 'git\.exe') 'The doctor fixture would invoke the host Git configuration.'
    $checkText = $checkText.Trim()
    if (-not $checkText.StartsWith('{') -or -not $checkText.EndsWith('}')) {
        throw 'The parsed doctor check did not have the expected script-block extent.'
    }
    $checkText = $checkText.Substring(1, $checkText.Length - 2)
    $check = [scriptblock]::Create($checkText)

    function Get-Command {
        [CmdletBinding()]
        param([Parameter(Position = 0)][string]$Name)
        if ($Name -eq 'dotfiles-ssh.cmd') { return $null }
        Microsoft.PowerShell.Core\Get-Command -Name $Name -ErrorAction $ErrorActionPreference
    }

    $doctorMessage = ''
    try { & $check }
    catch { $doctorMessage = $_.Exception.Message }
    foreach ($required in @('dotfiles-ssh.cmd', '%USERPROFILE%\.local\bin', 'Machine-only PATH', 'dot path')) {
        Assert ($doctorMessage.Contains($required)) "The missing-launcher diagnostic omitted '$required'."
    }

    # Remove the doctor-only mock so TLDR exercises real command resolution.
    Remove-Item -LiteralPath Function:Get-Command

    # Command resolution must fail closed with the same diagnostic as process
    # start failure. The supplied path is intentionally absent, so no process runs.
    . (Join-Path $root 'scripts/lib/windows-tldr.ps1')
    $missingExecutable = Join-Path $fixture 'missing/tldr-python.exe'
    $tldrMessage = ''
    try { Invoke-DotfilesTldrProcess -Argument '--version' -Executable $missingExecutable | Out-Null }
    catch { $tldrMessage = $_.Exception.Message }
    Assert ($tldrMessage -like 'TLDR launch failed:*') 'A missing TLDR executable did not report TLDR launch failed.'
    Assert ($tldrMessage.Contains($missingExecutable)) 'TLDR did not fail on the intended absent executable.'

    Write-Output 'PASS: package coverage, media dispatch and input rejection, doctor PATH guidance, and TLDR launch failure.'
} finally {
    $resolvedFixture = [IO.Path]::GetFullPath($fixture)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if ((Split-Path $resolvedFixture -Parent) -ine $tempRoot -or (Split-Path $resolvedFixture -Leaf) -notmatch '^public-projection-[0-9a-f]{32}$') {
        throw 'Unsafe public projection fixture cleanup path.'
    }
    if (Test-Path -LiteralPath $resolvedFixture) { Remove-Item -LiteralPath $resolvedFixture -Recurse -Force }
}
