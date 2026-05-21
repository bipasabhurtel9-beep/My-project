from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

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
            product_name TEXT,
            quantity INTEGER,
            category TEXT,
            low_stock_limit INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            quantity_sold INTEGER,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def dashboard():

    conn = get_db_connection()

    total_items = conn.execute("""
        SELECT COUNT(*) FROM inventory
    """).fetchone()[0]

    low_stock_items = conn.execute("""
        SELECT * FROM inventory
        WHERE quantity <= low_stock_limit
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_items=total_items,
        low_stock_items=low_stock_items,
        low_stock_count=len(low_stock_items)
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/inventory")
def inventory():

    search = request.args.get("search", "")

    conn = get_db_connection()

    if search:
        items = conn.execute("""
            SELECT * FROM inventory
            WHERE product_name LIKE ?
        """, (f"%{search}%",)).fetchall()
    else:
        items = conn.execute("""
            SELECT * FROM inventory
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "inventory.html",
        items=items,
        search=search
    )


@app.route("/add_item", methods=["GET", "POST"])
def add_item():

    if request.method == "POST":

        product_name = request.form["product_name"]
        quantity = request.form["quantity"]
        category = request.form["category"]
        low_stock_limit = request.form["low_stock_limit"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO inventory
            (product_name, quantity, category, low_stock_limit)
            VALUES (?, ?, ?, ?)
        """, (
            product_name,
            quantity,
            category,
            low_stock_limit
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("inventory"))

    return render_template("add_item.html")


@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):

    conn = get_db_connection()

    item = conn.execute("""
        SELECT * FROM inventory
        WHERE id=?
    """, (item_id,)).fetchone()

    if request.method == "POST":

        product_name = request.form["product_name"]
        quantity = request.form["quantity"]
        category = request.form["category"]
        low_stock_limit = request.form["low_stock_limit"]

        conn.execute("""
            UPDATE inventory
            SET product_name=?,
                quantity=?,
                category=?,
                low_stock_limit=?
            WHERE id=?
        """, (
            product_name,
            quantity,
            category,
            low_stock_limit,
            item_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("inventory"))

    conn.close()

    return render_template(
        "edit_item.html",
        item=item
    )


@app.route("/delete_item/<int:item_id>", methods=["POST"])
def delete_item(item_id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM inventory
        WHERE id=?
    """, (item_id,))

    conn.commit()
    conn.close()

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
        """, (
            new_quantity,
            item_id
        ))

        conn.execute("""
            INSERT INTO sales
            (product_name, quantity_sold)
            VALUES (?, ?)
        """, (
            item["product_name"],
            quantity_sold
        ))

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

    return render_template(
        "sales.html",
        sales_records=sales_records
    )


if __name__ == "__main__":

    init_db()

    app.run(debug=True)