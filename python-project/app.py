from flask import Flask, render_template, request, redirect

app = Flask(__name__)

inventory = []

@app.route('/')
def home():
    return render_template('index.html', inventory=inventory)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    quantity = request.form['quantity']
    inventory.append({'name': name, 'quantity': quantity})
    return redirect('/')

@app.route('/delete/<int:item_index>')
def delete_item(item_index):
    if 0 <= item_index < len(inventory):
        inventory.pop(item_index)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)