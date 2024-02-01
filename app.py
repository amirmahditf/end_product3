from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, flash
import sqlite3
import json
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

conn_products = sqlite3.connect('products.db')
cursor_products = conn_products.cursor()
conn_products.commit()
conn_products.close()
conn_users = sqlite3.connect('users.db')
cursor_users = conn_users.cursor()
conn_users.commit()
conn_users.close()


@app.route('/home')
def index():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)


@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        stock = request.form.get('stock')

        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                       (name, price, stock))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add_product.html')


@app.route('/admin_home')
def admin_home():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('admin_home.html', products=products)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))

        conn.commit()
        conn.close()

        flash('محصول با موفقیت حذف شد!', 'success')

    except Exception as e:
        flash(f'خطا در حذف محصول: {str(e)}', 'error')

    return redirect(url_for('admin_home'))


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart_data = request.cookies.get('cart_data', '{}')
    cart_data = json.loads(cart_data)

    if str(product_id) in cart_data:
        cart_data[str(product_id)]['quantity'] += 1
    else:
        cart_data[str(product_id)] = {'quantity': 1}

    response = make_response(redirect(url_for('cart')))
    response.set_cookie('cart_data', json.dumps(cart_data))
    return response


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_data = request.cookies.get('cart_data', '{}')
    cart_data = json.loads(cart_data)

    if str(product_id) in cart_data:
        if cart_data[str(product_id)]['quantity'] > 1:
            cart_data[str(product_id)]['quantity'] -= 1
        else:
            del cart_data[str(product_id)]

    response = make_response(redirect(url_for('cart')))
    response.set_cookie('cart_data', json.dumps(cart_data))
    return response


@app.route('/cart')
def cart():
    cart_data = request.cookies.get('cart_data', '{}')
    cart_data = json.loads(cart_data)

    total_price = 0
    cart_items = {}

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    for product_id, details in cart_data.items():
        cursor.execute(
            "SELECT name, price, stock FROM products WHERE id=?", (int(product_id),))
        product = cursor.fetchone()

        if product:
            max_stock = product[2]
            cart_items[product_id] = {
                'name': product[0], 'price': product[1], 'quantity': details['quantity'], 'max_stock': max_stock
            }
            total_price += product[1] * cart_items[product_id]['quantity']

    conn.close()
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            first_name = request.form.get('firstname')
            last_name = request.form.get('lastname')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            phone_number = request.form.get('phone_number')
            if password != confirm_password:
                raise ValueError(
                    'رمز عبور و تکرار آن با یکدیگر مطابقت ندارند.')
            conn_users = sqlite3.connect('users.db')
            cursor_users = conn_users.cursor()
            cursor_users.execute(
                "SELECT * FROM users WHERE email = ? OR username = ?", (email, username))
            existing_user = cursor_users.fetchone()

            if existing_user:
                raise ValueError('Username or email already exists.')
            phone_number = phone_number.lstrip('0')
            if len(phone_number) == 10:
                phone_number = '+98' + phone_number

            cursor_users.execute('''
                INSERT INTO users (username, first_name, last_name, email, password_hash, phone_number)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, first_name, last_name, email, password, phone_number))

            conn_users.commit()
            conn_users.close()

            flash('عضویت با موفقیت انجام شد!', 'success')

            return redirect(url_for('register'))

        except Exception as e:
            flash(str(e), 'error')

    return render_template('give_info.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username_or_email = request.form.get('username_or_email')
            password = request.form.get('password')
            conn_users = sqlite3.connect('users.db')
            cursor_users = conn_users.cursor()

            cursor_users.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
            user = cursor_users.fetchone()

            if user and check_password_hash(user[3], password):
                flash('ورود با موفقیت انجام شد!', 'success')
                session['user_id'] = user[0]
                session['username'] = user[1]
                conn_users.close()
                return redirect(url_for('products'))

            else:
                raise ValueError('Invalid username/email or password.')

        except Exception as e:
            flash(str(e), 'error')
    return render_template('login.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    new_quantity = int(request.form.get('quantity'))

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id=?", (product_id,))
    stock = cursor.fetchone()[0]

    if new_quantity <= stock:
        cart_data = request.cookies.get('cart_data', '{}')
        cart_data = json.loads(cart_data)

        if str(product_id) in cart_data:
            cart_data[str(product_id)]['quantity'] = new_quantity

        response = make_response(jsonify({'success': True}))
    else:
        response = make_response(jsonify(
            {'success': False, 'message': 'تعداد وارد شده بیشتر از تعداد موجودی است'}))

    response.set_cookie('cart_data', json.dumps(cart_data))
    conn.close()
    return response


@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    return jsonify(success=True, message='سبد خرید با موفقیت پاک شد.')


@app.route('/order', methods=['POST'])
def place_order():
    cart_data = request.cookies.get('cart_data', '{}')
    cart_data = json.loads(cart_data)

    conn_products = sqlite3.connect('products.db')
    cursor_products = conn_products.cursor()

    try:
        for product_id, details in cart_data.items():
            cursor_products.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?", (details['quantity'], int(product_id)))

        conn_products.commit()

        conn_products.close()

        response = make_response(redirect(url_for('cart')))
        response.set_cookie('cart_data', json.dumps({}))

        return response

    except Exception as e:
        conn_products.rollback()
        conn_products.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/create_initial_products', methods=['GET'])
def create_initial_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE name='محصول 1' OR name='محصول 2'")
    conn.commit()

    cursor.execute(
        "INSERT INTO products (name, price, stock) VALUES ('محصول 1', 100, 50)")
    cursor.execute(
        "INSERT INTO products (name, price, stock) VALUES ('محصول 2', 150, 70)")

    conn.commit()
    conn.close()

    return jsonify(success=True, message='محصولات اولیه با موفقیت ایجاد شدند.')


if __name__ == '__main__':
    app.run(debug=True)
