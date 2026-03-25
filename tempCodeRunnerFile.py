# =============================
# SIMPLE HOME DELIVERY APP (FLASK + SQLITE)
# Shop: Sayali Agarbati & Chai Patti
# =============================

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret123'

# =============================
# DATABASE SETUP
# =============================

def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price REAL,
                    quantity TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    qty INTEGER,
                    customer_name TEXT,
                    address TEXT
                )''')

    conn.commit()
    conn.close()

init_db()

# =============================
# HOME PAGE (CUSTOMER)
# =============================

@app.route('/')
def home():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('home.html', products=products)

# =============================
# ADD PRODUCT (ADMIN)
# =============================

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']

        conn = sqlite3.connect('shop.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
        conn.commit()
        conn.close()

        flash('Product Added Successfully!')
        return redirect(url_for('add_product'))

    return render_template('add_product.html')

# =============================
# PLACE ORDER
# =============================

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = c.fetchone()

    if request.method == 'POST':
        qty = request.form['qty']
        name = request.form['name']
        address = request.form['address']

        c.execute("INSERT INTO orders (product_name, qty, customer_name, address) VALUES (?, ?, ?, ?)",
                  (product[1], qty, name, address))
        conn.commit()
        conn.close()

        print("\n🔥 NEW ORDER RECEIVED 🔥")
        print(f"Product: {product[1]}, Qty: {qty}, Customer: {name}")

        flash('Order Placed Successfully!')
        return redirect(url_for('home'))

    conn.close()
    return render_template('order.html', product=product)

# =============================
# VIEW ORDERS (ADMIN)
# =============================

@app.route('/orders')
def view_orders():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    orders = c.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

# =============================
# RUN APP
# =============================

if __name__ == '__main__':
    app.run(debug=True)

# =============================
# NEXT STEP (IMPORTANT)
# =============================
# 1. Create 'templates' folder
# 2. Add HTML files:
#    - home.html
#    - add_product.html
#    - order.html
#    - orders.html
# 3. Run: python app.py
# 4. Open: http://127.0.0.1:5000

# =============================
# FUTURE IMPROVEMENTS
# =============================
# - Add WhatsApp notification (Twilio API)
# - Add Payment (UPI / Razorpay)
# - Convert into Android App (using Flask + APK)
# - Add Login system (Admin control)
# =============================
