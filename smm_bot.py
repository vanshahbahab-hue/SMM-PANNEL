from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import random
import re
import qrcode
from io import BytesIO
import base64
import hashlib

app = Flask(__name__)
app.secret_key = "venomx_secret_key_2024"

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smm_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Owner credentials
OWNER_USERNAME = "VENOMXSMMPY"
OWNER_PASSWORD = "VENOMXSMMPY"

# ============ DATABASE MODELS ============
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(200), nullable=True)
    google_id = db.Column(db.String(100), nullable=True)
    balance = db.Column(db.Float, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(200), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    qr_amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username=OWNER_USERNAME).first()
    if not admin:
        admin = User(username=OWNER_USERNAME, password=OWNER_PASSWORD, email="admin@venomx.com", is_admin=True, balance=0)
        db.session.add(admin)
        db.session.commit()

# ============ SERVICES DATA ============
SERVICES = {
    "instagram": {
        "name": "Instagram", "emoji": "📸",
        "photo": "https://i.ibb.co/SXBKM3cS/file-100.jpg",
        "services": [
            {"id": 11, "name": "Instagram Followers", "price": 14, "min": 50, "max": 50000},
            {"id": 12, "name": "Instagram Likes", "price": 14, "min": 20, "max": 20000},
            {"id": 13, "name": "Instagram Views", "price": 14, "min": 100, "max": 100000},
        ]
    },
    "youtube": {
        "name": "YouTube", "emoji": "📺",
        "photo": "https://i.ibb.co/6jQK0fK/file-99.jpg",
        "services": [
            {"id": 1, "name": "YouTube Views", "price": 14, "min": 100, "max": 100000},
            {"id": 2, "name": "YouTube Likes", "price": 14, "min": 10, "max": 10000},
            {"id": 3, "name": "YouTube Subscribers", "price": 14, "min": 10, "max": 10000},
        ]
    }
}

def generate_order_id():
    return f"ORD{random.randint(100000, 999999)}"

def generate_transaction_id():
    return f"TXN{random.randint(100000, 999999)}"

def generate_random_paise():
    return random.randint(1, 99)

# ============ COMPLETE LOGIN PAGE HTML ============
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENOM X SMM Panel - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { min-height: 100vh; background: linear-gradient(135deg, #0a0a2a, #0f0f3a, #1a1a4a); display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
        
        /* Animated Background Particles */
        .particle { position: absolute; width: 3px; height: 3px; background: #00ffcc; border-radius: 50%; animation: float 10s infinite; z-index: 0; }
        @keyframes float { 0% { transform: translateY(100vh) scale(0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(-20vh) scale(1); opacity: 0; } }
        
        /* Rotating Glow */
        .glow { position: absolute; width: 300px; height: 300px; background: radial-gradient(circle, rgba(0,255,204,0.2) 0%, transparent 70%); border-radius: 50%; animation: rotate 20s linear infinite; z-index: 0; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        .login-card { position: relative; z-index: 1; background: rgba(10, 10, 42, 0.95); backdrop-filter: blur(12px); border-radius: 24px; padding: 40px 35px; width: 100%; max-width: 480px; border: 1px solid rgba(0, 255, 204, 0.3); box-shadow: 0 0 40px rgba(0, 255, 204, 0.1); animation: fadeIn 0.6s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { max-width: 200px; }
        h2 { color: #00ffcc; text-align: center; font-size: 28px; letter-spacing: 4px; text-shadow: 0 0 10px #00ffcc; }
        .sub { color: rgba(255,255,255,0.6); text-align: center; font-size: 12px; margin-bottom: 25px; letter-spacing: 2px; }
        
        .tab { display: flex; margin-bottom: 25px; border-bottom: 1px solid rgba(0,255,204,0.3); }
        .tab-btn { flex: 1; background: none; border: none; padding: 12px; color: rgba(255,255,255,0.6); font-size: 16px; cursor: pointer; transition: 0.3s; }
        .tab-btn.active { color: #00ffcc; border-bottom: 2px solid #00ffcc; }
        
        .form-container { display: none; }
        .form-container.active { display: block; animation: fadeIn 0.4s ease; }
        
        .input-group { margin-bottom: 20px; }
        .input-group input { width: 100%; padding: 14px 18px; background: rgba(255,255,255,0.05); border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 12px; color: white; font-size: 14px; transition: 0.3s; }
        .input-group input:focus { outline: none; border-color: #00ffcc; box-shadow: 0 0 15px rgba(0, 255, 204, 0.3); }
        
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #00ffcc, #0099ff); border: none; border-radius: 12px; color: #0a0a2a; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; transition: 0.3s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0, 255, 204, 0.4); }
        
        .google-btn { background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); margin-top: 15px; }
        .divider { text-align: center; margin: 20px 0; color: rgba(255,255,255,0.4); font-size: 12px; position: relative; }
        .divider::before, .divider::after { content: ''; position: absolute; top: 50%; width: 40%; height: 1px; background: rgba(255,255,255,0.2); }
        .divider::before { left: 0; } .divider::after { right: 0; }
        
        .error { background: rgba(255,51,102,0.2); border: 1px solid #ff3366; border-radius: 10px; padding: 12px; margin-bottom: 20px; text-align: center; color: #ff6b6b; font-size: 13px; }
        .success { background: rgba(0,255,204,0.2); border: 1px solid #00ffcc; border-radius: 10px; padding: 12px; margin-bottom: 20px; text-align: center; color: #00ffcc; font-size: 13px; }
        
        .footer { text-align: center; margin-top: 25px; font-size: 10px; color: rgba(255,255,255,0.3); }
        a { color: #00ffcc; text-decoration: none; }
    </style>
</head>
<body>
    <div id="particles"></div>
    <div class="glow" style="top: -150px; right: -150px;"></div>
    <div class="glow" style="bottom: -150px; left: -150px; animation-direction: reverse;"></div>
    
    <div class="login-card">
        <div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X PANNEL"></div>
        <h2>VENOM X</h2><p class="sub">SMM PANEL</p>
        
        <div class="tab">
            <button class="tab-btn active" onclick="switchTab('login')">LOGIN</button>
            <button class="tab-btn" onclick="switchTab('register')">REGISTER</button>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        <!-- Login Form -->
        <div id="loginForm" class="form-container active">
            <form method="POST" action="/login">
                <div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div>
                <div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div>
                <button type="submit" class="btn">LOGIN</button>
            </form>
        </div>
        
        <!-- Register Form -->
        <div id="registerForm" class="form-container">
            <form method="POST" action="/register">
                <div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div>
                <div class="input-group"><input type="email" name="email" placeholder="EMAIL" required></div>
                <div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div>
                <div class="input-group"><input type="password" name="confirm_password" placeholder="CONFIRM PASSWORD" required></div>
                <button type="submit" class="btn">REGISTER</button>
            </form>
        </div>
        
        <div class="divider">OR</div>
        <a href="/google-login" style="text-decoration: none;"><button class="btn google-btn">🔐 SIGN IN WITH GOOGLE</button></a>
        
        <div class="footer">© 2025 VENOM X SMM PANEL | OWNER: VENOMXSMMPY</div>
    </div>
    
    <script>
        function switchTab(tab) {
            document.getElementById('loginForm').classList.remove('active');
            document.getElementById('registerForm').classList.remove('active');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            if(tab === 'login') {
                document.getElementById('loginForm').classList.add('active');
                document.querySelector('.tab-btn:first-child').classList.add('active');
            } else {
                document.getElementById('registerForm').classList.add('active');
                document.querySelector('.tab-btn:last-child').classList.add('active');
            }
        }
        
        // Create particles
        for(let i = 0; i < 60; i++) {
            let particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDuration = (Math.random() * 10 + 5) + 's';
            particle.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(particle);
        }
    </script>
</body>
</html>
"""

# ============ FLASK ROUTES ============
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not user.is_banned:
            return redirect('/dashboard' if not user.is_admin else '/admin')
    return LOGIN_HTML

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user and not user.is_banned:
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        user.ip_address = request.remote_addr
        db.session.commit()
        return redirect('/admin' if user.is_admin else '/dashboard')
    return LOGIN_HTML.replace('{% if error %}', '<div class="error">Invalid credentials!</div>')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirm_password')
    
    if password != confirm:
        return LOGIN_HTML.replace('{% if error %}', '<div class="error">Passwords do not match!</div>')
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return LOGIN_HTML.replace('{% if error %}', '<div class="error">Username already exists!</div>')
    
    new_user = User(username=username, email=email, password=password, balance=0)
    db.session.add(new_user)
    db.session.commit()
    
    return LOGIN_HTML.replace('{% if success %}', '<div class="success">Account created! Please login.</div>')

@app.route('/google-login')
def google_login():
    # Simple mock Google login - in production, use proper OAuth
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    if not user or user.is_banned:
        session.clear()
        return redirect('/')
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(10).all()
    return render_template_string(DASHBOARD_HTML, user=user, orders=orders, services=SERVICES)

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/')
    users = User.query.all()
    orders = Order.query.all()
    total_orders = len(orders)
    total_users = len(users)
    total_volume = sum([o.total_amount for o in orders])
    return render_template_string(ADMIN_HTML, users=users, orders=orders, total_orders=total_orders, total_users=total_users, total_volume=total_volume)

@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    if user.is_banned:
        return jsonify({'error': 'Account banned'}), 403
    
    service_type = request.form.get('service_type')
    service_id = int(request.form.get('service_id'))
    link = request.form.get('link')
    quantity = int(request.form.get('quantity'))
    
    service_info = None
    for st, data in SERVICES.items():
        for s in data['services']:
            if s['id'] == service_id:
                service_info = s
                break
        if service_info:
            break
    
    if not service_info:
        return jsonify({'error': 'Service not found'}), 400
    
    total_price = (quantity / 1000) * service_info['price']
    if user.balance < total_price:
        return jsonify({'error': f'Insufficient balance! Need ₹{total_price}'}), 400
    
    user.balance -= total_price
    order_id = generate_order_id()
    order = Order(order_id=order_id, user_id=user.id, service_name=service_info['name'], service_type=service_type, link=link, quantity=quantity, price=service_info['price'], total_amount=total_price)
    db.session.add(order)
    db.session.commit()
    return jsonify({'success': True, 'order_id': order_id, 'balance': user.balance})

@app.route('/add-cash', methods=['POST'])
def add_cash():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    amount = int(request.form.get('amount'))
    if amount < 10 or amount > 500:
        return jsonify({'error': 'Amount must be between ₹10 and ₹500'}), 400
    
    random_paise = generate_random_paise()
    qr_amount = amount + (random_paise / 100)
    upi_link = f"upi://pay?pa=venomxpay@naviaxis&pn=SMM&am={qr_amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    transaction_id = generate_transaction_id()
    transaction = Transaction(transaction_id=transaction_id, user_id=session['user_id'], amount=amount, qr_amount=qr_amount)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'success': True, 'qr_code': qr_base64, 'qr_amount': qr_amount, 'transaction_id': transaction_id})

@app.route('/order-history')
def order_history():
    if 'user_id' not in session:
        return redirect('/')
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template_string(ORDER_HISTORY_HTML, orders=orders)

@app.route('/transaction-history')
def transaction_history():
    if 'user_id' not in session:
        return redirect('/')
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).all()
    return render_template_string(TRANSACTION_HISTORY_HTML, transactions=transactions)

@app.route('/admin/ban-user', methods=['POST'])
def ban_user():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(request.form.get('user_id'))
    if user:
        user.is_banned = True
        db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/unban-user', methods=['POST'])
def unban_user():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(request.form.get('user_id'))
    if user:
        user.is_banned = False
        db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/add-balance', methods=['POST'])
def admin_add_balance():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(request.form.get('user_id'))
    amount = float(request.form.get('amount'))
    if user:
        user.balance += amount
        db.session.commit()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# SMS Webhook for auto payment verification
@app.route('/sms-webhook', methods=['POST'])
def sms_webhook():
    data = request.json
    sms_text = data.get('message', '')
    amount_match = re.search(r'Rs\.?\s*(\d+\.?\d*)', sms_text, re.IGNORECASE)
    if amount_match:
        amount = float(amount_match.group(1))
        transaction = Transaction.query.filter_by(qr_amount=amount, status='Pending').first()
        if transaction:
            transaction.status = 'Completed'
            user = User.query.get(transaction.user_id)
            user.balance += transaction.amount
            db.session.commit()
            return jsonify({'status': 'success'})
    return jsonify({'status': 'pending'})

# ============ SIMPLE DASHBOARD HTML ============
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>VENOM X - Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);min-height:100vh;}
.navbar{background:rgba(10,10,42,0.9);padding:15px 30px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #00ffcc;}
.logo img{height:45px;}
.nav-links a{color:#00ffcc;text-decoration:none;margin-left:25px;}
.balance{background:linear-gradient(135deg,#00ffcc,#0099ff);padding:8px 18px;border-radius:30px;color:#0a0a2a;font-weight:bold;}
.container{padding:30px;max-width:1400px;margin:0 auto;}
.welcome{color:#00ffcc;margin-bottom:30px;font-size:24px;}
.welcome span{color:white;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px;}
.stat-card{background:rgba(255,255,255,0.05);border:1px solid rgba(0,255,204,0.3);border-radius:16px;padding:20px;text-align:center;}
.stat-card h3{color:rgba(255,255,255,0.6);font-size:12px;}
.stat-card .value{color:#00ffcc;font-size:28px;font-weight:bold;}
.platforms{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px;}
.platform-card{background:rgba(255,255,255,0.05);border:1px solid #00ffcc;border-radius:16px;padding:20px;text-align:center;width:180px;cursor:pointer;}
.platform-card img{width:60px;height:60px;}
.platform-card h3{color:#00ffcc;}
.service-form{display:none;background:rgba(255,255,255,0.05);border-radius:16px;padding:20px;margin-top:20px;}
.service-form input,.service-form select{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.1);border:1px solid #00ffcc;border-radius:8px;color:white;}
.service-form button{background:linear-gradient(135deg,#00ffcc,#0099ff);padding:12px;border:none;border-radius:8px;color:#0a0a2a;font-weight:bold;cursor:pointer;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px;text-align:left;color:white;border-bottom:1px solid rgba(255,255,255,0.1);}
th{color:#00ffcc;}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);justify-content:center;align-items:center;z-index:300;}
.modal-content{background:#0a0a2a;padding:30px;border-radius:20px;max-width:400px;width:90%;border:1px solid #00ffcc;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><div class="nav-links"><a href="/dashboard">HOME</a><a href="#" onclick="openAddCash()">ADD CASH</a><a href="/order-history">ORDERS</a><a href="/transaction-history">HISTORY</a><a href="/logout" class="balance">LOGOUT</a></div></div>
<div class="container">
<div class="welcome">WELCOME, <span>{{ user.username }}</span></div>
<div class="stats"><div class="stat-card"><h3>BALANCE</h3><div class="value">₹{{ "%.2f"|format(user.balance) }}</div></div><div class="stat-card"><h3>ORDERS</h3><div class="value">{{ orders|length }}</div></div></div>
<div class="platforms"><div class="platform-card" onclick="showPlatform('instagram')"><img src="https://i.ibb.co/SXBKM3cS/file-100.jpg"><h3>INSTAGRAM</h3></div><div class="platform-card" onclick="showPlatform('youtube')"><img src="https://i.ibb.co/6jQK0fK/file-99.jpg"><h3>YOUTUBE</h3></div></div>
<div id="serviceForm" class="service-form"><h3 style="color:#00ffcc" id="serviceTitle">Select Service</h3><select id="serviceSelect"></select><input type="text" id="serviceLink" placeholder="Link"><input type="number" id="serviceQuantity" placeholder="Quantity"><p id="servicePrice" style="color:#00ffcc"></p><button onclick="placeOrder()">PLACE ORDER</button></div>
<div id="orderResult"></div>
<h3 style="color:#00ffcc;margin:20px 0 10px">RECENT ORDERS</h3>
<div class="table-container"><table><thead><tr><th>ID</th><th>SERVICE</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td>{{ o.order_id }}</td><td>{{ o.service_name[:20] }}</td><td>{{ o.quantity }}</td><td>₹{{ o.total_amount }}</td><td>{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d') }}</td></tr>{% endfor %}</tbody></table></div></div>
<div id="addCashModal" class="modal"><div class="modal-content"><h2 style="color:#00ffcc">ADD CASH</h2><input type="number" id="cashAmount" placeholder="Amount (10-500)"><button onclick="generateQR()" style="background:#00ffcc;color:#0a0a2a;padding:12px;width:100%;margin:10px 0;border:none;border-radius:8px;">GENERATE QR</button><button onclick="closeAddCash()" style="background:#333;color:white;padding:12px;width:100%;border:none;border-radius:8px;">CANCEL</button><div id="qrResult" style="margin-top:15px"></div></div></div>
<script>
let services = {{ services|tojson }};
let currentPlatform = null;
function showPlatform(p){currentPlatform=p;let s=document.getElementById('serviceSelect');s.innerHTML='';services[p].services.forEach(svc=>{let opt=document.createElement('option');opt.value=svc.id;opt.text=`${svc.name} - ₹${svc.price}/1K (Min:${svc.min} Max:${svc.max})`;s.appendChild(opt);});document.getElementById('serviceTitle').innerHTML=`${services[p].name} SERVICES`;document.getElementById('serviceForm').style.display='block';updatePrice();s.onchange=updatePrice;}
function updatePrice(){let sel=document.getElementById('serviceSelect');let id=parseInt(sel.value);let svc=null;for(let s of services[currentPlatform].services){if(s.id===id){svc=s;break;}}if(svc){document.getElementById('servicePrice').innerHTML=`Price: ₹${svc.price}/1000 | Min:${svc.min} Max:${svc.max}`;}}
function placeOrder(){let sid=document.getElementById('serviceSelect').value;let link=document.getElementById('serviceLink').value;let qty=document.getElementById('serviceQuantity').value;if(!link||!qty){alert('Fill all fields');return;}fetch('/place-order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`service_type=${currentPlatform}&service_id=${sid}&link=${link}&quantity=${qty}`}).then(res=>res.json()).then(data=>{if(data.success){document.getElementById('orderResult').innerHTML=`<span style="color:#0f0;">✅ Order Placed! ID: ${data.order_id}</span>`;setTimeout(()=>location.reload(),2000);}else{document.getElementById('orderResult').innerHTML=`<span style="color:#f33;">❌ ${data.error}</span>`;}});}
function openAddCash(){document.getElementById('addCashModal').style.display='flex';}
function closeAddCash(){document.getElementById('addCashModal').style.display='none';document.getElementById('qrResult').innerHTML='';document.getElementById('cashAmount').value='';}
function generateQR(){let amt=document.getElementById('cashAmount').value;if(amt<10||amt>500){alert('Amount must be 10-500');return;}fetch('/add-cash',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'amount='+amt}).then(res=>res.json()).then(data=>{if(data.success){document.getElementById('qrResult').innerHTML=`<p style="color:#0ff;">Pay: ₹${data.qr_amount}</p><img src="data:image/png;base64,${data.qr_code}" style="width:160px;"><p style="color:#fa0;">Txn ID: ${data.transaction_id}</p><p>Send screenshot to bot</p>`;}else{alert('Error');}});}
</script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>VENOM X - Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);}
.navbar{background:rgba(10,10,42,0.9);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ffcc;}
.logo img{height:45px;}
.container{padding:30px;max-width:1400px;margin:0 auto;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px;}
.stat-card{background:rgba(255,255,255,0.05);border:1px solid #00ffcc;border-radius:16px;padding:20px;text-align:center;}
.stat-card h3{color:rgba(255,255,255,0.6);}
.stat-card .value{color:#00ffcc;font-size:28px;font-weight:bold;}
h3{color:#00ffcc;margin:20px 0;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th,td{padding:10px;text-align:left;color:white;border-bottom:1px solid rgba(255,255,255,0.1);}
th{color:#00ffcc;}
.btn-ban{background:#ff3366;color:white;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;}
.btn-unban{background:#00ffcc;color:#0a0a2a;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;}
.btn-add{background:#0099ff;color:white;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><a href="/logout" style="color:#00ffcc;text-decoration:none;">LOGOUT</a></div>
<div class="container">
<h2 style="color:#00ffcc;margin-bottom:20px;">👑 ADMIN PANEL</h2>
<div class="stats"><div class="stat-card"><h3>TOTAL USERS</h3><div class="value">{{ total_users }}</div></div><div class="stat-card"><h3>TOTAL ORDERS</h3><div class="value">{{ total_orders }}</div></div><div class="stat-card"><h3>TOTAL VOLUME</h3><div class="value">₹{{ total_volume }}</div></div></div>
<h3>USERS</h3>
<div class="table-container"><table><thead><tr><th>ID</th><th>USERNAME</th><th>BALANCE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{% for u in users %}<tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>₹{{ u.balance }}</td><td>{% if u.is_banned %}BANNED{% else %}ACTIVE{% endif %}</td><td>{% if not u.is_admin %}{% if u.is_banned %}<button class="btn-unban" onclick="unbanUser({{ u.id }})">UNBAN</button>{% else %}<button class="btn-ban" onclick="banUser({{ u.id }})">BAN</button>{% endif %}<input type="number" id="amt_{{ u.id }}" placeholder="Amt" style="width:70px;"><button class="btn-add" onclick="addBalance({{ u.id }})">+</button>{% else %}OWNER{% endif %}</td></tr>{% endfor %}</tbody></table></div>
<h3>ORDERS</h3>
<div class="table-container"><table><thead><tr><th>ORDER ID</th><th>USER</th><th>SERVICE</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td>{{ o.order_id }}</td><td>{{ o.user_id }}</td><td>{{ o.service_name[:15] }}</td><td>{{ o.quantity }}</td><td>₹{{ o.total_amount }}</td><td>{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d') }}</td></tr>{% endfor %}</tbody></table></div></div>
<script>
function banUser(id){fetch('/admin/ban-user',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user_id='+id}).then(()=>location.reload());}
function unbanUser(id){fetch('/admin/unban-user',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user_id='+id}).then(()=>location.reload());}
function addBalance(id){let amt=document.getElementById('amt_'+id).value;fetch('/admin/add-balance',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user_id='+id+'&amount='+amt}).then(()=>location.reload());}
</script>
</body>
</html>
"""

ORDER_HISTORY_HTML = """
<!DOCTYPE html>
<html>
<head><title>Order History</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}body{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);}.navbar{background:rgba(10,10,42,0.9);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ffcc;}.logo img{height:45px;}.container{padding:30px;}.back{color:#00ffcc;text-decoration:none;}.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;margin-top:20px;}table{width:100%;border-collapse:collapse;}th,td{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.1);}th{color:#00ffcc;}</style>
</head>
<body><div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><a href="/dashboard" class="back">← BACK</a></div>
<div class="container"><h2 style="color:#00ffcc">ORDER HISTORY</h2>
<div class="table-container"><table><thead><tr><th>ORDER ID</th><th>SERVICE</th><th>LINK</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td>{{ o.order_id }}</td><td>{{ o.service_name }}</td><td><small>{{ o.link[:30] }}</small></td><td>{{ o.quantity }}</td><td>₹{{ o.total_amount }}</td><td>{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d') }}</td></tr>{% endfor %}</tbody></table></div></div></body>
</html>
"""

TRANSACTION_HISTORY_HTML = """
<!DOCTYPE html>
<html>
<head><title>Transaction History</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}body{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);}.navbar{background:rgba(10,10,42,0.9);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ffcc;}.logo img{height:45px;}.container{padding:30px;}.back{color:#00ffcc;text-decoration:none;}.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;margin-top:20px;}table{width:100%;border-collapse:collapse;}th,td{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.1);}th{color:#00ffcc;}</style>
</head>
<body><div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><a href="/dashboard" class="back">← BACK</a></div>
<div class="container"><h2 style="color:#00ffcc">TRANSACTION HISTORY</h2>
<div class="table-container"><table><thead><td><th>TXN ID</th><th>AMOUNT</th><th>QR AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for t in transactions %}<tr><td>{{ t.transaction_id }}</td><td>₹{{ t.amount }}</td><td>₹{{ t.qr_amount }}</td><td>{{ t.status }}</td><td>{{ t.created_at.strftime('%Y-%m-%d') }}</td></tr>{% endfor %}</tbody></table></div></div></body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
