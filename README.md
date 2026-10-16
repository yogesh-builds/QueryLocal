# QueryLocal

**Ask your database in plain English, privately and offline.**

QueryLocal turns a natural-language question into a SQL query, runs it safely on a SQLite database, and shows the result. It works with a cloud model (Google Gemini) or a fully local model (Ollama), so you can choose between accuracy and privacy.


![QueryLocal demo](docs/demo.png)

## Features

* **Two backends, one switch:** Gemini (cloud) or any Ollama model (local, works offline).
* **Safe by design:** only a single read-only `SELECT` is allowed. Queries run on a read-only database connection, and anything that writes or changes data is blocked.
* **Self-correction:** if the SQL fails to run, the error is sent back to the model, which gets up to two chances to fix it.
* **Handles vague and impossible questions:** the model states its assumption ("top customers" means highest total order amount), asks a clarifying question, or says the data cannot answer the question, instead of guessing silently.
* **Streamlit web app and a terminal mode.**
* **Benchmarked** on the Spider text-to-SQL dataset (results below).

## How it works

```
question + table definitions
        |
        v
  Gemini or Ollama  -->  JSON: ok (SQL + assumption) | clarify | impossible
        |
        v
  safety check (single SELECT only, forbidden keywords blocked)
        |
        v
  run on a read-only SQLite connection
        |
   error? --> send the error back to the model, retry up to 2 times
        |
        v
  show SQL, assumptions and result table
```

## Benchmark: cloud vs local

Both models answered the **same 50 random questions** from the Spider dev set (fixed seed 42). A question counts as correct only if the generated SQL returns exactly the same rows as the reference SQL (execution accuracy). Timings come from a laptop with **no dedicated GPU**, so the local model ran on the CPU.

||Gemini (`gemini-3.5-flash-lite`)|Local (`qwen2.5-coder:3b` via Ollama)|
|-|-|-|
|Correct|**44/50 (88%)**|35/50 (70%)|
|Average time per question|9.7 s|10.9 s|
|Median time per question|6.5 s|8.3 s|
|Ran but returned wrong rows|6|12|
|SQL error after retries|0|3|
|Needs internet / sends data to a third party|yes|**no**|
|Cost|free tier, rate limited|**free, unlimited**|

Gemini got 10 questions right that the local model missed. The local model got 1 right that Gemini missed. Both missed 5. Per-question results are in [`results/`](results/).

### Where the small local model falls short

Looking at the questions only Gemini answered correctly:

1. **Wrong tables or columns (about half of the misses).** Three queries failed outright with invented columns (for example `no such column: T2.owner\_id`). Others used the wrong table, such as joining a rankings table instead of using the match year, or counting rows in `model\_list` instead of `car\_names`.
2. **Multi-table joins.** For "the airport with the least flights" the local model grouped the airports table alone and never joined flights, so it counted airports instead of flights.
3. **Negation and set logic.** For "students who do not have a cat" it used `LEFT JOIN ... WHERE pettype != 'cat'`, which still returns students who own a cat and another pet. The correct form needs `NOT IN` or `EXCEPT`.

Part of the gap is the metric being strict, not real errors: for example, one logically correct local query was marked wrong because it omitted a duplicated column that the reference answer repeats. The true gap is probably a bit smaller than 18 points.

### Caveats

* 50 questions is a small sample, so treat the percentages as approximate (roughly plus or minus 9 points). The difference between the models is still unlikely to be chance (10 vs 1 disagreements, sign test p of about 0.01).
* Gemini timings include network time and free-tier rate-limit waits, so the speed comparison is rough.
* This Gemini model was chosen partly because larger models had very small free daily quotas (20 requests per day).

## Getting started

Requires Python 3.12 and, for local models, [Ollama](https://ollama.com).

```bash
git clone https://github.com/yogesh-builds/QueryLocal.git
cd QueryLocal
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file with your Gemini key (get one at aistudio.google.com):

```
GEMINI\_API\_KEY=your\_key\_here
```

Create the sample database and start the app:

```bash
python scripts/create\_sample\_db.py
streamlit run src/app.py
```

For the local model:

```bash
ollama pull qwen2.5-coder:3b
```

then pick **Ollama (local)** in the app sidebar.

### Reproduce the benchmark

Download the Spider dataset from https://yale-lily.github.io/spider and unzip it into `data/spider/` (git-ignored). Then:

```bash
python scripts/benchmark.py --backend ollama --n 50
python scripts/benchmark.py --backend gemini --n 50 --delay 8
python scripts/compare.py results/<gemini\_file>.csv results/<ollama\_file>.csv
```

## Project structure

```
src/text\_to\_sql.py            engine: prompts, safety check, retries, both backends
src/app.py                    Streamlit interface
scripts/create\_sample\_db.py   builds the demo shop database
scripts/benchmark.py          runs the Spider benchmark
scripts/compare.py            compares two result files
results/                      benchmark CSVs and comparison table
```

## Ideas for next steps

* Add foreign keys and a few sample rows to the prompt, which should help the small model pick correct tables and joins.
* Try a larger local model and measure the accuracy and speed trade-off.
* Add few-shot examples for set operations and negation.
* Support databases beyond SQLite.

## License

MIT

