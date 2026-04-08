"""
stress_test.py — Stress test para la aplicacion monolito
Uso: python3 stress_test.py [url] [requests] [concurrency]
Ejemplo: python3 stress_test.py http://localhost:5000 500 50
"""
import threading
import requests
import time
import sys
from collections import Counter

BASE_URL  = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
TOTAL_REQ = int(sys.argv[2]) if len(sys.argv) > 2 else 200
WORKERS   = int(sys.argv[3]) if len(sys.argv) > 3 else 20

results  = []
lock     = threading.Lock()

def worker(n):
    endpoint = f"{BASE_URL}/api/stress"
    try:
        start = time.time()
        r = requests.get(endpoint, timeout=10)
        elapsed = round((time.time() - start) * 1000, 2)
        with lock:
            results.append({"status": r.status_code, "ms": elapsed})
    except Exception as e:
        with lock:
            results.append({"status": "error", "ms": -1})

print(f"\n{'='*50}")
print(f"  STRESS TEST")
print(f"  URL:         {BASE_URL}/api/stress")
print(f"  Requests:    {TOTAL_REQ}")
print(f"  Concurrency: {WORKERS} threads")
print(f"{'='*50}\n")

start_total = time.time()

threads = []
for i in range(TOTAL_REQ):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)

# Launch in batches of WORKERS
for i in range(0, len(threads), WORKERS):
    batch = threads[i:i+WORKERS]
    for t in batch:
        t.start()
    for t in batch:
        t.join()

total_time = round(time.time() - start_total, 2)

# ── Stats ──────────────────────────────────────────────────────────
ok      = [r for r in results if r["status"] == 200]
errors  = [r for r in results if r["status"] != 200]
times   = [r["ms"] for r in ok]

print(f"{'='*50}")
print(f"  RESULTS")
print(f"  Total requests : {len(results)}")
print(f"  Successful     : {len(ok)}")
print(f"  Failed         : {len(errors)}")
print(f"  Total time     : {total_time}s")
print(f"  Req/sec        : {round(len(results)/total_time, 1)}")
if times:
    print(f"  Avg latency    : {round(sum(times)/len(times), 1)} ms")
    print(f"  Min latency    : {min(times)} ms")
    print(f"  Max latency    : {max(times)} ms")
print(f"  Status codes   : {dict(Counter(str(r['status']) for r in results))}")
print(f"{'='*50}\n")
