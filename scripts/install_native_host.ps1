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
    throw '扩展 ID 无效。请从 edge://extensions 复制 32 位扩展 ID（字符范围 a-p）。'
}
if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
    throw '找不到 Native Host manifest 模板。'
}
if (-not (Test-Path -LiteralPath $HostLauncher -PathType Leaf)) {
    throw '找不到固定 Native Host 启动入口。'
}

$resolvedManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)
if (Test-Path -LiteralPath $RegistryPath) {
    $existingPath = (Get-Item -LiteralPath $RegistryPath).GetValue('')
    if (-not [string]::IsNullOrWhiteSpace($existingPath)) {
        try {
            $resolvedExistingPath = [System.IO.Path]::GetFullPath([string]$existingPath)
        }
        catch {
            throw '同名 Native Host 注册项包含无效路径；为避免覆盖，安装已停止。'
        }
        if ($resolvedExistingPath -ne $resolvedManifestPath) {
            throw '同名 Native Host 已指向其他项目；为避免覆盖，安装已停止。'
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
    throw '生成的 Native Host manifest 验证失败。'
}

[System.IO.File]::WriteAllText(
    $ManifestPath,
    $manifest,
    [System.Text.UTF8Encoding]::new($false)
)
New-Item -Path $RegistryPath -Force | Out-Null
Set-Item -LiteralPath $RegistryPath -Value $resolvedManifestPath

Write-Host 'Native Messaging Host 已为当前用户安装。' -ForegroundColor Green
Write-Host "允许的扩展来源：chrome-extension://$ExtensionId/"
Write-Host '请在 edge://extensions 重新加载扩展后使用。'
