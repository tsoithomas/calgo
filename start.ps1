$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# ── venv setup ───────────────────────────────────────────────────────────────
$venvActivate = "$root\venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Host "[setup] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv "$root\venv"
    & $venvActivate
    Write-Host "[setup] Installing Python dependencies..." -ForegroundColor Cyan
    pip install -r "$root\requirements.txt"
} else {
    & $venvActivate
}

$python  = "$root\venv\Scripts\python.exe"
$uvicorn = "$root\venv\Scripts\uvicorn.exe"

# ── start jobs ───────────────────────────────────────────────────────────────
Write-Host "[start] Launching all services..." -ForegroundColor Green

$jobCore = Start-Job -Name "Core" -ArgumentList $python, $root -ScriptBlock {
    param($python, $root)
    Set-Location $root
    $env:PYTHONUTF8 = "1"
    & $python main.py --config config/config.json --symbols AAPL MSFT GOOGL --no-banner 2>&1
}

$jobApi = Start-Job -Name "API" -ArgumentList $uvicorn, $root -ScriptBlock {
    param($uvicorn, $root)
    Set-Location $root
    & $uvicorn dashboard_api:app --host 0.0.0.0 --port 8000 --reload 2>&1
}

$jobFrontend = Start-Job -Name "Frontend" -ArgumentList $root -ScriptBlock {
    param($root)
    Set-Location "$root\dashboard"
    npm install 2>&1 | Out-Null
    npm run dev 2>&1
}

$jobs = @($jobCore, $jobApi, $jobFrontend)

Write-Host "[ready] Core | API -> http://localhost:8000 | Frontend -> http://localhost:5173"
Write-Host "        Press Ctrl+C to stop all services.`n"

# ── stream output ─────────────────────────────────────────────────────────────
$colors = @{ Core = "Yellow"; API = "Cyan"; Frontend = "Magenta" }

try {
    while ($true) {
        foreach ($job in $jobs) {
            $lines = Receive-Job $job 2>&1
            foreach ($line in $lines) {
                Write-Host "[$($job.Name)] $line" -ForegroundColor $colors[$job.Name]
            }
            # Surface any job that died unexpectedly
            if ($job.State -eq "Failed") {
                Write-Host "[$($job.Name)] FAILED: $($job.ChildJobs[0].JobStateInfo.Reason)" -ForegroundColor Red
            }
        }
        Start-Sleep -Milliseconds 300
    }
} finally {
    Write-Host "`n[stop] Stopping all services..." -ForegroundColor Red
    $jobs | Stop-Job
    $jobs | Remove-Job -Force
    Write-Host "[stop] Done."
}
