# =============================================================================
#  RAG-RBAC — stop backend + frontend
# -----------------------------------------------------------------------------
#  Finds whatever is listening on :8000 and :5173 and kills the whole process
#  tree (taskkill /T) — important for the frontend, since `npm run dev` spawns
#  cmd -> npm -> node and we need to kill all of them.
#
#  Ollama is intentionally NOT touched (it's a shared user-managed service).
# =============================================================================

function Stop-PortTree([int]$port, [string]$label) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "[ -- ] $label (:$port) not running"
        return
    }
    # Get-NetTCPConnection may return multiple rows (IPv4 + IPv6 etc.); dedupe PIDs
    $pids = @($conn | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($procId in $pids) {
        Write-Host "[ .. ] Stopping $label (:$port, PID $procId + children)"
        & taskkill /F /T /PID $procId *> $null
    }
    Start-Sleep -Milliseconds 500
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Warning "  $label port $port still listening — manual cleanup may be needed"
    } else {
        Write-Host "[ OK ] $label stopped"
    }
}

Write-Host "=== RAG-RBAC stop ===" -ForegroundColor Cyan
Stop-PortTree 8000 "Backend"
Stop-PortTree 5173 "Frontend"
Write-Host ""
