# Windows PowerShell 5.1 stub. Linked to
# ~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1.
# Prefer the repo profile; fall back to the PowerShell 7 Documents path.
$candidates = @(
    (Join-Path $HOME '.dotfiles\powershell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) 'PowerShell\Microsoft.PowerShell_profile.ps1')
)
foreach ($sharedProfile in $candidates) {
    if (Test-Path -LiteralPath $sharedProfile -PathType Leaf) {
        . $sharedProfile
        break
    }
}

# Import the Chocolatey Profile that contains the necessary code to enable
# tab-completions to function for `choco`.
# Be aware that if you are missing these lines from your profile, tab completion
# for `choco` will not function.
# See https://ch0.co/tab-completion for details.
$ChocolateyProfile = "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
if (Test-Path($ChocolateyProfile)) {
  Import-Module "$ChocolateyProfile"
}
