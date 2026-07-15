$ErrorActionPreference = 'Stop'

$TaskName = 'AI Job Copilot Backend'
$ProjectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$StartScript = Join-Path $ProjectRoot 'scripts\start_backend.ps1'

function Get-NormalizedPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    try {
        return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    }
    catch {
        return $null
    }
}

function Get-TaskStartScriptPath {
    param($Task)

    if ($null -eq $Task -or @($Task.Actions).Count -ne 1) {
        return $null
    }

    $arguments = [string]$Task.Actions[0].Arguments
    $match = [regex]::Match(
        $arguments,
        '(?i)(?:^|\s)-File\s+(?:"([^"]+)"|''([^'']+)''|(\S+))'
    )
    if (-not $match.Success) {
        return $null
    }

    foreach ($groupNumber in 1..3) {
        if ($match.Groups[$groupNumber].Success) {
            return Get-NormalizedPath $match.Groups[$groupNumber].Value
        }
    }
    return $null
}

function Test-TaskBelongsToCurrentProject {
    param($Task)

    $taskScript = Get-TaskStartScriptPath $Task
    $expectedScript = Get-NormalizedPath $StartScript
    return ($null -ne $taskScript) -and
        $taskScript.Equals($expectedScript, [System.StringComparison]::OrdinalIgnoreCase)
}

try {
    if (-not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) {
        throw 'Windows ScheduledTasks PowerShell module is unavailable on this system.'
    }

    $existingTasks = @(
        Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue |
            Where-Object { $_.TaskName -eq $TaskName }
    )

    if ($existingTasks.Count -eq 0) {
        Write-Host "Autostart is not installed for this project. Task '$TaskName' was not found." -ForegroundColor Yellow
        Write-Host 'No changes were made.'
        Write-Host 'If the backend is running, use stop_ai_job_copilot.bat to stop it.'
        exit 0
    }

    $currentProjectTasks = @($existingTasks | Where-Object { Test-TaskBelongsToCurrentProject $_ })
    if ($currentProjectTasks.Count -eq 0) {
        Write-Host "Task '$TaskName' exists, but it does not point to this project's backend script." -ForegroundColor Red
        Write-Host 'Nothing was removed.'
        exit 2
    }
    if ($currentProjectTasks.Count -gt 1) {
        Write-Host "More than one task named '$TaskName' points to this project." -ForegroundColor Red
        Write-Host 'Nothing was removed because the task ownership is ambiguous.'
        exit 2
    }

    $taskToRemove = $currentProjectTasks[0]
    Unregister-ScheduledTask -TaskName $taskToRemove.TaskName -TaskPath $taskToRemove.TaskPath -Confirm:$false

    Write-Host 'Autostart was removed successfully. Project files and .env were not changed.' -ForegroundColor Green
    Write-Host 'A currently running backend was not stopped.'
    Write-Host 'Use stop_ai_job_copilot.bat if you want to stop the current backend.' -ForegroundColor Yellow
    exit 0
}
catch {
    Write-Host "Failed to uninstall autostart: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
