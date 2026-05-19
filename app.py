from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "inventory_secret_key"

DATABASE = "inventory.db"


# ---------------- DATABASE CONNECTION ---------------- #

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATABASE SETUP ---------------- #

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # default admin
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    # sample data
    cursor.execute("SELECT COUNT(*) as count FROM inventory")
    count = cursor.fetchone()["count"]

    if count == 0:
        sample_items = [
            ("Chicken Fillet", 10, "Meat", 5),
            ("Fish Fillet", 4, "Seafood", 5),
            ("Potatoes", 20, "Vegetables", 8),
            ("Cooking Oil", 3, "Grocery", 4)
        ]

        cursor.executemany("""
            INSERT INTO inventory (product_name, quantity, category, low_stock_limit)
            VALUES (?, ?, ?, ?)
        """, sample_items)

    conn.commit()
    conn.close()


# ---------------- LOGIN REQUIRED ---------------- #

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()
        conn.close()

        if user:
            session["username"] = username
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()

    total_items = conn.execute("SELECT COUNT(*) as count FROM inventory").fetchone()["count"]

    low_stock_items = conn.execute("""
        SELECT * FROM inventory
        WHERE quantity <= low_stock_limit
    """).fetchall()

    recent_items = conn.execute("""
        SELECT * FROM inventory
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    recent_sales = conn.execute("""
        SELECT * FROM sales
        ORDER BY sale_date DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_items=total_items,
        low_stock_items=low_stock_items,
        low_stock_count=len(low_stock_items),
        recent_items=recent_items,
        recent_sales=recent_sales
    )


@app.route("/inventory")
@login_required
def inventory():
    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:
        items = conn.execute("""
            SELECT * FROM inventory
            WHERE product_name LIKE ?
            ORDER BY id DESC
        """, ('%' + search + '%',)).fetchall()
    else:
        items = conn.execute("""
            SELECT * FROM inventory
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template("inventory.html", items=items, search=search)


@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()
        low_stock_limit = request.form.get("low_stock_limit", "").strip()

        if not product_name or not quantity or not category or not low_stock_limit:
            flash("All fields required.", "error")
            return render_template("add_item.html")

        try:
            quantity = int(quantity)
            low_stock_limit = int(low_stock_limit)
        except ValueError:
            flash("Numbers only for quantity.", "error")
            return render_template("add_item.html")

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO inventory (product_name, quantity, category, low_stock_limit)
            VALUES (?, ?, ?, ?)
        """, (product_name, quantity, category, low_stock_limit))
        conn.commit()
        conn.close()

        flash("Item added.", "success")
        return redirect(url_for("inventory"))

    return render_template("add_item.html")


@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    conn = get_db_connection()

    item = conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()

    if not item:
        conn.close()
        flash("Item not found.", "error")
        return redirect(url_for("inventory"))

    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()
        low_stock_limit = request.form.get("low_stock_limit", "").strip()

        conn.execute("""
            UPDATE inventory
            SET product_name = ?, quantity = ?, category = ?, low_stock_limit = ?
            WHERE id = ?
        """, (product_name, int(quantity), category, int(low_stock_limit), item_id))

        conn.commit()
        conn.close()

        flash("Updated.", "success")
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

    flash("Deleted.", "success")
    return redirect(url_for("inventory"))


@app.route("/sell_item/<int:item_id>", methods=["POST"])
@login_required
def sell_item(item_id):
    quantity_sold = request.form.get("quantity_sold", "").strip()

    if not quantity_sold:
        flash("Enter quantity.", "error")
        return redirect(url_for("inventory"))

    try:
        quantity_sold = int(quantity_sold)
    except ValueError:
        flash("Invalid number.", "error")
        return redirect(url_for("inventory"))

    conn = get_db_connection()

    item = conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()

    if not item:
        conn.close()
        flash("Item not found.", "error")
        return redirect(url_for("inventory"))

    if quantity_sold > item["quantity"]:
        conn.close()
        flash("Not enough stock.", "error")
        return redirect(url_for("inventory"))

    new_qty = item["quantity"] - quantity_sold

    conn.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))

    conn.execute("""
        INSERT INTO sales (product_name, quantity_sold)
        VALUES (?, ?)
    """, (item["product_name"], quantity_sold))

    conn.commit()
    conn.close()

    flash("Sale recorded.", "success")
    return redirect(url_for("inventory"))


@app.route("/sales")
@login_required
def sales():
    conn = get_db_connection()

    records = conn.execute("""
        SELECT * FROM sales
        ORDER BY sale_date DESC
    """).fetchall()

    conn.close()

    return render_template("sales.html", sales_records=records)


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True) 