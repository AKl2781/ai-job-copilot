param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ExtensionId
)

$ErrorActionPreference = 'Stop'
$HostName = 'com.ai_job_copilot.service_control'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$NativeHostDirectory = Join-Path $ProjectRoot 'native_host'
$TemplatePath = Join-Path $NativeHostDirectory 'host_manifest.template.json'
$ManifestPath = Join-Path $NativeHostDirectory 'host_manifest.json'
$HostLauncher = Join-Path $NativeHostDirectory 'run_host.bat'
$RegistryPath = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName"

function ConvertTo-JsonStringContent {
    param([string]$Value)
    $json = ConvertTo-Json $Value -Compress
    return $json.Substring(1, $json.Length - 2)
}

if ($ExtensionId -cnotmatch '^[a-p]{32}$') {
    throw 'Invalid extension ID. Copy the 32-character ID (a-p only) from edge://extensions.'
}
if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
    throw 'Native Host manifest template was not found.'
}
if (-not (Test-Path -LiteralPath $HostLauncher -PathType Leaf)) {
    throw 'The fixed Native Host launcher was not found.'
}

$resolvedManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)
if (Test-Path -LiteralPath $RegistryPath) {
    $existingPath = (Get-Item -LiteralPath $RegistryPath).GetValue('')
    if (-not [string]::IsNullOrWhiteSpace($existingPath)) {
        try {
            $resolvedExistingPath = [System.IO.Path]::GetFullPath([string]$existingPath)
        }
        catch {
            throw 'The existing Native Host registration has an invalid path; refusing to overwrite it.'
        }
        if ($resolvedExistingPath -ne $resolvedManifestPath) {
            throw 'The Native Host name belongs to another project; refusing to overwrite it.'
        }
    }
}

$template = Get-Content -LiteralPath $TemplatePath -Raw -Encoding UTF8
$manifest = $template.Replace(
    '__HOST_PATH__',
    (ConvertTo-JsonStringContent ([System.IO.Path]::GetFullPath($HostLauncher)))
).Replace(
    '__ALLOWED_ORIGIN__',
    "chrome-extension://$ExtensionId/"
)

# Validate before writing or changing the registry.
$parsedManifest = $manifest | ConvertFrom-Json
if ($parsedManifest.name -ne $HostName -or
    $parsedManifest.type -ne 'stdio' -or
    $parsedManifest.allowed_origins.Count -ne 1 -or
    $parsedManifest.allowed_origins[0] -ne "chrome-extension://$ExtensionId/") {
    throw 'Generated Native Host manifest validation failed.'
}

[System.IO.File]::WriteAllText(
    $ManifestPath,
    $manifest,
    [System.Text.UTF8Encoding]::new($false)
)
New-Item -Path $RegistryPath -Force | Out-Null
Set-Item -LiteralPath $RegistryPath -Value $resolvedManifestPath

Write-Host 'Native Messaging Host installed for the current user.' -ForegroundColor Green
Write-Host "Allowed extension origin: chrome-extension://$ExtensionId/"
Write-Host 'Reload the extension at edge://extensions before use.'
