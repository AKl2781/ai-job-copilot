$ErrorActionPreference = 'Stop'

$TaskName = 'AI Job Copilot Backend'
$TaskPath = '\'
$ProjectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$StartScript = Join-Path $ProjectRoot 'scripts\start_backend.ps1'
$PowerShellExe = Join-Path $PSHOME 'powershell.exe'
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

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
    if (-not (Test-Path -LiteralPath $StartScript -PathType Leaf)) {
        throw "Backend start script was not found: $StartScript"
    }

    $existingTasks = @(
        Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue |
            Where-Object { $_.TaskName -eq $TaskName }
    )

    if ($existingTasks.Count -gt 0) {
        $currentProjectTasks = @($existingTasks | Where-Object { Test-TaskBelongsToCurrentProject $_ })
        if ($existingTasks.Count -eq 1 -and $currentProjectTasks.Count -eq 1) {
            Write-Host "Autostart is already installed for this project: $ProjectRoot" -ForegroundColor Yellow
            exit 0
        }

        Write-Host "A scheduled task named '$TaskName' already exists but is not the single task owned by this project." -ForegroundColor Red
        Write-Host 'Nothing was changed. Remove or rename the conflicting task manually after verifying its owner.'
        exit 2
    }

    $actionArguments = '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $StartScript
    $action = New-ScheduledTaskAction -Execute $PowerShellExe -Argument $actionArguments -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
    $trigger.Delay = 'PT15S'
    $principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
        -Description 'Starts the AI Job Copilot local backend after the current user logs on.'

    Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -InputObject $task | Out-Null

    $registeredTask = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction Stop
    if (-not (Test-TaskBelongsToCurrentProject $registeredTask)) {
        throw 'The scheduled task was created, but its backend script path could not be verified.'
    }

    Write-Host "Autostart installed successfully for the current user: $CurrentUser" -ForegroundColor Green
    Write-Host "Task: $TaskName"
    Write-Host "Backend script: $StartScript"
    Write-Host 'The task starts about 15 seconds after Windows logon.'
    exit 0
}
catch {
    Write-Host "Failed to install autostart: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'No API key or credential was requested or stored.'
    exit 1
}
