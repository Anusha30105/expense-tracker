from flask import Flask, render_template, request, redirect, session, Response, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import csv
import os
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key"

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "expenses.db"
)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def create_table():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            amount REAL,
            category TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


create_table()


# =========================================================
# SIGN UP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect("/signup")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect("/signup")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect("/signup")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )

        if cur.fetchone():
            conn.close()
            flash("That username is already taken.", "danger")
            return redirect("/signup")

        password_hash = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users(username, password_hash) VALUES(?, ?)",
            (username, password_hash)
        )

        conn.commit()
        conn.close()

        flash("Account created successfully! Please log in.", "success")

        return redirect("/login")

    return render_template("signup.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username=?",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):

            session["user_id"] = user[0]
            session["user"] = user[1]

            return redirect("/")

        flash("Invalid username or password.", "danger")

        return redirect("/login")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Total Expense
    cur.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    total = cur.fetchone()[0]

    # Transaction Count
    cur.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    count = cur.fetchone()[0]

    # Category Count
    cur.execute("""
        SELECT COUNT(DISTINCT category)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    categories = cur.fetchone()[0]

    # Highest Expense
    cur.execute("""
        SELECT IFNULL(MAX(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    highest = cur.fetchone()[0]

    # Lowest Expense
    cur.execute("""
        SELECT IFNULL(MIN(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    lowest = cur.fetchone()[0]

    # Average Expense
    cur.execute("""
        SELECT IFNULL(AVG(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    average = round(cur.fetchone()[0], 2)

    # Current Month Expense
    cur.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        AND strftime('%Y-%m', date)=strftime('%Y-%m', 'now')
    """, (user_id,))

    month_total = cur.fetchone()[0]

    # =====================================================
    # RECENT 5 EXPENSES
    # =====================================================

    cur.execute("""
        SELECT title, amount, category, date
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,))

    recent_expenses = cur.fetchall()

    # =====================================================
    # CATEGORY-WISE EXPENSE DATA
    # =====================================================

    cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (user_id,))

    category_data = cur.fetchall()

    category_labels = [row[0] for row in category_data]
    category_amounts = [row[1] for row in category_data]

    # =====================================================
    # MONTHLY EXPENSE TREND
    # =====================================================

    cur.execute("""
        SELECT
            strftime('%Y-%m', date),
            SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY strftime('%Y-%m', date)
    """, (user_id,))

    monthly_data = cur.fetchall()

    monthly_labels = [row[0] for row in monthly_data]
    monthly_amounts = [row[1] for row in monthly_data]

    conn.close()

    return render_template(
        "index.html",
        total=total,
        count=count,
        categories=categories,
        highest=highest,
        lowest=lowest,
        average=average,
        month_total=month_total,
        recent_expenses=recent_expenses,
        monthly_labels=monthly_labels,
        monthly_amounts=monthly_amounts,
        category_labels=category_labels,
        category_amounts=category_amounts
    )


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route("/add", methods=["GET", "POST"])
def add():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO expenses(
                user_id,
                title,
                amount,
                category,
                date
            )
            VALUES(?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            title,
            amount,
            category,
            date
        ))

        conn.commit()
        conn.close()

        flash("Expense added successfully!", "success")

        return redirect("/view")

    return render_template("add_expense.html")


# =========================================================
# VIEW EXPENSES
# =========================================================

@app.route("/view")
def view():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    search = request.args.get("search", "")
    month = request.args.get("month", "")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT id, title, amount, category, date
        FROM expenses
        WHERE user_id=?
    """

    params = [user_id]

    if search:

        query += """
            AND (
                title LIKE ?
                OR category LIKE ?
            )
        """

        params.extend([
            f"%{search}%",
            f"%{search}%"
        ])

    if month:

        query += """
            AND strftime('%Y-%m', date)=?
        """

        params.append(month)

    query += " ORDER BY date DESC"

    cur.execute(query, params)

    expenses = cur.fetchall()

    conn.close()

    return render_template(
        "view_expense.html",
        expenses=expenses,
        search=search,
        selected_month=month
    )


# =========================================================
# EDIT EXPENSE
# =========================================================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM expenses
        WHERE id=? AND user_id=?
    """, (id, user_id))

    expense = cur.fetchone()

    if not expense:

        conn.close()

        flash("Expense not found.", "danger")

        return redirect("/view")

    if request.method == "POST":

        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]

        cur.execute("""
            UPDATE expenses
            SET title=?,
                amount=?,
                category=?,
                date=?
            WHERE id=? AND user_id=?
        """, (
            title,
            amount,
            category,
            date,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        flash("Expense updated successfully!", "success")

        return redirect("/view")

    conn.close()

    return render_template(
        "edit_expense.html",
        expense=expense
    )


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route("/delete/<int:id>")
def delete(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM expenses
        WHERE id=? AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash("Expense deleted successfully!", "success")

    return redirect("/view")


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Total
    cur.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    total = cur.fetchone()[0]

    # Count
    cur.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    count = cur.fetchone()[0]

    # Category data
    cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
    """, (user_id,))

    pie_data = cur.fetchall()

    categories = [row[0] for row in pie_data]
    amounts = [row[1] for row in pie_data]

    # Monthly trend
    cur.execute("""
        SELECT
            strftime('%Y-%m', date),
            SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY strftime('%Y-%m', date)
    """, (user_id,))

    trend = cur.fetchall()

    months = [row[0] for row in trend]
    totals = [row[1] for row in trend]

    conn.close()

    return render_template(
        "reports.html",
        total=total,
        count=count,
        categories=categories,
        amounts=amounts,
        months=months,
        totals=totals
    )


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/export")
def export():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, amount, category, date
        FROM expenses
        WHERE user_id=?
    """, (session["user_id"],))

    expenses = cur.fetchall()

    conn.close()

    class Echo:

        def write(self, value):
            return value

    def generate():

        data = csv.writer(Echo())

        yield data.writerow([
            "ID",
            "Title",
            "Amount",
            "Category",
            "Date"
        ])

        for row in expenses:
            yield data.writerow(row)

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=expenses.csv"
        }
    )


# =========================================================
# EXPORT PDF
# =========================================================

@app.route("/export_pdf")
def export_pdf():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, amount, category, date
        FROM expenses
        WHERE user_id=?
        ORDER BY date DESC
    """, (user_id,))

    expenses = cur.fetchall()

    cur.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))

    total = cur.fetchone()[0]

    conn.close()

    def clean(value):

        return (
            str(value)
            .encode("latin-1", "ignore")
            .decode("latin-1")
            .strip()
        )

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)

    pdf.cell(
        0,
        12,
        "Expense Report",
        ln=True,
        align="C"
    )

    pdf.set_font("Helvetica", "", 10)

    pdf.cell(
        0,
        8,
        f"Total Expense: Rs. {total:,.2f}",
        ln=True,
        align="C"
    )

    pdf.ln(6)

    col_widths = [15, 55, 30, 45, 35]

    headers = [
        "ID",
        "Title",
        "Amount",
        "Category",
        "Date"
    ]

    pdf.set_font("Helvetica", "B", 10)

    pdf.set_fill_color(30, 58, 95)

    pdf.set_text_color(255, 255, 255)

    for header, width in zip(headers, col_widths):

        pdf.cell(
            width,
            10,
            header,
            border=1,
            align="C",
            fill=True
        )

    pdf.ln()

    pdf.set_font("Helvetica", "", 10)

    pdf.set_text_color(0, 0, 0)

    for row in expenses:

        row_id, title, amount, category, date = row

        pdf.cell(
            col_widths[0],
            9,
            clean(row_id),
            border=1,
            align="C"
        )

        pdf.cell(
            col_widths[1],
            9,
            clean(title)[:28],
            border=1
        )

        pdf.cell(
            col_widths[2],
            9,
            f"{amount:,.2f}",
            border=1,
            align="R"
        )

        pdf.cell(
            col_widths[3],
            9,
            clean(category),
            border=1
        )

        pdf.cell(
            col_widths[4],
            9,
            clean(date),
            border=1,
            align="C"
        )

        pdf.ln()

    if not expenses:

        pdf.cell(
            sum(col_widths),
            9,
            "No expenses found.",
            border=1,
            align="C"
        )

        pdf.ln()

    pdf_bytes = pdf.output(dest="S")

    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                "attachment; filename=expenses.pdf"
        }
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)