from flask import Flask, render_template_string

app = Flask(__name__)

# Dummy inventory data
inventory = [
    {"name": "Burger Buns", "qty": 10, "price": 5},
    {"name": "Chips", "qty": 20, "price": 3},
    {"name": "Paper", "qty": 15, "price": 2}
]

@app.route("/")
def home():
    html = "<h1>Inventory Dashboard of Orana Takeaway </h1><table border=1 style='border-collapse: collapse;'>"
    html += "<tr><th>Item</th><th>Quantity</th><th>Price</th></tr>"
    for item in inventory:
        html += f"<tr><td>{item['name']}</td><td>{item['qty']}</td><td>${item['price']}</td></tr>"
    html += "</table>"
    return html

if __name__ == "__main__":
    app.run(debug=True)