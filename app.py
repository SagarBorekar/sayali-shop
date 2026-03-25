from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3, razorpay ,  matplotlib.pyplot as plt,io, base64, os, random

app = Flask(__name__)
razorpay_client = razorpay.Client(auth=("rzp_test_SV9Fk3oCCQ37ts", "ZWdR3Y39A1yXE86bL6wu3YJS"))
app.secret_key = "secret"

UPLOAD_FOLDER = "static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# DATABASE
def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        otp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        p250 REAL,
        p500 REAL,
        p1kg REAL,
        image TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        weight TEXT,
        qty INTEGER,
        total REAL,
        phone TEXT,
        address TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# LOGIN
import random

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        otp = str(random.randint(1000,9999))

        session['otp'] = otp
        session['phone'] = phone

        print("OTP:", otp)  # 👉 Shows in console

        return render_template('verify.html')

    return render_template('login.html')

@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        otp = request.form['otp']
        phone = session.get('temp')

        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT otp FROM users WHERE phone=?",(phone,))
        real = c.fetchone()[0]
        conn.close()

        if otp == real:
            session['user'] = phone
            return redirect('/')

    return render_template('verify.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# HOME
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    data = c.fetchall()
    conn.close()

    return render_template('home.html', products=data)

# ADD PRODUCT
@app.route('/add_product', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        p250 = request.form['p250']
        p500 = request.form['p500']
        p1kg = request.form['p1kg']
        img = request.files['image']

        filename = img.filename
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("INSERT INTO products (name,p250,p500,p1kg,image) VALUES (?,?,?,?,?)",
                  (name,p250,p500,p1kg,filename))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_product.html')

# DELETE PRODUCT
@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# EDIT PRODUCT
@app.route('/edit_product/<int:id>', methods=['GET','POST'])
def edit_product(id):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        p250 = request.form['p250']
        p500 = request.form['p500']
        p1kg = request.form['p1kg']

        c.execute("UPDATE products SET name=?,p250=?,p500=?,p1kg=? WHERE id=?",
                  (name,p250,p500,p1kg,id))
        conn.commit()
        conn.close()
        return redirect('/')

    c.execute("SELECT * FROM products WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()

    return render_template('edit_product.html', p=data)

# ORDER
@app.route('/order/<int:id>', methods=['GET','POST'])
def order(id):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    p = c.fetchone()

    if request.method == 'POST':
        weight = request.form['weight']
        qty = int(request.form['qty'])
        address = request.form['address']

        if weight == "250g": price = p[2]
        elif weight == "500g": price = p[3]
        elif weight == "1kg": price = p[4]

        total = price * qty

        c.execute("INSERT INTO orders (product,weight,qty,total,phone,address) VALUES (?,?,?,?,?,?)",
                  (p[1],weight,qty,total,session['user'],address))
        conn.commit()
        conn.close()

        return redirect('/')

    conn.close()
    return render_template('order.html', p=p)

# VIEW ORDERS
@app.route('/orders')
def orders():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    data = c.fetchall()
    conn.close()
    return render_template('orders.html', orders=data)

# DELETE ORDER
@app.route('/delete_order/<int:id>')
def delete_order(id):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/orders')

@app.route('/admin')
def admin():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()

    # BASIC STATS
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]

    c.execute("SELECT SUM(total) FROM orders")
    revenue = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]

    # 📈 DAILY SALES
    c.execute("SELECT date('now'), SUM(total) FROM orders")
    sales_data = c.fetchall()

    labels = [row[0] for row in sales_data]
    values = [row[1] or 0 for row in sales_data]

    plt.figure()
    plt.plot(labels, values)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph = base64.b64encode(img.getvalue()).decode()

    # 🏆 TOP PRODUCTS
    c.execute("SELECT product, SUM(qty) as total_qty FROM orders GROUP BY product ORDER BY total_qty DESC LIMIT 5")
    top_products = c.fetchall()

    # 📦 WEIGHT DISTRIBUTION
    c.execute("SELECT weight, COUNT(*) FROM orders GROUP BY weight")
    weight_data = c.fetchall()

    conn.close()

    return render_template("admin.html",
                           total_orders=total_orders,
                           revenue=revenue,
                           total_products=total_products,
                           graph=graph,
                           top_products=top_products,
                           weight_data=weight_data)


# ================= CART SYSTEM =================

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    weight = request.form['weight']
    qty = int(request.form['qty'])

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    p = c.fetchone()
    conn.close()

    if weight == "250g": price = p[2]
    elif weight == "500g": price = p[3]
    elif weight == "1kg": price = p[4]

    total = price * qty

    item = {
        "name": p[1],
        "weight": weight,
        "qty": qty,
        "total": total
    }

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    cart.append(item)
    session['cart'] = cart

    return redirect('/')


@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(item['total'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)


@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', [])

    total_amount = sum(item['total'] for item in cart)
    amount = int(total_amount * 100)  # convert to paise

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template("payment.html",
                           order_id=order['id'],
                           amount=amount,
                           key_id="rzp_test_SV9Fk3oCCQ37ts")

@app.route('/payment_success', methods=['POST'])
def payment_success():
    cart = session.get('cart', [])
    phone = session['user']
    address = request.form.get('address', '')

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()

    for item in cart:
        c.execute("INSERT INTO orders (product,weight,qty,total,phone,address) VALUES (?,?,?,?,?,?)",
                  (item['name'], item['weight'], item['qty'], item['total'], phone, address))

    conn.commit()
    conn.close()

    session['cart'] = []

    return "✅ Payment Successful! Order Placed"

    # DELETE ITEM FROM CART
@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    cart = session.get('cart', [])

    if 0 <= index < len(cart):
        cart.pop(index)

    session['cart'] = cart
    return redirect('/cart')

# RUN
if __name__ == "__main__":
    app.run(debug=True)
