from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "inventory_secret_key"

DATABASE = "inventory.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            category TEXT NOT NULL,
            low_stock_limit INTEGER NOT NULL
        )
    """)

    # Default login user
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    # Optional sample inventory data
    cursor.execute("SELECT COUNT(*) as count FROM inventory")
    count = cursor.fetchone()["count"]

    if count == 0:
        sample_items = [
            ("Chicken Fillet", 10, "Meat", 5),
            ("Fish Fillet", 4, "Seafood", 5),
            ("Potatoes", 20, "Vegetables", 8),
            ("Cooking Oil", 3, "Grocery", 4)
        ]
        cursor.executemany(
            "INSERT INTO inventory (product_name, quantity, category, low_stock_limit) VALUES (?, ?, ?, ?)",
            sample_items
        )

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["username"] = username
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()

    total_items = conn.execute("SELECT COUNT(*) as count FROM inventory").fetchone()["count"]

    low_stock_items = conn.execute(
        "SELECT * FROM inventory WHERE quantity <= low_stock_limit"
    ).fetchall()

    recent_items = conn.execute(
        "SELECT * FROM inventory ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_items=total_items,
        low_stock_items=low_stock_items,
        low_stock_count=len(low_stock_items),
        recent_items=recent_items
    )


@app.route("/inventory")
@login_required
def inventory():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("inventory.html", items=items)


@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()
        low_stock_limit = request.form.get("low_stock_limit", "").strip()

        if not product_name or not quantity or not category or not low_stock_limit:
            flash("All fields are required.", "error")
            return render_template("add_item.html")

        try:
            quantity = int(quantity)
            low_stock_limit = int(low_stock_limit)
        except ValueError:
            flash("Quantity and low stock limit must be numbers.", "error")
            return render_template("add_item.html")

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO inventory (product_name, quantity, category, low_stock_limit) VALUES (?, ?, ?, ?)",
            (product_name, quantity, category, low_stock_limit)
        )
        conn.commit()
        conn.close()

        flash("Inventory item added successfully.", "success")
        return redirect(url_for("inventory"))

    return render_template("add_item.html")


@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        conn.close()
        flash("Item not found.", "error")
        return redirect(url_for("inventory"))

    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()
        low_stock_limit = request.form.get("low_stock_limit", "").strip()

        if not product_name or not quantity or not category or not low_stock_limit:
            conn.close()
            flash("All fields are required.", "error")
            return render_template("edit_item.html", item=item)

        try:
            quantity = int(quantity)
            low_stock_limit = int(low_stock_limit)
        except ValueError:
            conn.close()
            flash("Quantity and low stock limit must be numbers.", "error")
            return render_template("edit_item.html", item=item)

        conn.execute("""
            UPDATE inventory
            SET product_name = ?, quantity = ?, category = ?, low_stock_limit = ?
            WHERE id = ?
        """, (product_name, quantity, category, low_stock_limit, item_id))
        conn.commit()
        conn.close()

        flash("Inventory item updated successfully.", "success")
        return redirect(url_for("inventory"))

    conn.close()
    return render_template("edit_item.html", item=item)


@app.route("/delete_item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    flash("Inventory item deleted successfully.", "success")
    return redirect(url_for("inventory"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)