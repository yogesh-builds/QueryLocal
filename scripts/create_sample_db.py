import random
import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect("data/shop.db")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT,
    signup_date DATE
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date  DATE,
    amount      REAL
);
""")

names = ["Asha", "Rahul", "Priya", "Vikram", "Neha",
         "Arjun", "Sneha", "Karan", "Divya", "Rohan"]
cities = ["Bengaluru", "Mumbai", "Delhi", "Chennai", "Pune"]

for i, name in enumerate(names, start=1):
    signup = date(2025, 1, 1) + timedelta(days=random.randint(0, 365))
    cur.execute("INSERT INTO customers VALUES (?, ?, ?, ?)",
                (i, name, random.choice(cities), str(signup)))

for order_id in range(1, 201):
    order_day = date.today() - timedelta(days=random.randint(0, 180))
    cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?)",
                (order_id, random.randint(1, 10), str(order_day),
                 round(random.uniform(200, 5000), 2)))

conn.commit()
conn.close()
print("Created data/shop.db")