"""Point 3: concurrent vs sequential load through the real HTTP API.

Requires the backend running on http://localhost:8000 (DEBUG=false recommended).
Logs in as admin, then runs the SAME 10 distinct queries twice:
  (A) sequentially  — baseline, one after another;
  (B) concurrently  — all dispatched at once via asyncio.gather.

For every request we record BOTH:
  * client_ms  — wall-clock the client waited for the HTTP response;
  * server_ms  — RagService's own elapsed_ms from the JSON body (time spent
                 inside the request handler);
plus HTTP status and number of sources. We also record the total wall-clock of
each mode (start of first request -> end of last). Comparing client_ms vs
server_ms and concurrent vs sequential is what explains the "parallel looks
faster" artifact.
"""
import asyncio
import json
import statistics
import time

import _common  # noqa: F401
import httpx

BASE = "http://localhost:8000"
API = "/api/v1"

QUERIES = [
    "What is the company's data retention policy?",
    "How much paid vacation do employees get?",
    "What is the code review process for engineers?",
    "How are production incidents handled on call?",
    "How often are API keys and secrets rotated?",
    "What health insurance and benefits are offered?",
    "How do I submit an expense reimbursement?",
    "What is the git branching and release process?",
    "What are the rules against harassment at work?",
    "How are database migrations managed safely?",
]

PARAMS = {"top_k": 5, "threshold": 0.4, "hybrid": True, "generate_answer": True}


async def login(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login/json",
        json={"username": "admin", "password": "admin123!"},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def do_query(client: httpx.AsyncClient, token: str, q: str) -> dict:
    t = time.perf_counter()
    r = await client.post(
        f"{API}/search",
        json={"query": q, **PARAMS},
        headers={"Authorization": f"Bearer {token}"},
    )
    client_ms = (time.perf_counter() - t) * 1000
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    return {
        "query": q,
        "status": r.status_code,
        "client_ms": round(client_ms, 1),
        "server_ms": body.get("elapsed_ms"),
        "n_sources": len(body.get("sources", [])),
        "answer_chars": len(body.get("answer") or ""),
    }


def summarize(rows: list[dict], key: str) -> dict:
    vals = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    if not vals:
        return {}
    return {
        "mean": round(statistics.mean(vals), 1),
        "median": round(statistics.median(vals), 1),
        "min": round(min(vals), 1),
        "max": round(max(vals), 1),
    }


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=600) as client:
        token = await login(client)
        print("Logged in as admin.")

        # --- (A) sequential ---
        print("\n[A] Sequential (10 distinct queries) ...")
        t0 = time.perf_counter()
        seq = []
        for q in QUERIES:
            r = await do_query(client, token, q)
            seq.append(r)
            print(f"  {r['status']} client={r['client_ms']:>8.1f}ms "
                  f"server={r['server_ms']}ms src={r['n_sources']}  {q[:40]}")
        seq_wall = (time.perf_counter() - t0) * 1000

        # small gap to respect the 30/min search rate limit window
        print("  (pausing 5s before concurrent batch)")
        await asyncio.sleep(5)

        # --- (B) concurrent ---
        print("\n[B] Concurrent (10 distinct queries, asyncio.gather) ...")
        t0 = time.perf_counter()
        con = await asyncio.gather(*(do_query(client, token, q) for q in QUERIES))
        con_wall = (time.perf_counter() - t0) * 1000
        for r in con:
            print(f"  {r['status']} client={r['client_ms']:>8.1f}ms "
                  f"server={r['server_ms']}ms src={r['n_sources']}  {r['query'][:40]}")

    out = {
        "params": PARAMS,
        "sequential": {
            "wall_ms": round(seq_wall, 1),
            "requests": seq,
            "client_ms": summarize(seq, "client_ms"),
            "server_ms": summarize(seq, "server_ms"),
            "ok": sum(1 for r in seq if r["status"] == 200),
        },
        "concurrent": {
            "wall_ms": round(con_wall, 1),
            "requests": con,
            "client_ms": summarize(con, "client_ms"),
            "server_ms": summarize(con, "server_ms"),
            "ok": sum(1 for r in con if r["status"] == 200),
        },
    }
    print("\n=== SUMMARY ===")
    print(f"Sequential wall-clock: {seq_wall/1000:6.1f}s  | per-req client mean {out['sequential']['client_ms'].get('mean')}ms"
          f" server mean {out['sequential']['server_ms'].get('mean')}ms  ok={out['sequential']['ok']}/10")
    print(f"Concurrent wall-clock: {con_wall/1000:6.1f}s  | per-req client mean {out['concurrent']['client_ms'].get('mean')}ms"
          f" server mean {out['concurrent']['server_ms'].get('mean')}ms  ok={out['concurrent']['ok']}/10")

    with open("../scripts/dipl_measurements/results/concurrency.json", "w") as f:
        json.dump(out, f, indent=2)
    print("Saved -> results/concurrency.json")


if __name__ == "__main__":
    asyncio.run(main())
