from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import random
import re
import qrcode
from io import BytesIO
import base64
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = "venomx_secret_key_2024"

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smm_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Google OAuth (Optional - Google Client ID/Secret dena padega)
# Agar nahi hai toh Google login hatane ke liye comment kar dena
# app.config['GOOGLE_OAUTH_CLIENT_ID'] = 'YOUR_GOOGLE_CLIENT_ID'
# app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = 'YOUR_GOOGLE_CLIENT_SECRET'
# google_bp = make_google_blueprint(client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'], client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'], scope=['profile', 'email'])
# app.register_blueprint(google_bp, url_prefix='/login')

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

# ============ HTML TEMPLATES ============
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
        body::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle, rgba(0,255,255,0.1) 0%, transparent 50%); animation: rotate 20s linear infinite; z-index: 0; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .login-card { position: relative; z-index: 1; background: rgba(10, 10, 42, 0.9); backdrop-filter: blur(12px); border-radius: 24px; padding: 40px 35px; width: 100%; max-width: 450px; border: 1px solid rgba(0, 255, 204, 0.3); box-shadow: 0 0 40px rgba(0, 255, 204, 0.1); }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo img { max-width: 220px; }
        h2 { color: #00ffcc; text-align: center; font-size: 28px; letter-spacing: 4px; margin-bottom: 10px; text-shadow: 0 0 10px #00ffcc; }
        .sub { color: rgba(255,255,255,0.6); text-align: center; font-size: 13px; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; }
        .input-group input { width: 100%; padding: 14px 18px; background: rgba(255,255,255,0.05); border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 12px; color: white; font-size: 14px; }
        .input-group input:focus { outline: none; border-color: #00ffcc; box-shadow: 0 0 15px rgba(0, 255, 204, 0.3); }
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #00ffcc, #0099ff); border: none; border-radius: 12px; color: #0a0a2a; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0, 255, 204, 0.4); }
        .error { background: rgba(255,0,0,0.2); border: 1px solid #ff3366; border-radius: 10px; padding: 10px; margin-bottom: 20px; text-align: center; color: #ff6b6b; font-size: 13px; }
        .footer { text-align: center; margin-top: 25px; font-size: 11px; color: rgba(255,255,255,0.3); }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X PANNEL"></div>
        <h2>VENOM X</h2><p class="sub">SMM PANEL</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div>
            <div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div>
            <button type="submit" class="btn">LOGIN</button>
        </form>
        <div class="footer">© 2025 VENOM X SMM PANEL | OWNER: VENOMXSMMPY</div>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENOM X - Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { background: linear-gradient(135deg, #0a0a2a, #0f0f3a, #1a1a4a); min-height: 100vh; }
        .navbar { background: rgba(10, 10, 42, 0.9); backdrop-filter: blur(10px); padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0, 255, 204, 0.3); }
        .logo img { height: 45px; }
        .nav-links a { color: #00ffcc; text-decoration: none; margin-left: 25px; font-size: 13px; }
        .balance { background: linear-gradient(135deg, #00ffcc, #0099ff); padding: 8px 18px; border-radius: 30px; color: #0a0a2a; font-weight: bold; margin-left: 25px; }
        .container { padding: 30px; max-width: 1400px; margin: 0 auto; }
        .welcome { color: #00ffcc; margin-bottom: 30px; font-size: 24px; }
        .welcome span { color: white; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 16px; padding: 20px; text-align: center; }
        .stat-card h3 { color: rgba(255,255,255,0.6); font-size: 12px; }
        .stat-card .value { color: #00ffcc; font-size: 28px; font-weight: bold; }
        .section-title { color: #00ffcc; margin: 30px 0 20px; font-size: 18px; }
        .table-container { background: rgba(255,255,255,0.05); border-radius: 16px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; color: white; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 12px; }
        th { color: #00ffcc; background: rgba(0,0,0,0.3); }
        .btn-service { background: linear-gradient(135deg, #00ffcc, #0099ff); padding: 10px 20px; border: none; border-radius: 8px; color: #0a0a2a; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; margin-right: 10px; }
        .platforms { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 30px; }
        .platform-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 16px; padding: 20px; text-align: center; width: 180px; cursor: pointer; transition: 0.3s; }
        .platform-card:hover { transform: translateY(-3px); box-shadow: 0 5px 20px rgba(0,255,204,0.2); }
        .platform-card img { width: 60px; height: 60px; object-fit: contain; margin-bottom: 10px; }
        .platform-card h3 { color: #00ffcc; font-size: 16px; }
        .service-form { display: none; background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; margin-top: 20px; }
        .service-form input, .service-form select { width: 100%; padding: 12px; margin: 10px 0; background: rgba(255,255,255,0.1); border: 1px solid #00ffcc; border-radius: 8px; color: white; }
        .service-form button { background: linear-gradient(135deg, #00ffcc, #0099ff); padding: 12px; border: none; border-radius: 8px; color: #0a0a2a; font-weight: bold; cursor: pointer; width: 100%; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); justify-content: center; align-items: center; z-index: 300; }
        .modal-content { background: #0a0a2a; padding: 30px; border-radius: 20px; max-width: 400px; width: 90%; border: 1px solid #00ffcc; text-align: center; }
        .modal-content input { width: 100%; padding: 12px; margin: 10px 0; background: rgba(255,255,255,0.1); border: 1px solid #00ffcc; border-radius: 8px; color: white; }
        @media (max-width: 768px) { .nav-links a { display: none; } .container { padding: 20px; } }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X"></div>
        <div class="nav-links">
            <a href="/dashboard">DASHBOARD</a>
            <a href="#" onclick="showServices()">SERVICES</a>
            <a href="#" onclick="openAddCash()">ADD CASH</a>
            <a href="/logout" class="balance">LOGOUT</a>
        </div>
    </div>
    <div class="container">
        <div class="welcome">WELCOME, <span>{{ user.username.upper() }}</span></div>
        <div class="stats">
            <div class="stat-card"><h3>WALLET BALANCE</h3><div class="value">₹{{ "%.2f"|format(user.balance) }}</div></div>
            <div class="stat-card"><h3>TOTAL ORDERS</h3><div class="value">{{ orders|length }}</div></div>
        </div>
        
        <div class="platforms">
            <div class="platform-card" onclick="showPlatform('instagram')"><img src="https://i.ibb.co/SXBKM3cS/file-100.jpg"><h3>INSTAGRAM</h3></div>
            <div class="platform-card" onclick="showPlatform('youtube')"><img src="https://i.ibb.co/6jQK0fK/file-99.jpg"><h3>YOUTUBE</h3></div>
        </div>
        
        <div id="serviceForm" class="service-form">
            <h3 style="color:#00ffcc" id="serviceTitle">Select Service</h3>
            <select id="serviceSelect"></select>
            <input type="text" id="serviceLink" placeholder="Instagram/YouTube Link" required>
            <input type="number" id="serviceQuantity" placeholder="Quantity" required>
            <p id="servicePrice" style="color:#00ffcc; margin:10px 0;"></p>
            <button onclick="placeOrder()">PLACE ORDER</button>
        </div>
        
        <div id="orderResult" style="margin-top:20px; text-align:center; color:#00ffcc;"></div>
        
        <h3 class="section-title">RECENT ORDERS</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>ORDER ID</th><th>SERVICE</th><th>QUANTITY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead>
                <tbody>
                    {% for order in orders %}
                    <tr><td>{{ order.order_id }}</td><td>{{ order.service_name[:25] }}</td><td>{{ order.quantity }}</td><td>₹{{ order.total_amount }}</td><td>{{ order.status }}</td><td>{{ order.created_at.strftime('%Y-%m-%d') }}</td></tr>
                    {% else %}
                    <tr><td colspan="6" style="text-align:center;">No orders yet</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="addCashModal" class="modal">
        <div class="modal-content">
            <h2 style="color:#00ffcc">ADD CASH</h2>
            <input type="number" id="cashAmount" placeholder="Amount (₹10-500)" min="10" max="500">
            <button onclick="generateQR()" style="background:#00ffcc; color:#0a0a2a; padding:12px; border:none; border-radius:8px; font-weight:bold;">GENERATE QR</button>
            <button onclick="closeAddCash()" style="margin-top:10px; background:rgba(255,255,255,0.1); color:white; padding:12px; border:none; border-radius:8px;">CANCEL</button>
            <div id="qrResult" style="margin-top:20px;"></div>
        </div>
    </div>
    
    <script>
        let services = {{ services|tojson }};
        let currentPlatform = null;
        
        function showServices() { document.getElementById('serviceForm').style.display = 'block'; }
        function showPlatform(platform) {
            currentPlatform = platform;
            let serviceSelect = document.getElementById('serviceSelect');
            serviceSelect.innerHTML = '';
            services[platform].services.forEach(s => {
                let option = document.createElement('option');
                option.value = s.id;
                option.text = `${s.name} - ₹${s.price}/1K (Min:${s.min} Max:${s.max})`;
                serviceSelect.appendChild(option);
            });
            document.getElementById('serviceTitle').innerHTML = `${services[platform].name} SERVICES`;
            document.getElementById('serviceForm').style.display = 'block';
            updatePrice();
            serviceSelect.onchange = updatePrice;
        }
        function updatePrice() {
            let select = document.getElementById('serviceSelect');
            let selectedId = parseInt(select.value);
            let service = null;
            for(let s of services[currentPlatform].services) { if(s.id === selectedId) { service = s; break; } }
            if(service) { document.getElementById('servicePrice').innerHTML = `Price: ₹${service.price}/1000 | Min:${service.min} Max:${service.max}`; }
        }
        function placeOrder() {
            let serviceId = document.getElementById('serviceSelect').value;
            let link = document.getElementById('serviceLink').value;
            let quantity = document.getElementById('serviceQuantity').value;
            if(!link || !quantity) { alert('Fill all fields'); return; }
            fetch('/place-order', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `service_type=${currentPlatform}&service_id=${serviceId}&link=${link}&quantity=${quantity}`
            }).then(res => res.json()).then(data => {
                if(data.success) { document.getElementById('orderResult').innerHTML = `<span style="color:#00ff00;">✅ Order Placed! ID: ${data.order_id} | New Balance: ₹${data.balance}</span>`; setTimeout(() => location.reload(), 2000); }
                else { document.getElementById('orderResult').innerHTML = `<span style="color:#ff3366;">❌ ${data.error}</span>`; }
            });
        }
        function openAddCash() { document.getElementById('addCashModal').style.display = 'flex'; }
        function closeAddCash() { document.getElementById('addCashModal').style.display = 'none'; document.getElementById('qrResult').innerHTML = ''; document.getElementById('cashAmount').value = ''; }
        function generateQR() {
            let amount = document.getElementById('cashAmount').value;
            if(amount < 10 || amount > 500) { alert('Amount must be between ₹10 and ₹500'); return; }
            fetch('/add-cash', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'amount=' + amount })
            .then(res => res.json()).then(data => {
                if(data.success) { document.getElementById('qrResult').innerHTML = `<p style="color:#00ffcc;">Pay: ₹${data.qr_amount}</p><img src="data:image/png;base64,${data.qr_code}" style="width:180px;"><p style="color:#ffaa00;">Txn ID: ${data.transaction_id}</p><p style="color:#aaa;">Send screenshot to bot for verification</p>`; }
                else { alert('Error: ' + data.error); }
            });
        }
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENOM X - Admin Panel</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { background: linear-gradient(135deg, #0a0a2a, #0f0f3a, #1a1a4a); min-height: 100vh; }
        .navbar { background: rgba(10, 10, 42, 0.9); padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ffcc; }
        .logo img { height: 45px; }
        .container { padding: 30px; max-width: 1400px; margin: 0 auto; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: rgba(255,255,255,0.05); border: 1px solid #00ffcc; border-radius: 16px; padding: 20px; text-align: center; }
        .stat-card h3 { color: rgba(255,255,255,0.6); font-size: 12px; }
        .stat-card .value { color: #00ffcc; font-size: 28px; font-weight: bold; }
        h3 { color: #00ffcc; margin: 20px 0; }
        .table-container { background: rgba(255,255,255,0.05); border-radius: 16px; overflow-x: auto; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; color: white; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 12px; }
        th { color: #00ffcc; }
        .btn-ban { background: #ff3366; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
        .btn-unban { background: #00ffcc; color: #0a0a2a; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
        .btn-add { background: #0099ff; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
        .logout { color: #00ffcc; text-decoration: none; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X"></div>
        <a href="/logout" class="logout">LOGOUT</a>
    </div>
    <div class="container">
        <h2 style="color:#00ffcc; margin-bottom:20px;">👑 ADMIN PANEL</h2>
        <div class="stats">
            <div class="stat-card"><h3>TOTAL USERS</h3><div class="value">{{ total_users }}</div></div>
            <div class="stat-card"><h3>TOTAL ORDERS</h3><div class="value">{{ total_orders }}</div></div>
            <div class="stat-card"><h3>TOTAL VOLUME</h3><div class="value">₹{{ total_volume }}</div></div>
        </div>
        
        <h3>📋 USERS</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>ID</th><th>USERNAME</th><th>BALANCE</th><th>STATUS</th><th>ACTION</th></tr></thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td>{{ u.id }}</td><td>{{ u.username }}</td><td>₹{{ u.balance }}</td>
                        <td>{% if u.is_banned %}❌ Banned{% else %}✅ Active{% endif %}</td>
                        <td>
                            {% if not u.is_admin %}
                                {% if u.is_banned %}
                                <button class="btn-unban" onclick="unbanUser({{ u.id }})">UNBAN</button>
                                {% else %}
                                <button class="btn-ban" onclick="banUser({{ u.id }})">BAN</button>
                                {% endif %}
                                <input type="number" id="amount_{{ u.id }}" placeholder="Amount" style="width:80px; margin-left:5px;">
                                <button class="btn-add" onclick="addBalance({{ u.id }})">+ ADD</button>
                            {% else %}
                                <span style="color:#00ffcc;">👑 OWNER</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <h3>📦 ORDERS</h3>
        <div class="table-container">
            <table><thead><tr><th>ORDER ID</th><th>USER</th><th>SERVICE</th><th>QUANTITY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead>
            <tbody>
                {% for o in orders %}
                <tr><td>{{ o.order_id }}</td><td>{{ o.user_id }}</td><td>{{ o.service_name[:20] }}</td><td>{{ o.quantity }}</td><td>₹{{ o.total_amount }}</td><td>{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d') }}</td></tr>
                {% endfor %}
            </tbody>
            </table>
        </div>
    </div>
    <script>
        function banUser(id) { fetch('/admin/ban-user', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'user_id='+id }).then(() => location.reload()); }
        function unbanUser(id) { fetch('/admin/unban-user', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'user_id='+id }).then(() => location.reload()); }
        function addBalance(id) { let amount = document.getElementById('amount_'+id).value; fetch('/admin/add-balance', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'user_id='+id+'&amount='+amount }).then(() => location.reload()); }
    </script>
</body>
</html>
"""

ORDER_HISTORY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENOM X - Order History</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { background: linear-gradient(135deg, #0a0a2a, #0f0f3a, #1a1a4a); min-height: 100vh; }
        .navbar { background: rgba(10, 10, 42, 0.9); padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ffcc; }
        .logo img { height: 45px; }
        .container { padding: 30px; max-width: 1200px; margin: 0 auto; }
        .back { color: #00ffcc; text-decoration: none; display: inline-block; margin-bottom: 20px; }
        h2 { color: #00ffcc; margin-bottom: 20px; }
        .table-container { background: rgba(255,255,255,0.05); border-radius: 16px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; color: white; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 12px; }
        th { color: #00ffcc; }
    </style>
</head>
<body>
    <div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X"></div><a href="/dashboard" class="back">← BACK</a></div>
    <div class="container">
        <h2>📜 ORDER HISTORY</h2>
        <div class="table-container">
            <table>
                <thead><tr><th>ORDER ID</th><th>SERVICE</th><th>LINK</th><th>QUANTITY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead>
                <tbody>
                    {% for o in orders %}
                    <tr><td>{{ o.order_id }}</td><td>{{ o.service_name }}</td><td><small>{{ o.link[:40] }}</small></td><td>{{ o.quantity }}</td><td>₹{{ o.total_amount }}</td><td>{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d %H:%M') }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

TRANSACTION_HISTORY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENOM X - Transaction History</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { background: linear-gradient(135deg, #0a0a2a, #0f0f3a, #1a1a4a); min-height: 100vh; }
        .navbar { background: rgba(10, 10, 42, 0.9); padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ffcc; }
        .logo img { height: 45px; }
        .container { padding: 30px; max-width: 1200px; margin: 0 auto; }
        .back { color: #00ffcc; text-decoration: none; display: inline-block; margin-bottom: 20px; }
        h2 { color: #00ffcc; margin-bottom: 20px; }
        .table-container { background: rgba(255,255,255,0.05); border-radius: 16px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; color: white; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 12px; }
        th { color: #00ffcc; }
    </style>
</head>
<body>
    <div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg" alt="VENOM X"></div><a href="/dashboard" class="back">← BACK</a></div>
    <div class="container">
        <h2>💰 TRANSACTION HISTORY</h2>
        <div class="table-container">
            <table>
                <thead><tr><th>TRANSACTION ID</th><th>AMOUNT</th><th>QR AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead>
                <tbody>
                    {% for t in transactions %}
                    <tr><td>{{ t.transaction_id }}</td><td>₹{{ t.amount }}</td><td>₹{{ t.qr_amount }}</td><td>{{ t.status }}</td><td>{{ t.created_at.strftime('%Y-%m-%d %H:%M') }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
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
        # Save IP
        user.ip_address = request.remote_addr
        db.session.commit()
        return redirect('/admin' if user.is_admin else '/dashboard')
    return LOGIN_HTML.replace('{% if error %}', f'<div class="error">Invalid credentials!</div>')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    if not user or user.is_banned:
        session.clear()
        return redirect('/')
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(10).all()
    return DASHBOARD_HTML.replace('{{ user.username }}', user.username).replace('{{ user.balance }}', str(user.balance)).replace('{{ orders|length }}', str(len(orders))) + ''.join([f'<tr><td>{o.order_id}</td><td>{o.service_name[:25]}</td><td>{o.quantity}</td><td>₹{o.total_amount}</td><td>{o.status}</td><td>{o.created_at.strftime("%Y-%m-%d")}</td></tr>' for o in orders]) if orders else '<tr><td colspan="6">No orders yet</td></tr>'

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/')
    users = User.query.all()
    orders = Order.query.all()
    total_orders = len(orders)
    total_users = len(users)
    total_volume = sum([o.total_amount for o in orders])
    return ADMIN_HTML

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
    return ORDER_HISTORY_HTML

@app.route('/transaction-history')
def transaction_history():
    if 'user_id' not in session:
        return redirect('/')
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).all()
    return TRANSACTION_HISTORY_HTML

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
