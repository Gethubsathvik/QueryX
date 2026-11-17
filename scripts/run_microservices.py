"""Start all five services as local processes (works on Windows, Linux and macOS).

    python scripts/run_microservices.py

Ports: gateway 8000 (public), query 8001, data 8002, history 8003, chart 8004.
Set QUERYX_HOST=0.0.0.0 to let other devices (e.g. an Android phone) reach the gateway.
Press Ctrl+C to stop everything.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (name, uvicorn target, port); the gateway starts last
SERVICES = [
    ("history", "services.history_service.main:app", 8003),
    ("data", "services.data_service.main:app", 8002),
    ("chart", "services.chart_service.main:app", 8004),
    ("query", "services.query_service.main:app", 8001),
    ("gateway", "services.gateway.main:app", 8000),
]


def main() -> int:
    env = os.environ.copy()
    env.setdefault("QUERY_SERVICE_URL", "http://127.0.0.1:8001")
    env.setdefault("DATA_SERVICE_URL", "http://127.0.0.1:8002")
    env.setdefault("HISTORY_SERVICE_URL", "http://127.0.0.1:8003")
    env.setdefault("CHART_SERVICE_URL", "http://127.0.0.1:8004")
    env.setdefault("QUERYX_INTERNAL_TOKEN", "dev-internal-token")  # change for anything beyond local dev
    public_host = env.get("QUERYX_HOST", "127.0.0.1")

    procs: list[subprocess.Popen] = []
    # Treat a termination signal like Ctrl+C so the `finally` block stops every child service.
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        for name, target, port in SERVICES:
            host = public_host if name == "gateway" else "127.0.0.1"  # internal services stay local
            procs.append(subprocess.Popen(
                [sys.executable, "-m", "uvicorn", target, "--host", host, "--port", str(port)],
                cwd=ROOT, env=env))
            print(f"started {name:<8} on http://{host}:{port}")
            time.sleep(0.8)
        print("\nOpen http://localhost:8000  (Ctrl+C to stop)")
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
        print("a service exited; shutting down the rest")
        return 1
    except KeyboardInterrupt:
        print("\nstopping services...")
        return 0
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    sys.exit(main())
