import json
import re
import sqlite3
import time
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

MODEL = "models/gemini-3.8-flash"
DB_PATH = "data/shop.db"
MAX_RETRIES = 2
MAX_CLARIFY_ROUNDS = 2

FORBIDDEN = ["drop", "delete", "update", "insert", "alter", "create",
             "replace", "attach", "detach", "pragma", "vacuum", "truncate"]


def get_schema(db_path):
    """Read the CREATE TABLE statements so the model knows the tables and columns."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    conn.close()
    return "\n\n".join(r[0] for r in rows)


def clean_sql(text):
    """Remove markdown fences (```sql ... ```) if the model added them."""
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def validate_sql(sql):
    """Raise ValueError unless sql is a single read-only SELECT query."""
    body = sql.strip().rstrip(";").strip()
    if not body:
        raise ValueError("Empty query.")
    if ";" in body:
        raise ValueError("Only one statement is allowed.")
    if not re.match(r"^(select|with)\b", body, flags=re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", body, flags=re.IGNORECASE):
            raise ValueError(f"Blocked keyword: {word.upper()}")
    return body


def ask_model(prompt, as_json=False):
    config = types.GenerateContentConfig(
        response_mime_type="application/json" if as_json else "text/plain"
    )
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )
    return response.text.strip()


def interpret(question, schema):
    """Ask the model to answer with SQL, a clarifying question, or 'impossible'."""
    prompt = f"""You are an expert SQLite analyst.
Database schema:

{schema}

Today's date is {date.today()}.

Reply with JSON only, in exactly one of these shapes:
{{"status": "ok", "sql": "<one SQLite SELECT query>", "assumption": "<what you assumed, or empty string>"}}
{{"status": "clarify", "question": "<one short question for the user>"}}
{{"status": "impossible", "reason": "<why this database cannot answer it>"}}

Rules:
- Use "clarify" ONLY when the question could reasonably mean two or more things that
  would give clearly different results and no sensible default exists.
- If a sensible default exists (for example "top customers" = highest total order
  amount, "recent" = last 30 days), use "ok" and state the default in "assumption".
- Use "impossible" when the needed tables or columns do not exist in the schema.
- SQL must be a single read-only SELECT.

Question: {question}"""
    text = ask_model(prompt, as_json=True)
    try:
        result = json.loads(text)
        if result.get("status") not in ("ok", "clarify", "impossible"):
            raise ValueError("bad status")
        return result
    except (json.JSONDecodeError, ValueError, AttributeError):
        # The model ignored the format: treat the reply as plain SQL.
        return {"status": "ok", "sql": clean_sql(text), "assumption": ""}


def fix_sql(question, schema, bad_sql, error):
    prompt = f"""You are an expert SQLite analyst.
Schema:

{schema}

Question: {question}

This SQL query failed:
{bad_sql}

Error message: {error}

Write a corrected ONE SQLite SELECT query.
Return only the SQL. No explanation, no markdown.
Today's date is {date.today()}."""
    return clean_sql(ask_model(prompt))


def run_query(db_path, sql):
    # Open the database read-only so a bad query can never change data.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return columns, rows


def answer(question, schema):
    """Return a dict with status 'ok', 'clarify' or 'impossible'.

    'ok' also has sql, columns, rows, assumption.
    'clarify' has question. 'impossible' has reason.
    Raises an exception if the SQL still fails after all retries.
    """
    result = interpret(question, schema)
    if result["status"] != "ok":
        return result

    sql = clean_sql(result.get("sql", ""))
    for attempt in range(MAX_RETRIES + 1):
        try:
            safe_sql = validate_sql(sql)
            columns, rows = run_query(DB_PATH, safe_sql)
            return {
                "status": "ok",
                "sql": safe_sql,
                "columns": columns,
                "rows": rows,
                "assumption": result.get("assumption", ""),
            }
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"Attempt {attempt + 1} failed ({e}). Asking the model to fix it...")
            sql = fix_sql(question, schema, sql, str(e))


def show_result(result, seconds):
    if result["status"] == "impossible":
        print(f"\nI can't answer that from this data: {result['reason']}")
        return
    if result["status"] == "clarify":
        print("\nStill unclear. Try rephrasing your question with more detail.")
        return
    print(f"\nSQL ({seconds:.1f}s):\n{result['sql']}\n")
    if result["assumption"]:
        print(f"Assumption: {result['assumption']}\n")
    print(" | ".join(result["columns"]))
    for row in result["rows"][:20]:
        print(" | ".join(str(v) for v in row))
    if len(result["rows"]) > 20:
        print(f"... and {len(result['rows']) - 20} more rows")


def main():
    schema = get_schema(DB_PATH)
    print("QueryLocal ready. Ask a question about your data (type 'quit' to exit).")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        try:
            start = time.time()
            result = answer(question, schema)
            for _ in range(MAX_CLARIFY_ROUNDS):
                if result["status"] != "clarify":
                    break
                reply = input(f"\nI need one detail: {result['question']}\nYour answer: ").strip()
                question = f"{question}\nUser clarification: {reply}"
                result = answer(question, schema)
            show_result(result, time.time() - start)
        except Exception as e:
            print(f"Could not answer: {e}")


if __name__ == "__main__":
    main()