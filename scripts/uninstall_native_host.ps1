$ErrorActionPreference = 'Stop'
$HostName = 'com.ai_job_copilot.service_control'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $ProjectRoot 'native_host\host_manifest.json'
$RegistryPath = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName"
$resolvedManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)

if (-not (Test-Path -LiteralPath $RegistryPath)) {
    Write-Host 'The Native Messaging Host is not installed for this project.' -ForegroundColor Yellow
    exit 0
}

$registeredPath = (Get-Item -LiteralPath $RegistryPath).GetValue('')
try {
    $resolvedRegisteredPath = [System.IO.Path]::GetFullPath([string]$registeredPath)
}
catch {
    throw 'The registration path is invalid; refusing to remove another Host.'
}

if ($resolvedRegisteredPath -ne $resolvedManifestPath) {
    throw 'The Native Host does not point to this project; refusing to remove it.'
}

Remove-Item -LiteralPath $RegistryPath -Force
if (Test-Path -LiteralPath $ManifestPath -PathType Leaf) {
    Remove-Item -LiteralPath $ManifestPath -Force
}

Write-Host 'The Native Messaging Host for this project was uninstalled.' -ForegroundColor Green
Write-Host 'The extension, project, .env, and running backend were not changed.'
