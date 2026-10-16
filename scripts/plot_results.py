"""Make charts from every benchmark CSV in results/.

Usage: python scripts/plot_results.py
Writes results/accuracy.png and results/accuracy_vs_speed.png
"""
import csv
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

RESULTS = Path("results")


def is_correct(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # gemini_gemini-3.5-flash-lite_50 -> gemini-3.5-flash-lite
    backend, rest = path.stem.split("_", 1)
    name = rest.rsplit("_", 1)[0].replace("_", ":")
    seconds = [float(r["seconds"]) for r in rows if r.get("seconds")]
    return {
        "name": name,
        "cloud": backend == "gemini",
        "n": len(rows),
        "accuracy": 100 * sum(is_correct(r["correct"]) for r in rows) / len(rows),
        "median_s": statistics.median(seconds) if seconds else 0,
    }


def main():
    runs = [load(p) for p in sorted(RESULTS.glob("*.csv"))]
    runs = [r for r in runs if r["n"] > 0]
    if not runs:
        print("No result CSVs found in results/")
        return
    runs.sort(key=lambda r: r["accuracy"])
    colors = ["#2a78d6" if r["cloud"] else "#1f9e6e" for r in runs]

    # Chart 1: accuracy per model
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(runs) + 1.5))
    bars = ax.barh([r["name"] for r in runs], [r["accuracy"] for r in runs], color=colors)
    ax.bar_label(bars, labels=[f"{r['accuracy']:.0f}%" for r in runs], padding=4)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Execution accuracy on Spider dev (%)")
    ax.set_title(f"Text-to-SQL accuracy ({runs[0]['n']} questions)  blue = cloud, green = local")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(RESULTS / "accuracy.png", dpi=150)

    # Chart 2: accuracy vs speed
    fig, ax = plt.subplots(figsize=(8, 5))
    for r, c in zip(runs, colors):
        ax.scatter(r["median_s"], r["accuracy"], s=90, color=c)
        ax.annotate(r["name"], (r["median_s"], r["accuracy"]),
                    textcoords="offset points", xytext=(8, 4))
    ax.set_xlabel("Median seconds per question (lower is better)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy vs speed")
    ax.set_ylim(0, 100)
    ax.set_xlim(left=0)
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(RESULTS / "accuracy_vs_speed.png", dpi=150)

    for r in sorted(runs, key=lambda r: -r["accuracy"]):
        print(f"{r['name']:<28} {r['accuracy']:5.1f}%  median {r['median_s']:.1f}s")
    print("Saved results/accuracy.png and results/accuracy_vs_speed.png")


if __name__ == "__main__":
    main()
