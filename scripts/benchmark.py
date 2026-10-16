"""Benchmark QueryLocal on a random sample of the Spider dev set.

Usage (from the project root):
    python scripts/benchmark.py --backend gemini --n 5
    python scripts/benchmark.py --backend ollama --n 100
Re-running the same command resumes where it stopped.
"""
import argparse
import csv
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
import text_to_sql as t2s  # noqa: E402

SPIDER = Path("data/spider")
RESULTS = Path("results")
FIELDS = ["idx", "db_id", "question", "gold_sql", "pred_sql",
          "status", "correct", "seconds", "error"]


def summarize(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return
    n = len(rows)
    correct = sum(r["correct"] == "True" for r in rows)
    avg = sum(float(r["seconds"]) for r in rows) / n
    print(f"\n{path.name}: {correct}/{n} correct ({100 * correct / n:.1f}%), "
          f"average {avg:.1f}s per question")
    print("Statuses:", dict(Counter(r["status"] for r in rows)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["gemini", "ollama"], required=True)
    ap.add_argument("--n", type=int, default=100, help="number of questions")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--delay", type=float, default=0, help="seconds to pause between questions")
    ap.add_argument("--retry-errors", action="store_true", help="re-run rows that ended in an error")
    ap.add_argument("--model", help="Ollama model to test, e.g. qwen3.5:4b")
    args = ap.parse_args()
    if args.model:
        t2s.OLLAMA_MODEL = args.model

    examples = json.load(open(SPIDER / "dev.json", encoding="utf-8"))
    sample = random.Random(args.seed).sample(examples, args.n)

    model = t2s.MODEL if args.backend == "gemini" else t2s.OLLAMA_MODEL
    safe_model = model.replace("/", "_").replace(":", "_")
    RESULTS.mkdir(exist_ok=True)
    out_path = RESULTS / f"{args.backend}_{safe_model}_{args.n}.csv"
    if args.retry_errors and out_path.exists():
        with open(out_path, newline="", encoding="utf-8") as f:
            kept = [r for r in csv.DictReader(f) if r["status"] != "error"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(kept)

    done = set()
    if out_path.exists():
        with open(out_path, newline="", encoding="utf-8") as f:
            done = {int(r["idx"]) for r in csv.DictReader(f)}
    new_file = not out_path.exists()

    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        for i, ex in enumerate(sample):
            if i in done:
                continue
            db_path = SPIDER / "database" / ex["db_id"] / f"{ex['db_id']}.sqlite"
            start = time.time()
            status, error, pred_sql, correct = "ok", "", "", False
            try:
                schema = t2s.get_schema(db_path)
                result = t2s.answer(ex["question"], schema, args.backend, db_path=db_path)
                status = result["status"]
                if status == "ok":
                    pred_sql = result["sql"]
                    _, gold_rows = t2s.run_query(db_path, ex["query"])
                    correct = (Counter(map(tuple, result["rows"]))
                               == Counter(map(tuple, gold_rows)))
            except Exception as e:
                if "PerDay" in str(e):
                    print("Daily Gemini quota used up. Try again after it resets, or use another model.")
                    sys.exit(1)
                status, error = "error", str(e)[:200]
            seconds = time.time() - start

            writer.writerow({
                "idx": i, "db_id": ex["db_id"], "question": ex["question"],
                "gold_sql": ex["query"], "pred_sql": pred_sql, "status": status,
                "correct": correct, "seconds": f"{seconds:.2f}", "error": error,
            })
            f.flush()
            print(f"[{i + 1}/{len(sample)}] {'OK ' if correct else 'BAD'} "
                  f"{seconds:.1f}s {ex['question']}")
            if args.delay:
                time.sleep(args.delay)

    summarize(out_path)


if __name__ == "__main__":
    main()