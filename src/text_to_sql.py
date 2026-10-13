import re
import sqlite3
import time
from datetime import date

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

MODEL = "models/gemini-3.8-flash"
DB_PATH = "data/shop.db"
MAX_RETRIES = 2

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


def ask_model(prompt):
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return clean_sql(response.text)


def generate_sql(question, schema):
    prompt = f"""You are an expert SQLite analyst.
Given this database schema:

{schema}

Write ONE SQLite SELECT query that answers the question below.
Return only the SQL. No explanation, no markdown.
Today's date is {date.today()}.

Question: {question}"""
    return ask_model(prompt)


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
    return ask_model(prompt)


def run_query(db_path, sql):
    # Open the database read-only so a bad query can never change data.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return columns, rows


def answer(question, schema):
    """Generate SQL, check it, run it, and retry with the error if it fails."""
    sql = generate_sql(question, schema)
    for attempt in range(MAX_RETRIES + 1):
        try:
            safe_sql = validate_sql(sql)
            columns, rows = run_query(DB_PATH, safe_sql)
            return safe_sql, columns, rows
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"Attempt {attempt + 1} failed ({e}). Asking the model to fix it...")
            sql = fix_sql(question, schema, sql, str(e))


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
            sql, columns, rows = answer(question, schema)
            print(f"\nSQL ({time.time() - start:.1f}s):\n{sql}\n")
            print(" | ".join(columns))
            for row in rows[:20]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > 20:
                print(f"... and {len(rows) - 20} more rows")
        except Exception as e:
            print(f"Could not answer: {e}")


if __name__ == "__main__":
    main()