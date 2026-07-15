$ErrorActionPreference = 'Stop'
$HostName = 'com.ai_job_copilot.service_control'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $ProjectRoot 'native_host\host_manifest.json'
$RegistryPath = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName"
$resolvedManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)

if (-not (Test-Path -LiteralPath $RegistryPath)) {
    Write-Host '当前项目的 Native Messaging Host 尚未安装。' -ForegroundColor Yellow
    exit 0
}

$registeredPath = (Get-Item -LiteralPath $RegistryPath).GetValue('')
try {
    $resolvedRegisteredPath = [System.IO.Path]::GetFullPath([string]$registeredPath)
}
catch {
    throw '注册项路径无效；为避免删除其他 Host，卸载已停止。'
}

if ($resolvedRegisteredPath -ne $resolvedManifestPath) {
    throw '同名 Native Host 未指向当前项目；为避免误删，卸载已停止。'
}

Remove-Item -LiteralPath $RegistryPath -Force
if (Test-Path -LiteralPath $ManifestPath -PathType Leaf) {
    Remove-Item -LiteralPath $ManifestPath -Force
}

Write-Host '当前项目的 Native Messaging Host 已卸载。' -ForegroundColor Green
Write-Host '扩展、项目、.env 和当前后端均未修改。'
