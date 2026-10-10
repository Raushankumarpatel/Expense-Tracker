import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import mysql.connector
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from flask.json.provider import DefaultJSONProvider
from werkzeug.security import check_password_hash, generate_password_hash

from config import SECRET_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


class DecimalEncoder(json.JSONEncoder):
    """Convert Decimal → float and date/datetime → ISO string."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("cls", DecimalEncoder)
        return json.dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


app = Flask(__name__)
app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)
app.secret_key = SECRET_KEY


def get_db():
    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    return connection


def db_cursor(connection):
    """Return a dictionary cursor (rows accessible as dicts)."""
    return connection.cursor(dictionary=True)


def init_db():
    connection = get_db()
    cursor = db_cursor(connection)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(512) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('income','expense') NOT NULL,
            title VARCHAR(255) NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            category VARCHAR(100) NOT NULL,
            date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category VARCHAR(100) NOT NULL,
            monthly_limit DECIMAL(12,2) NOT NULL,
            UNIQUE KEY unique_user_cat (user_id, category),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            target_amount DECIMAL(12,2) NOT NULL,
            saved_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("SELECT id FROM users WHERE email = %s", ("admin@expense.com",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
            ("admin@expense.com", "Admin User", generate_password_hash("admin123")),
        )
    connection.commit()
    cursor.close()
    connection.close()


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


def login_required_json():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    email = request.form.get("email", "")
    if request.method == "POST":
        email = email.strip().lower()
        password = request.form.get("password", "")
        connection = get_db()
        cursor = db_cursor(connection)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        error = "Invalid email or password"
    return render_template("login.html", error=error, email=email)


@app.route("/signup", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    if request.method == "POST":
        name = name.strip()
        email = email.strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not name or not email or not password:
            error = "All fields are required"
        elif password != confirm_password:
            error = "Passwords do not match"
        else:
            connection = get_db()
            cursor = db_cursor(connection)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                error = "Email already exists"
                cursor.close()
                connection.close()
            else:
                cursor.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                    (email, name, generate_password_hash(password)),
                )
                connection.commit()
                new_id = cursor.lastrowid
                cursor.close()
                connection.close()
                session["user_id"] = new_id
                session["email"] = email
                return redirect(url_for("dashboard"))
    return render_template("register.html", error=error, name=name, email=email)


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


@app.route("/api/profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    new_password = data.get("new_password", "").strip()
    current_password = data.get("current_password", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    if new_password:
        if not current_password:
            cursor.close()
            connection.close()
            return jsonify({"error": "Current password is required to change password"}), 400
        if not check_password_hash(user["password_hash"], current_password):
            cursor.close()
            connection.close()
            return jsonify({"error": "Current password is incorrect"}), 400
        cursor.execute(
            "UPDATE users SET name=%s, password_hash=%s WHERE id=%s",
            (name, generate_password_hash(new_password), session["user_id"]),
        )
    else:
        cursor.execute("UPDATE users SET name=%s WHERE id=%s", (name, session["user_id"]))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Profile updated successfully"})


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "SELECT id, type, title, amount, category, date, notes FROM transactions WHERE user_id = %s ORDER BY date DESC, id DESC",
        (session["user_id"],),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    # Convert date objects to string and Decimal amounts to float for JSON serialization
    for row in rows:
        if hasattr(row.get("date"), "isoformat"):
            row["date"] = row["date"].isoformat()
        if row.get("amount") is not None:
            row["amount"] = float(row["amount"])
    return jsonify(rows)


@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    data = request.get_json() or {}
    tx_type = data.get("type")
    title = data.get("title", "").strip()
    category = data.get("category", "").strip()
    notes = data.get("notes", "").strip()
    date = data.get("date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400
    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Invalid type"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400
    if not category:
        return jsonify({"error": "Category is required"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "INSERT INTO transactions (user_id, type, title, amount, category, date, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (session["user_id"], tx_type, title, amount, category, date, notes),
    )
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return jsonify({"message": "Transaction created successfully", "id": new_id}), 201


@app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    data = request.get_json() or {}
    tx_type = data.get("type")
    title = data.get("title", "").strip()
    category = data.get("category", "").strip()
    notes = data.get("notes", "").strip()
    date = data.get("date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400
    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Invalid type"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400
    if not category:
        return jsonify({"error": "Category is required"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "UPDATE transactions SET type=%s, title=%s, amount=%s, category=%s, date=%s, notes=%s WHERE id=%s AND user_id=%s",
        (tx_type, title, amount, category, date, notes, transaction_id, session["user_id"]),
    )
    connection.commit()
    rowcount = cursor.rowcount
    cursor.close()
    connection.close()
    if rowcount == 0:
        return jsonify({"error": "Transaction not found or unauthorized"}), 404
    return jsonify({"message": "Transaction updated successfully"})


@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "DELETE FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, session["user_id"]),
    )
    connection.commit()
    rowcount = cursor.rowcount
    cursor.close()
    connection.close()
    if rowcount == 0:
        return jsonify({"error": "Transaction not found or unauthorized"}), 404
    return jsonify({"message": "Transaction deleted successfully"})


@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute("SELECT category, monthly_limit FROM budgets WHERE user_id = %s", (session["user_id"],))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    for row in rows:
        if row.get("monthly_limit") is not None:
            row["monthly_limit"] = float(row["monthly_limit"])
    return jsonify(rows)


@app.route("/api/budgets", methods=["POST"])
def set_budget():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    data = request.get_json() or {}
    category = data.get("category", "").strip()
    try:
        monthly_limit = float(data.get("monthly_limit"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400
    if not category:
        return jsonify({"error": "Category is required"}), 400
    if monthly_limit <= 0:
        return jsonify({"error": "Limit must be greater than zero"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "INSERT INTO budgets (user_id, category, monthly_limit) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE monthly_limit=%s",
        (session["user_id"], category, monthly_limit, monthly_limit),
    )
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Budget saved"})


@app.route("/api/budgets/<path:category>", methods=["DELETE"])
def delete_budget(category):
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute("DELETE FROM budgets WHERE user_id = %s AND category = %s", (session["user_id"], category))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Budget removed"})


@app.route("/api/goals", methods=["GET"])
def get_goals():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "SELECT id, name, target_amount, saved_amount FROM savings_goals WHERE user_id = %s", (session["user_id"],)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    for row in rows:
        for field in ("target_amount", "saved_amount"):
            if row.get(field) is not None:
                row[field] = float(row[field])
    return jsonify(rows)


@app.route("/api/goals", methods=["POST"])
def create_goal():
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    try:
        target_amount = float(data.get("target_amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid target amount"}), 400
    if not name:
        return jsonify({"error": "Goal name is required"}), 400
    if target_amount <= 0:
        return jsonify({"error": "Target must be greater than zero"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "INSERT INTO savings_goals (user_id, name, target_amount, saved_amount) VALUES (%s, %s, %s, 0)",
        (session["user_id"], name, target_amount),
    )
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return jsonify({"message": "Goal created", "id": new_id}), 201


@app.route("/api/goals/<int:goal_id>", methods=["PUT"])
def update_goal(goal_id):
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    data = request.get_json() or {}
    try:
        saved_amount = float(data.get("saved_amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400
    if saved_amount < 0:
        return jsonify({"error": "Amount cannot be negative"}), 400
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "UPDATE savings_goals SET saved_amount=%s WHERE id=%s AND user_id=%s",
        (saved_amount, goal_id, session["user_id"]),
    )
    connection.commit()
    rowcount = cursor.rowcount
    cursor.close()
    connection.close()
    if rowcount == 0:
        return jsonify({"error": "Goal not found"}), 404
    return jsonify({"message": "Goal updated"})


@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    unauthorized = login_required_json()
    if unauthorized:
        return unauthorized
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "DELETE FROM savings_goals WHERE id=%s AND user_id=%s", (goal_id, session["user_id"])
    )
    connection.commit()
    rowcount = cursor.rowcount
    cursor.close()
    connection.close()
    if rowcount == 0:
        return jsonify({"error": "Goal not found"}), 404
    return jsonify({"message": "Goal deleted"})


@app.route("/export/csv")
def export_csv():
    if "user_id" not in session:
        return redirect(url_for("login"))
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute(
        "SELECT date, type, title, category, amount, notes FROM transactions WHERE user_id = %s ORDER BY date DESC",
        (session["user_id"],),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Title", "Category", "Amount (INR)", "Notes"])
    for row in rows:
        writer.writerow([row["date"], row["type"], row["title"], row["category"], row["amount"], row["notes"]])
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expense_report.csv"
    return response


@app.route("/export/pdf")
def export_pdf():
    if "user_id" not in session:
        return redirect(url_for("login"))
    connection = get_db()
    cursor = db_cursor(connection)
    cursor.execute("SELECT name, email FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.execute(
        "SELECT date, type, title, category, amount, notes FROM transactions WHERE user_id = %s ORDER BY date DESC",
        (session["user_id"],),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Expense Report", styles["Title"]))
    elements.append(Paragraph(f"Account: {user['name']} ({user['email']})", styles["Normal"]))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 0.4*cm))

    total_income = sum(float(r["amount"]) for r in rows if r["type"] == "income")
    total_expense = sum(float(r["amount"]) for r in rows if r["type"] == "expense")
    summary_data = [
        ["Total Income", "Total Expenses", "Net Balance"],
        [f"INR {total_income:,.2f}", f"INR {total_expense:,.2f}", f"INR {(total_income - total_expense):,.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a5a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f4f1e9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9ded5")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("All Transactions", styles["Heading2"]))
    elements.append(Spacer(1, 0.2*cm))
    table_data = [["Date", "Type", "Title", "Category", "Amount (INR)", "Notes"]]
    for r in rows:
        table_data.append([str(r["date"]), r["type"].capitalize(), r["title"], r["category"], f"{float(r['amount']):,.2f}", r["notes"] or ""])
    tx_table = Table(table_data, colWidths=[2.2*cm, 1.8*cm, 4.5*cm, 3.5*cm, 2.8*cm, 2.2*cm])
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a5a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f4f1e9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9ded5")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (4, 1), (4, -1), "RIGHT"),
    ]))
    elements.append(tx_table)

    doc.build(elements)
    buf.seek(0)
    response = Response(buf.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=expense_report.pdf"
    return response


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
