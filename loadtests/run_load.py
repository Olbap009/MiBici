"""Ejecuta Locust y muestrea docker stats durante cada escenario de concurrencia."""

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1:18080")
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--users", type=int, nargs="+", default=[5, 25])
    parser.add_argument("--output", type=Path, default=Path("reports/evidence/finops"))
    args = parser.parse_args()
    if args.seconds < 1 or any(users < 1 for users in args.users):
        parser.error("La duración y la cantidad de usuarios deben ser positivas.")
    args.output.mkdir(parents=True, exist_ok=True)
    containers = ["mibici-p2-api", "mibici-postgres", "mibici-grafana", "mibici-nginx"]
    for users in args.users:
        prefix = args.output / f"u{users}"
        started = time.time()
        command = [
            sys.executable,
            "-m",
            "locust",
            "-f",
            "loadtests/locustfile.py",
            "--headless",
            "--host",
            args.host,
            "--users",
            str(users),
            "--spawn-rate",
            str(users),
            "--run-time",
            f"{args.seconds}s",
            "--csv",
            str(prefix),
            "--csv-full-history",
            "--html",
            str(prefix) + ".html",
        ]
        with (
            prefix.with_suffix(".log").open("w") as log,
            (args.output / f"u{users}_resources.jsonl").open("w") as stats,
        ):
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            try:
                while process.poll() is None:
                    measured = datetime.now(UTC).isoformat()
                    output = subprocess.check_output(
                        ["docker", "stats", "--no-stream", "--format", "{{json .}}", *containers],
                        text=True,
                    )
                    for line in output.splitlines():
                        sample = json.loads(line)
                        sample.update(timestamp=measured, elapsed_seconds=time.time() - started)
                        stats.write(json.dumps(sample) + "\n")
                    stats.flush()
                    time.sleep(2)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=15)
            if process.returncode:
                raise RuntimeError(
                    f"Locust terminó con código {process.returncode}. Consulta {log.name}"
                )
        print(f"Escenario con {users} usuarios terminado", flush=True)


if __name__ == "__main__":
    main()
