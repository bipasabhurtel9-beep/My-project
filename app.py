from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3

app = Flask(__name__)
app.secret_key = "inventory_secret_key"

DATABASE = "inventory.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            category TEXT NOT NULL,
            low_stock_limit INTEGER NOT NULL,
            unit_price REAL DEFAULT 0
        )
    """)

    try:
        conn.execute("ALTER TABLE inventory ADD COLUMN unit_price REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def dashboard():
    conn = get_db_connection()

    total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    total_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

    total_inventory_value = conn.execute("""
        SELECT SUM(quantity * unit_price) FROM inventory
    """).fetchone()[0] or 0

    low_stock_items = conn.execute("""
        SELECT * FROM inventory
        WHERE quantity <= low_stock_limit
    """).fetchall()

    recent_sales = conn.execute("""
        SELECT * FROM sales
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_items=total_items,
        total_sales=total_sales,
        total_inventory_value=total_inventory_value,
        low_stock_count=len(low_stock_items),
        low_stock_items=low_stock_items,
        recent_sales=recent_sales
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login successful.")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    flash("Logged out.")
    return redirect(url_for("login"))


@app.route("/inventory")
def inventory():
    search = request.args.get("search", "")
    category = request.args.get("category", "")

    conn = get_db_connection()

    categories = conn.execute("""
        SELECT DISTINCT category FROM inventory
        ORDER BY category
    """).fetchall()

    if search and category:
        items = conn.execute("""
            SELECT * FROM inventory
            WHERE product_name LIKE ? AND category=?
            ORDER BY id DESC
        """, (f"%{search}%", category)).fetchall()
    elif search:
        items = conn.execute("""
            SELECT * FROM inventory
            WHERE product_name LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%",)).fetchall()
    elif category:
        items = conn.execute("""
            SELECT * FROM inventory
            WHERE category=?
            ORDER BY id DESC
        """, (category,)).fetchall()
    else:
        items = conn.execute("""
            SELECT * FROM inventory
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "inventory.html",
        items=items,
        search=search,
        category=category,
        categories=categories
    )


@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        product_name = request.form["product_name"]
        quantity = request.form["quantity"]
        category = request.form["category"]
        low_stock_limit = request.form["low_stock_limit"]
        unit_price = request.form["unit_price"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO inventory
            (product_name, quantity, category, low_stock_limit, unit_price)
            VALUES (?, ?, ?, ?, ?)
        """, (product_name, quantity, category, low_stock_limit, unit_price))

        conn.commit()
        conn.close()

        flash("Item added successfully.")
        return redirect(url_for("inventory"))

    return render_template("add_item.html")


@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    conn = get_db_connection()

    item = conn.execute("""
        SELECT * FROM inventory
        WHERE id=?
    """, (item_id,)).fetchone()

    if item is None:
        conn.close()
        flash("Item not found.")
        return redirect(url_for("inventory"))

    if request.method == "POST":
        product_name = request.form["product_name"]
        quantity = request.form["quantity"]
        category = request.form["category"]
        low_stock_limit = request.form["low_stock_limit"]
        unit_price = request.form["unit_price"]

        conn.execute("""
            UPDATE inventory
            SET product_name=?,
                quantity=?,
                category=?,
                low_stock_limit=?,
                unit_price=?
            WHERE id=?
        """, (product_name, quantity, category, low_stock_limit, unit_price, item_id))

        conn.commit()
        conn.close()

        flash("Item updated successfully.")
        return redirect(url_for("inventory"))

    conn.close()
    return render_template("edit_item.html", item=item)


@app.route("/delete_item/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    conn = get_db_connection()

    conn.execute("""
        DELETE FROM inventory
        WHERE id=?
    """, (item_id,))

    conn.commit()
    conn.close()

    flash("Item deleted successfully.")
    return redirect(url_for("inventory"))


@app.route("/sell_item/<int:item_id>", methods=["POST"])
def sell_item(item_id):
    quantity_sold = int(request.form["quantity_sold"])

    conn = get_db_connection()

    item = conn.execute("""
        SELECT * FROM inventory
        WHERE id=?
    """, (item_id,)).fetchone()

    if item and quantity_sold <= item["quantity"]:
        new_quantity = item["quantity"] - quantity_sold

        conn.execute("""
            UPDATE inventory
            SET quantity=?
            WHERE id=?
        """, (new_quantity, item_id))

        conn.execute("""
            INSERT INTO sales
            (product_name, quantity_sold)
            VALUES (?, ?)
        """, (item["product_name"], quantity_sold))

        flash("Sale recorded successfully.")
    else:
        flash("Sale failed. Not enough stock.")

    conn.commit()
    conn.close()

    return redirect(url_for("inventory"))


@app.route("/sales")
def sales():
    conn = get_db_connection()

    sales_records = conn.execute("""
        SELECT * FROM sales
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("sales.html", sales_records=sales_records)


@app.route("/reports")
def reports():
    conn = get_db_connection()

    total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    total_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

    total_inventory_value = conn.execute("""
        SELECT SUM(quantity * unit_price) FROM inventory
    """).fetchone()[0] or 0

    low_stock_items = conn.execute("""
        SELECT * FROM inventory
        WHERE quantity <= low_stock_limit
    """).fetchall()

    sales_records = conn.execute("""
        SELECT * FROM sales
        ORDER BY id DESC
    """).fetchall()

    category_data = conn.execute("""
        SELECT category,
               COUNT(*) AS total_items,
               SUM(quantity) AS total_quantity,
               SUM(quantity * unit_price) AS total_value
        FROM inventory
        GROUP BY category
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_items=total_items,
        total_sales=total_sales,
        total_inventory_value=total_inventory_value,
        low_stock_items=low_stock_items,
        sales_records=sales_records,
        category_data=category_data
    )


@app.route("/category_report")
def category_report():
    conn = get_db_connection()

    category_data = conn.execute("""
        SELECT category,
               COUNT(*) AS total_items,
               SUM(quantity) AS total_quantity,
               SUM(quantity * unit_price) AS total_value
        FROM inventory
        GROUP BY category
    """).fetchall()

    conn.close()

    return render_template("category_report.html", category_data=category_data)


@app.route("/export_sales")
def export_sales():
    conn = get_db_connection()

    sales_records = conn.execute("""
        SELECT * FROM sales
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    csv_data = "ID,Product Name,Quantity Sold,Sale Date\n"

    for sale in sales_records:
        csv_data += f"{sale['id']},{sale['product_name']},{sale['quantity_sold']},{sale['sale_date']}\n"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=sales_report.csv"}
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)