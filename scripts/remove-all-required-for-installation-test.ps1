param(
  [switch]$RemoveApp,
  [switch]$AllData,
  [switch]$DevData,
  [switch]$KeepPython,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "Removing Codex Account Manager local install/runtime state for installation testing..."
if ($DryRun) {
  Write-Host "Dry run only; no files will be removed."
}

$homeDir = $env:USERPROFILE
$roamingAppData = Join-Path $homeDir "AppData\Roaming"
$localAppData = Join-Path $homeDir "AppData\Local"
$programFiles = ${env:ProgramFiles}

$targets = @(
  "$homeDir\.local\bin\codex-account.exe",
  "$homeDir\.local\bin\codex-account",
  "$homeDir\pipx\venvs\codex-account-manager",
  "$homeDir\pipx\shared",
  "$homeDir\pipx\logs",
  "$homeDir\.local\pipx\venvs\codex-account-manager",
  "$homeDir\.local\pipx\shared",
  "$homeDir\.local\pipx\logs",
  "$homeDir\.codex\ui-service\service.json",
  "$homeDir\.codex\account-manager\runtime-state.json",
  "$roamingAppData\Codex Account Manager",
  "$localAppData\Codex Account Manager",
  "$localAppData\com.codexaccountmanager.desktop",
  "$localAppData\Programs\Codex Account Manager"
)

function Remove-IfPresent {
  param([string]$PathValue)
  if (Test-Path -LiteralPath $PathValue) {
    if ($DryRun) {
      Write-Host "Would remove: $PathValue"
    } else {
      Remove-Item -LiteralPath $PathValue -Recurse -Force -ErrorAction SilentlyContinue
      Write-Host "Removed: $PathValue"
    }
  } else {
    Write-Host "Not present: $PathValue"
  }
}

function Run-IfPresent {
  param(
    [string]$Command,
    [string[]]$Args
  )
  if (Get-Command $Command -ErrorAction SilentlyContinue) {
    if ($DryRun) {
      Write-Host "Would run: $Command $($Args -join ' ')"
      return
    }
    try {
      & $Command @Args | Out-Null
      Write-Host "Ran: $Command $($Args -join ' ')"
    } catch {
      Write-Host "Command failed (ignored): $Command $($Args -join ' ')"
    }
  } else {
    Write-Host "Command not found, skipped: $Command"
  }
}

function Stop-AppProcess {
  if ($DryRun) {
    Write-Host "Would stop Codex Account Manager processes."
    return
  }
  Get-Process -Name "Codex Account Manager" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Write-Host "Requested packaged app stop."
}

Stop-AppProcess
Run-IfPresent "$homeDir\.local\bin\codex-account.exe" @("ui-service", "stop")
Run-IfPresent "codex-account" @("ui-service", "stop")
Run-IfPresent "pipx" @("uninstall", "codex-account-manager")
Run-IfPresent "py" @("-m", "pip", "uninstall", "-y", "codex-account-manager")
Run-IfPresent "python" @("-m", "pip", "uninstall", "-y", "codex-account-manager")

foreach ($target in $targets) {
  Remove-IfPresent -PathValue $target
}

if ($RemoveApp) {
  $appTargets = @(
    "$localAppData\Programs\Codex Account Manager",
    "$programFiles\Codex Account Manager"
  )
  foreach ($target in $appTargets) {
    Remove-IfPresent -PathValue $target
  }
} else {
  Write-Host "Kept installed app. Pass -RemoveApp to remove installer app directories."
}

if ($DevData) {
  Remove-IfPresent -PathValue "$roamingAppData\Codex Account Manager Dev"
  Remove-IfPresent -PathValue "$localAppData\Codex Account Manager Dev"
} else {
  Write-Host "Kept Electron dev-shell data. Pass -DevData to remove it."
}

if ($AllData) {
  Remove-IfPresent -PathValue "$homeDir\.codex\account-profiles"
  Remove-IfPresent -PathValue "$homeDir\.codex\profile-homes"
  Remove-IfPresent -PathValue "$homeDir\.codex\account-backups"
  Remove-IfPresent -PathValue "$homeDir\.codex\auth.json"
} else {
  Write-Host ""
  Write-Host "Kept intentionally:"
  Write-Host "  $homeDir\.codex\account-profiles"
  Write-Host "  $homeDir\.codex\profile-homes"
  Write-Host "  $homeDir\.codex\account-backups"
  Write-Host "  $homeDir\.codex\auth.json"
}

if (-not $KeepPython) {
  $pythonPkg = Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -like "Python 3.11* (64-bit)" } |
    Select-Object -First 1

  if ($pythonPkg -and $pythonPkg.QuietUninstallString) {
    if ($DryRun) {
      Write-Host "Would remove: $($pythonPkg.DisplayName)"
    } else {
      $quiet = [string]$pythonPkg.QuietUninstallString
      $exe = if ($quiet -match '"([^"]+)"') { $Matches[1] } else { ($quiet -split " ")[0] }
      if (Test-Path -LiteralPath $exe) {
        Start-Process -FilePath $exe -ArgumentList "/uninstall", "/quiet" -Wait
        Write-Host "Removed: $($pythonPkg.DisplayName)"
      } else {
        Write-Host "Python uninstaller not found: $exe"
      }
    }
  } else {
    Write-Host "Python 3.11 uninstall entry not present."
  }
} else {
  Write-Host "Kept Python runtime (-KeepPython)."
}

Write-Host ""
Write-Host "Cleanup complete. The packaged app should use its bundled core on next launch."
