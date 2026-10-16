"""Compare two benchmark CSVs and write results/comparison.md.

Usage (from the project root):
    python scripts/compare.py results/FIRST_FILE.csv results/SECOND_FILE.csv
"""
import csv
import statistics
import sys
from collections import Counter
from pathlib import Path


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {int(r["idx"]): r for r in csv.DictReader(f)}


def summarize(rows):
    vals = list(rows.values())
    n = len(vals)
    correct = sum(r["correct"] == "True" for r in vals)
    secs = [float(r["seconds"]) for r in vals]
    status = Counter(r["status"] for r in vals)
    wrong = sum(r["status"] == "ok" and r["correct"] != "True" for r in vals)
    return {
        "Correct": f"{correct}/{n} ({100 * correct / n:.1f}%)",
        "Average seconds per question": f"{statistics.mean(secs):.1f}",
        "Median seconds per question": f"{statistics.median(secs):.1f}",
        "Ran but returned wrong rows": str(wrong),
        "SQL error after retries": str(status.get("error", 0)),
        "Asked to clarify or said impossible": str(status.get("clarify", 0) + status.get("impossible", 0)),
    }


def one_line(text):
    return " ".join(text.split())


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python scripts/compare.py FIRST.csv SECOND.csv")
    paths = [Path(p) for p in sys.argv[1:]]
    data = [load(p) for p in paths]
    names = [p.stem for p in paths]
    sums = [summarize(d) for d in data]

    lines = ["# Benchmark comparison", "",
             f"| Metric | {names[0]} | {names[1]} |", "|---|---|---|"]
    for key in sums[0]:
        lines.append(f"| {key} | {sums[0][key]} | {sums[1][key]} |")

    common = sorted(set(data[0]) & set(data[1]))
    for a, b in ((0, 1), (1, 0)):
        lines += ["", f"## Correct only for {names[a]}", ""]
        found = False
        for i in common:
            ra, rb = data[a][i], data[b][i]
            if ra["correct"] == "True" and rb["correct"] != "True":
                found = True
                other = rb["pred_sql"] or rb["error"] or rb["status"]
                lines += [f"- **{ra['question']}**",
                          f"  - correct SQL: `{one_line(ra['gold_sql'])}`",
                          f"  - {names[b]}: `{one_line(other)}`"]
        if not found:
            lines.append("None.")

    both_wrong = [i for i in common
                  if data[0][i]["correct"] != "True" and data[1][i]["correct"] != "True"]
    lines += ["", f"## Wrong for both models ({len(both_wrong)})", ""]
    for i in both_wrong:
        lines.append(f"- {data[0][i]['question']}")

    text = "\n".join(lines) + "\n"
    Path("results/comparison.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()