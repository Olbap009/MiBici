"""Genera las gráficas a partir del historial de Locust y las muestras de recursos."""

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from summarize import memory_mib

EVIDENCE = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/evidence/finops")
rows = json.loads((EVIDENCE / "summary.json").read_text())["scenarios"]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.2,
    }
)
fig, axes = plt.subplots(3, 1, figsize=(8.4, 6.6), sharex=True)
for row, color in zip(rows, ["#23499A", "#008A87"]):
    with (EVIDENCE / f"u{row['users']}_stats_history.csv").open() as file:
        history = [x for x in csv.DictReader(file) if x["Name"] == "Aggregated"]
    start = float(history[0]["Timestamp"])
    x = [float(h["Timestamp"]) - start for h in history]
    axes[0].plot(
        x, [float(h["Requests/s"]) for h in history], color=color, label=f"{row['users']} usuarios"
    )
    axes[1].plot(
        x, [float(h["95%"]) if h["95%"] != "N/A" else float("nan") for h in history], color=color
    )
    axes[2].plot(x, [float(h["Failures/s"]) for h in history], color=color)
for ax, title in zip(axes, ["Peticiones / s", "Latencia p95 (ms)", "Fallos / s"]):
    ax.set_ylabel(title)
axes[0].legend(loc="best")
axes[-1].set_xlabel("Tiempo desde la primera muestra (s)")
fig.tight_layout()
fig.savefig(EVIDENCE / "locust_performance.png", dpi=170)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
for row, color in zip(rows, ["#23499A", "#008A87"]):
    samples = [
        json.loads(l)
        for l in (EVIDENCE / f"u{row['users']}_resources.jsonl").read_text().splitlines()
    ]
    samples = [s for s in samples if s["Name"] == "mibici-p2-api"]
    axes[0].plot(
        [s["elapsed_seconds"] for s in samples],
        [float(s["CPUPerc"].rstrip("%")) for s in samples],
        color=color,
        label=f"{row['users']} usuarios",
    )
    axes[1].plot(
        [s["elapsed_seconds"] for s in samples],
        [memory_mib(s["MemUsage"]) for s in samples],
        color=color,
    )
axes[0].set_ylabel("CPU de la API (%)")
axes[1].set_ylabel("Memoria API (MiB)")
for ax in axes:
    ax.set_xlabel("Tiempo desde el inicio (s)")
axes[0].legend()
fig.tight_layout()
fig.savefig(EVIDENCE / "resources.png", dpi=170)
plt.close(fig)
