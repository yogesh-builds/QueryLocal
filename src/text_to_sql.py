import re
import sqlite3
from datetime import date

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

MODEL = "models/gemini-3.8-flash"   # use the name that worked in hello_gemini.py
DB_PATH = "data/shop.db"


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


def generate_sql(question, schema):
    prompt = f"""You are an expert SQLite analyst.
Given this database schema:

{schema}

Write ONE SQLite SELECT query that answers the question below.
Return only the SQL. No explanation, no markdown.
Today's date is {date.today()}.

Question: {question}"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return clean_sql(response.text)


def run_query(db_path, sql):
    # Open the database read-only so a bad query can never change data.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return columns, rows


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
            sql = generate_sql(question, schema)
            print(f"\nSQL:\n{sql}\n")
            columns, rows = run_query(DB_PATH, sql)
            print(" | ".join(columns))
            for row in rows[:20]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > 20:
                print(f"... and {len(rows) - 20} more rows")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()