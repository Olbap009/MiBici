"""Resume CSV de Locust y docker stats, y estima el costo unitario de referencia."""

import argparse
import csv
import json
import statistics
from pathlib import Path


def memory_mib(text):
    value = text.split("/")[0].strip()
    for unit, multiplier in (("GiB", 1024), ("MiB", 1), ("KiB", 1 / 1024), ("B", 1 / 1048576)):
        if value.endswith(unit):
            return float(value.removesuffix(unit)) * multiplier
    raise ValueError(f"Unidad de memoria desconocida: {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("reports/evidence/finops"))
    args = parser.parse_args()
    results = []
    for stats_path in sorted(args.folder.glob("u*_stats.csv")):
        with stats_path.open() as file:
            periodic = next(r for r in csv.DictReader(file) if r["Name"] == "Aggregated")
        users = int(stats_path.name.split("_")[0][1:])
        html = (args.folder / f"u{users}.html").read_text()
        final_report = json.JSONDecoder().raw_decode(html.split("window.templateArgs = ", 1)[1])[0]
        stats = next(r for r in final_report["requests_statistics"] if r["name"] == "Aggregated")
        (args.folder / f"u{users}_final.json").write_text(
            json.dumps(
                {
                    "start_time": final_report["start_time"],
                    "end_time": final_report["end_time"],
                    "host": final_report["host"],
                    "statistics": stats,
                    "periodic_csv_requests": int(periodic["Request Count"]),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        containers = {}
        for line in (args.folder / f"u{users}_resources.jsonl").read_text().splitlines():
            row = json.loads(line)
            name = row["Name"]
            containers.setdefault(name, {"cpu": [], "memory": []})
            containers[name]["cpu"].append(float(row["CPUPerc"].removesuffix("%")))
            containers[name]["memory"].append(memory_mib(row["MemUsage"]))
        resource_summary = {
            name: {
                "samples": len(values["cpu"]),
                "cpu_mean_percent": statistics.mean(values["cpu"]),
                "cpu_max_percent": max(values["cpu"]),
                "memory_mean_mib": statistics.mean(values["memory"]),
                "memory_max_mib": max(values["memory"]),
            }
            for name, values in containers.items()
        }
        rps = stats["total_rps"] - stats["total_fail_per_sec"]
        if rps <= 0:
            raise ValueError(
                "Se requieren respuestas exitosas para calcular costo por inferencia."
            )
        result = {
            "users": users,
            "requests": stats["num_requests"],
            "failures": stats["num_failures"],
            "error_rate_percent": 100 * stats["num_failures"] / stats["num_requests"],
            "rps": rps,
            "mean_ms": stats["avg_response_time"],
            "p50_ms": stats["median_response_time"],
            "p95_ms": stats["response_time_percentile_0.95"],
            "p99_ms": stats["response_time_percentile_0.99"],
            "resources": resource_summary,
            "usd_per_inference": (24 / 730 / 3600) / rps,
            "usd_per_1000_at_measured_rate": 1000 * (24 / 730 / 3600) / rps,
            "usd_per_1000_at_10pct_utilization": 1000 * (24 / 730 / 3600) / (0.1 * rps),
        }
        results.append(result)
    if len(results) < 2:
        raise ValueError("Faltan resultados de uno de los escenarios.")
    output = {
        "price_reference": {
            "service": "AWS Lightsail Linux/Unix con IPv4 público",
            "monthly_usd": 24,
            "memory_gb": 4,
            "vcpus": 2,
            "hours_per_month_assumed": 730,
            "source": "https://aws.amazon.com/lightsail/pricing/",
        },
        "scenarios": sorted(results, key=lambda row: row["users"]),
    }
    (args.folder / "summary.json").write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
