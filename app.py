from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Add Expense
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]

        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            amount REAL,
            category TEXT,
            date TEXT
        )
        """)

        cursor.execute(
            "INSERT INTO expenses(title, amount, category, date) VALUES (?, ?, ?, ?)",
            (title, amount, category, date)
        )

        conn.commit()
        conn.close()

        return redirect("/view")

    return render_template("add_expense.html")


# View Expenses
@app.route("/view")
def view():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)

    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    conn.close()

    return render_template("view_expenses.html", expenses=expenses)


# Reports
@app.route("/reports")
def reports():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    cursor.execute("""
    SELECT category, SUM(amount)
    FROM expenses
    GROUP BY category
    """)

    category_data = cursor.fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total=total,
        category_data=category_data
    )


if __name__ == "__main__":
    app.run(debug=True)