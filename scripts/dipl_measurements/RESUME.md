# Diploma measurements — progress & how to resume

All scripts live in `scripts/dipl_measurements/`. Run them from `backend/` with the
venv python and `DEBUG=false`. Results are written to `scripts/dipl_measurements/results/`.

## Done
- **Point 0** — stand params captured → report §0. (`env_report.py`, `results/env_report.json`)
- **Point 1** — corpus expanded 5 → **37 docs / 298 chunks** (public 12 / internal 12 /
  confidential 8 / restricted 5, avg 854 words). (`seed_corpus.py` + `corpus_data.py`,
  `results/seed_log.txt`)
- **Point 4a** — 5-chunk **Seq Scan** EXPLAIN baseline captured BEFORE seeding →
  `results/explain_5chunks.txt` (Execution Time 4.394 ms).
- Report skeleton with §0,1,6,7,8 written → `docs/dipl_measurements_report.md`
  (§2,3,4.2,5 have PLACEHOLDER markers to fill from results JSON).

## Remaining (run in this order — Ollama serializes, so don't overlap)
```powershell
$env:DEBUG="false"; $env:PYTHONUNBUFFERED="1"
cd D:\KPI_University\4thYear\Sem2\Thesis\program\files\rag-rbac-app\backend
$py = ".\.venv\Scripts\python.exe"

# Point 2 (sequential latency) — MAY ALREADY BE RUNNING in background (task b3wn7efe0)
& $py ..\scripts\dipl_measurements\measure_latency.py   # ~7 min, -> results/latency_sequential.json

# Point 5 (quality, retrieval-only, ~1 min)
& $py ..\scripts\dipl_measurements\quality_metrics.py    # -> results/quality_metrics.json

# Point 3 (concurrency) — needs backend up on :8000 (task bpuqrmfmd already running)
& $py ..\scripts\dipl_measurements\measure_concurrency.py # -> results/concurrency.json

# Point 4b (synthetic HNSW test + auto-cleanup) — RUN LAST
& $py ..\scripts\dipl_measurements\hnsw_explain.py --synth 3000  # -> capture HNSW Index Scan plan
```

## After data is collected
Fill the 4 PLACEHOLDER blocks in `docs/dipl_measurements_report.md` from the result
JSONs (§2 latency, §3 concurrency, §4.2 HNSW, §5 quality), write the interpretation
paragraphs, and explain the concurrency result honestly (compare `server_ms` vs
`client_ms`; Ollama generation serializes on CPU).

## Background tasks left running (stop when done)
- `bpuqrmfmd` — uvicorn backend on 127.0.0.1:8000 (needed only for Point 3).
- `b3wn7efe0` — Point 2 latency run (let it finish; check its output file).
- Stop backend later with: `Get-NetTCPConnection -LocalPort 8000 -State Listen |
  %{ Stop-Process -Id $_.OwningProcess -Force }`

## Notes / decisions made
- Measurement stack = **local CPU Ollama + Neon cloud Postgres** (the app's real config;
  matches existing Ch.4 "Neon"). No Docker installed, no NVIDIA GPU → Point 6 documented
  as skipped.
- No application code was modified. Per-stage timing is obtained by a harness that
  replicates `RagService.search` step-by-step (`measure_latency.py`), so the
  "diploma-instrumentation" commit was not needed.
- Synthetic HNSW rows go into the real `chunks` table under sentinel document
  `00000000-0000-0000-0000-0000000000ff` and are DELETED automatically at the end of
  `hnsw_explain.py` (unless `--keep`).
- `test_queries.json` references relevant docs by **title** (resolved to UUIDs at runtime).
