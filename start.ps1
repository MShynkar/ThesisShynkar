# =============================================================================
#  RAG-RBAC — start backend + frontend
# -----------------------------------------------------------------------------
#  Launches uvicorn (FastAPI, :8000) and the Vite dev server (:5173) in the
#  background, waits until both respond, then prints URLs and demo credentials.
#
#  Prereqs:
#    * backend\.venv  populated  (python -m venv .venv ; pip install -r requirements.txt)
#    * frontend\node_modules     (npm install)
#    * Ollama running on :11434 with nomic-embed-text and llama3.2:3b pulled
#
#  Run:    .\start.ps1
#  Stop:   .\stop.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$ROOT     = $PSScriptRoot
$BACKEND  = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$LOG_DIR  = Join-Path $ROOT "logs"
New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null

function Test-PortListening([int]$port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-For([scriptblock]$check, [int]$timeoutSec) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        try { if (& $check) { return $true } } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Host "=== RAG-RBAC start ===" -ForegroundColor Cyan

# ---- sanity checks ----------------------------------------------------------
if (-not (Test-Path (Join-Path $BACKEND ".venv\Scripts\uvicorn.exe"))) {
    Write-Error "Backend venv not found. Create it:`n  cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}
if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
    Write-Warning "Frontend node_modules missing — running 'npm install' first"
    Push-Location $FRONTEND; npm install; Pop-Location
}

# ---- Ollama (warn only — backend will start without it but search will fail) -
try {
    $null = Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
    Write-Host "[ OK ] Ollama reachable on :11434"
} catch {
    Write-Warning "Ollama not reachable on :11434 — start it with 'ollama serve' (search/generation will fail without it)"
}

# ---- backend ----------------------------------------------------------------
if (Test-PortListening 8000) {
    Write-Warning "Port 8000 already in use — backend may already be running. Skipping."
} else {
    Write-Host "[ .. ] Starting backend on :8000"
    $be = Start-Process -FilePath (Join-Path $BACKEND ".venv\Scripts\uvicorn.exe") `
        -ArgumentList "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory $BACKEND `
        -RedirectStandardOutput (Join-Path $LOG_DIR "backend.out.log") `
        -RedirectStandardError  (Join-Path $LOG_DIR "backend.err.log") `
        -PassThru -WindowStyle Hidden
    # poll the app-root /health (no DB hit) so we don't race the Neon cold-start (~8s)
    $ok = Wait-For { (Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } 30
    if ($ok) { Write-Host "[ OK ] Backend ready (PID $($be.Id)) — http://localhost:8000" }
    else     { Write-Warning "Backend not ready in 20s — see $LOG_DIR\backend.err.log" }
}

# ---- frontend ---------------------------------------------------------------
if (Test-PortListening 5173) {
    Write-Warning "Port 5173 already in use — frontend may already be running. Skipping."
} else {
    Write-Host "[ .. ] Starting frontend on :5173"
    # Vite picks this up via frontend/.env.local too; setting it here as well so the
    # script works even if .env.local is missing.
    $env:VITE_API_PROXY = "http://localhost:8000"
    $fe = Start-Process -FilePath "npm.cmd" `
        -ArgumentList "run", "dev" `
        -WorkingDirectory $FRONTEND `
        -RedirectStandardOutput (Join-Path $LOG_DIR "frontend.out.log") `
        -RedirectStandardError  (Join-Path $LOG_DIR "frontend.err.log") `
        -PassThru -WindowStyle Hidden
    $ok = Wait-For { Test-PortListening 5173 } 25
    if ($ok) { Write-Host "[ OK ] Frontend ready (npm PID $($fe.Id)) — http://localhost:5173" }
    else     { Write-Warning "Frontend not ready in 25s — see $LOG_DIR\frontend.err.log" }
}

# ---- summary ----------------------------------------------------------------
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  RAG-RBAC running"                                -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Frontend:    http://localhost:5173"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  Swagger UI:  http://localhost:8000/docs"
Write-Host ""
Write-Host "  Demo logins (username / password):"
Write-Host "    admin    / admin123!      (all 4 access levels)"
Write-Host "    manager  / manager123!    (public + internal + confidential)"
Write-Host "    user     / user123!       (public + internal)"
Write-Host "    guest    / guest123!      (public only)"
Write-Host ""
Write-Host "  Logs: $LOG_DIR"
Write-Host "  Stop: .\stop.ps1"
Write-Host "================================================" -ForegroundColor Green
