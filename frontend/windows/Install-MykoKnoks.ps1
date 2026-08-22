$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Installer = Get-ChildItem -Path $PSScriptRoot -Filter 'MykoKnoks-Windows-Setup-v*-x64.exe' | Select-Object -First 1
$ChecksumFile = Join-Path $PSScriptRoot 'SHA256SUMS.txt'
$ApiHealth = 'https://knoksen.nova.usbx.me/mykoknoks-api/health'

Write-Host ''
Write-Host '=== MykoKnoks Windows One-Click ===' -ForegroundColor Green

if (-not $Installer) {
    throw 'MykoKnoks Windows installer was not found in this folder.'
}
if (-not (Test-Path $ChecksumFile)) {
    throw 'SHA256SUMS.txt is missing. Installation stopped.'
}

Write-Host '[1/4] Verifying installer SHA-256...'
$ExpectedLine = Get-Content $ChecksumFile | Where-Object { $_ -match [regex]::Escape($Installer.Name) } | Select-Object -First 1
if (-not $ExpectedLine) {
    throw "No checksum entry found for $($Installer.Name)."
}
$ExpectedHash = (($ExpectedLine -split '\s+')[0]).ToUpperInvariant()
$ActualHash = (Get-FileHash -Path $Installer.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
if ($ActualHash -ne $ExpectedHash) {
    throw "SHA-256 mismatch. Expected $ExpectedHash, got $ActualHash."
}
Write-Host "      OK: $ActualHash" -ForegroundColor Green

Write-Host '[2/4] Testing MykoKnoks Ultra API...'
try {
    $Health = Invoke-RestMethod -Uri $ApiHealth -Method Get -TimeoutSec 15
    if ($Health.status -eq 'ok') {
        Write-Host "      API OK: $($Health.service) $($Health.version)" -ForegroundColor Green
    } else {
        Write-Warning "API responded without status=ok. Demo mode remains available."
    }
} catch {
    Write-Warning 'Ultra API is currently unavailable. Installing anyway; Demo mode remains available.'
}

Write-Host '[3/4] Installing MykoKnoks for the current Windows user...'
$Process = Start-Process -FilePath $Installer.FullName -ArgumentList '/S' -Wait -PassThru
if ($Process.ExitCode -ne 0) {
    throw "Installer exited with code $($Process.ExitCode)."
}
Write-Host '      Installation complete.' -ForegroundColor Green

Write-Host '[4/4] Starting MykoKnoks...'
$Candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\MykoKnoks\MykoKnoks.exe'),
    (Join-Path $env:LOCALAPPDATA 'MykoKnoks\MykoKnoks.exe'),
    (Join-Path $env:ProgramFiles 'MykoKnoks\MykoKnoks.exe')
)
$AppExe = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $AppExe -and (Test-Path (Join-Path $env:LOCALAPPDATA 'Programs'))) {
    $AppExe = Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Programs') -Filter 'MykoKnoks.exe' -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}

if ($AppExe -and (Test-Path $AppExe)) {
    Start-Process -FilePath $AppExe
    Write-Host "      Started: $AppExe" -ForegroundColor Green
} else {
    Write-Warning 'MykoKnoks was installed, but the executable was not found automatically. Start MykoKnoks from the Start menu.'
}

Write-Host ''
Write-Host 'DONE. MykoKnoks is installed.' -ForegroundColor Green
Write-Host 'API: https://knoksen.nova.usbx.me/mykoknoks-api'
