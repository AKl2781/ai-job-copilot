param(
    [switch]$NoBuild,
    [switch]$NoSeed,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Invoke-DockerCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "`n==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Wait-ForHealthyService {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServiceName,
        [int]$TimeoutSeconds = 90
    )

    Write-Host "`n==> Wait for $ServiceName health check" -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $containerId = docker compose ps -q $ServiceName 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($containerId)) {
            $status = docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" $containerId 2>$null
            if ($LASTEXITCODE -eq 0 -and $status -eq "healthy") {
                return
            }
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "$ServiceName did not become healthy within $TimeoutSeconds seconds (last status: $status)."
}

try {
    Write-Host "==> Check Docker Desktop" -ForegroundColor Cyan
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI was not found. Install and start Docker Desktop, then try again."
    }

    docker info --format "Docker Engine {{.ServerVersion}}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop is not running. Start Docker Desktop, wait until it is ready, then double-click the shortcut again."
    }

    if ($NoBuild) {
        Invoke-DockerCommand "Start Docker Compose services" { docker compose up -d }
    }
    else {
        Invoke-DockerCommand "Build and start Docker Compose services" { docker compose up --build -d }
    }

    Wait-ForHealthyService "backend"

    # This launcher is an explicit local Demo initialization command. Compose
    # itself intentionally does not run migrations during container startup.
    Invoke-DockerCommand "Upgrade local Demo database to Alembic head" {
        docker compose exec -T backend python -m alembic -c alembic.ini upgrade head
    }

    Invoke-DockerCommand "Verify Alembic revision" {
        docker compose exec -T backend python -m alembic -c alembic.ini current
    }

    $postgresUser = (docker compose exec -T postgres printenv POSTGRES_USER | Select-Object -Last 1).Trim()
    $postgresDatabase = (docker compose exec -T postgres printenv POSTGRES_DB | Select-Object -Last 1).Trim()
    if ([string]::IsNullOrWhiteSpace($postgresUser) -or [string]::IsNullOrWhiteSpace($postgresDatabase)) {
        throw "Unable to resolve the Demo database name or user."
    }

    $userCountOutput = docker compose exec -T postgres psql -U $postgresUser -d $postgresDatabase -Atc "SELECT count(*) FROM users;"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect Demo data."
    }
    $userCount = [int]($userCountOutput | Select-Object -Last 1)

    if ($userCount -eq 0 -and -not $NoSeed) {
        Invoke-DockerCommand "Seed local Demo data" {
            docker compose exec -T backend python backend/scripts/seed_demo.py
        }
    }
    elseif ($userCount -gt 0) {
        Write-Host "`n==> Demo data already exists; seed skipped." -ForegroundColor DarkGreen
    }
    else {
        Write-Host "`n==> Empty database detected; seed skipped because -NoSeed was supplied." -ForegroundColor Yellow
    }

    Wait-ForHealthyService "frontend"

    $backend = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 15
    if ($backend.StatusCode -ne 200 -or $backend.Content -notmatch '"status"\s*:\s*"ok"') {
        throw "Backend health check returned an unexpected response."
    }

    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 30
    if ($frontend.StatusCode -ne 200) {
        throw "Frontend returned HTTP $($frontend.StatusCode)."
    }

    Write-Host "`n==> Demo is ready" -ForegroundColor Green
    docker compose ps
    Write-Host "`nFrontend: http://localhost:3000"
    Write-Host "Backend:  http://localhost:8000"
    Write-Host "Health:   http://localhost:8000/health"

    if (-not $NoBrowser) {
        Write-Host "`n==> Open http://localhost:3000 in the default browser" -ForegroundColor Cyan
        Start-Process "http://localhost:3000"
    }
}
catch {
    Write-Host "`nDemo startup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Run 'docker compose ps' and 'docker compose logs' for details." -ForegroundColor Yellow
    exit 1
}
