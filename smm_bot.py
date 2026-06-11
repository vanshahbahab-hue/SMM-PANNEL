from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random
import re
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "venomx_secret_key_2024"

# Database - FIXED PATH for Render
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "smm_panel.db")}'
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

# Create tables - FIXED
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username=OWNER_USERNAME).first()
    if not admin:
        admin = User(username=OWNER_USERNAME, password=OWNER_PASSWORD, email="admin@venomx.com", is_admin=True, balance=99999)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

# ============ SERVICES DATA ============
SERVICES = {
    "instagram": {
        "name": "INSTAGRAM",
        "photo": "https://i.ibb.co/SXBKM3cS/file-100.jpg",
        "services": [
            {"id": 11, "name": "INSTAGRAM FOLLOWERS", "price": 14, "min": 50, "max": 50000},
            {"id": 12, "name": "INSTAGRAM LIKES", "price": 14, "min": 20, "max": 20000},
            {"id": 13, "name": "INSTAGRAM VIEWS", "price": 14, "min": 100, "max": 100000},
        ]
    },
    "youtube": {
        "name": "YOUTUBE",
        "photo": "https://i.ibb.co/6jQK0fK/file-99.jpg",
        "services": [
            {"id": 1, "name": "YOUTUBE VIEWS", "price": 14, "min": 100, "max": 100000},
            {"id": 2, "name": "YOUTUBE LIKES", "price": 14, "min": 10, "max": 10000},
            {"id": 3, "name": "YOUTUBE SUBSCRIBERS", "price": 14, "min": 10, "max": 10000},
        ]
    }
}

def generate_order_id():
    return f"ORD{random.randint(100000, 999999)}"

def generate_transaction_id():
    return f"TXN{random.randint(100000, 999999)}"

def generate_random_paise():
    return random.randint(1, 99)

# ============ SIMPLE ROUTE TO TEST ============
@app.route('/test')
def test():
    return "Server is working! Database is connected."

# ============ FLASK ROUTES ============
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not user.is_banned:
            return redirect('/dashboard' if not user.is_admin else '/admin')
    return '''
<!DOCTYPE html>
<html>
<head><title>VENOM X LOGIN</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);min-height:100vh;display:flex;justify-content:center;align-items:center;}
.login-card{background:rgba(10,10,42,0.95);backdrop-filter:blur(15px);border-radius:30px;padding:45px 40px;width:100%;max-width:450px;border:1px solid #00ffcc;box-shadow:0 0 50px rgba(0,255,204,0.15);}
.logo{text-align:center;margin-bottom:25px;}
.logo img{max-width:200px;}
h2{color:#00ffcc;text-align:center;font-size:28px;letter-spacing:5px;margin-bottom:10px;}
.sub{color:rgba(255,255,255,0.5);text-align:center;font-size:12px;margin-bottom:30px;}
.tab{display:flex;margin-bottom:30px;border-bottom:1px solid rgba(0,255,204,0.3);}
.tab-btn{flex:1;background:none;border:none;padding:12px;color:rgba(255,255,255,0.5);font-size:16px;font-weight:600;cursor:pointer;}
.tab-btn.active{color:#00ffcc;border-bottom:2px solid #00ffcc;}
.form-container{display:none;}
.form-container.active{display:block;}
.input-group{margin-bottom:20px;}
.input-group input{width:100%;padding:15px;background:rgba(255,255,255,0.05);border:1px solid rgba(0,255,204,0.3);border-radius:15px;color:white;font-size:14px;}
.input-group input:focus{outline:none;border-color:#00ffcc;}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#00ffcc,#0099ff);border:none;border-radius:15px;color:#0a0a2a;font-size:16px;font-weight:800;cursor:pointer;margin-top:10px;}
.error{background:rgba(255,51,102,0.2);border:1px solid #ff3366;border-radius:12px;padding:12px;margin-bottom:20px;text-align:center;color:#ff6b6b;font-size:12px;}
.success{background:rgba(0,255,204,0.15);border:1px solid #00ffcc;border-radius:12px;padding:12px;margin-bottom:20px;text-align:center;color:#00ffcc;}
.divider{text-align:center;margin:20px 0;color:rgba(255,255,255,0.3);font-size:11px;}
.footer{text-align:center;margin-top:25px;font-size:9px;color:rgba(255,255,255,0.25);}
</style>
</head>
<body>
<div class="login-card">
<div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div>
<h2>VENOM X</h2><p class="sub">SMM PANEL</p>
<div class="tab"><button class="tab-btn active" onclick="switchTab('login')">LOGIN</button><button class="tab-btn" onclick="switchTab('register')">REGISTER</button></div>
<div id="loginForm" class="form-container active"><form method="POST" action="/login"><div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div><div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div><button type="submit" class="btn">LOGIN</button></form></div>
<div id="registerForm" class="form-container"><form method="POST" action="/register"><div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div><div class="input-group"><input type="email" name="email" placeholder="EMAIL" required></div><div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div><div class="input-group"><input type="password" name="confirm_password" placeholder="CONFIRM PASSWORD" required></div><button type="submit" class="btn">REGISTER</button></form></div>
<div class="divider">OR</div>
<a href="/google-login"><button class="btn" style="background:rgba(255,255,255,0.1);color:white;">GOOGLE LOGIN</button></a>
<div class="footer">VENOM X SMM PANEL | OWNER VENOMXSMMPY</div>
</div>
<script>
function switchTab(tab){
document.getElementById('loginForm').classList.remove('active');
document.getElementById('registerForm').classList.remove('active');
document.querySelectorAll('.tab-btn').forEach(btn=>btn.classList.remove('active'));
if(tab==='login'){
document.getElementById('loginForm').classList.add('active');
document.querySelector('.tab-btn:first-child').classList.add('active');
}else{
document.getElementById('registerForm').classList.add('active');
document.querySelector('.tab-btn:last-child').classList.add('active');
}}
</script>
</body>
</html>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user and not user.is_banned:
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        return redirect('/admin' if user.is_admin else '/dashboard')
    return redirect('/?error=invalid')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirm_password')
    
    if password != confirm:
        return redirect('/?error=password_mismatch')
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return redirect('/?error=exists')
    
    new_user = User(username=username, email=email, password=password, balance=0)
    db.session.add(new_user)
    db.session.commit()
    
    return redirect('/?success=registered')

@app.route('/google-login')
def google_login():
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
    
    orders_html = ''
    for o in orders:
        orders_html += f'<tr><td>{o.order_id}</td><td>{o.service_name[:20]}</td><td>{o.quantity}</td><td>RS {o.total_amount}</td><td>{o.status}</td><td>{o.created_at.strftime("%Y-%m-%d")}</td></tr>'
    if not orders_html:
        orders_html = '<tr><td colspan="6">NO ORDERS YET</td></tr>'
    
    services_json = str(SERVICES).replace("'", '"')
    
    return f'''
<!DOCTYPE html>
<html>
<head><title>VENOM X - DASHBOARD</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}}
body{{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);}}
.navbar{{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ffcc;}}
.logo img{{height:45px;}}
.nav-links a{{color:#00ffcc;text-decoration:none;margin-left:25px;font-size:12px;}}
.balance{{background:linear-gradient(135deg,#00ffcc,#0099ff);padding:8px 20px;border-radius:30px;color:#0a0a2a;font-weight:800;}}
.container{{padding:30px;}}
.welcome{{color:#00ffcc;margin-bottom:30px;font-size:24px;font-weight:700;}}
.welcome span{{color:white;}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px;}}
.stat-card{{background:rgba(255,255,255,0.05);border:1px solid rgba(0,255,204,0.3);border-radius:20px;padding:25px;text-align:center;}}
.stat-card h3{{color:rgba(255,255,255,0.6);font-size:11px;}}
.stat-card .value{{color:#00ffcc;font-size:32px;font-weight:800;}}
.platforms{{display:flex;gap:25px;margin-bottom:35px;}}
.platform-card{{background:rgba(255,255,255,0.05);border:1px solid #00ffcc;border-radius:20px;padding:25px;text-align:center;width:180px;cursor:pointer;}}
.platform-card img{{width:70px;height:70px;margin-bottom:15px;}}
.platform-card h3{{color:#00ffcc;font-size:16px;}}
.service-form{{display:none;background:rgba(255,255,255,0.05);border-radius:20px;padding:25px;margin-top:25px;}}
.service-form input,.service-form select{{width:100%;padding:14px;margin:10px 0;background:rgba(255,255,255,0.08);border:1px solid rgba(0,255,204,0.3);border-radius:12px;color:white;}}
.service-form button{{width:100%;padding:14px;background:linear-gradient(135deg,#00ffcc,#0099ff);border:none;border-radius:12px;color:#0a0a2a;font-weight:800;cursor:pointer;}}
.table-container{{background:rgba(255,255,255,0.05);border-radius:20px;overflow-x:auto;margin-top:20px;}}
table{{width:100%;border-collapse:collapse;}}
th,td{{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.08);font-size:12px;}}
th{{color:#00ffcc;}}
.section-title{{color:#00ffcc;margin:30px 0 20px;font-size:18px;}}
.modal{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);justify-content:center;align-items:center;z-index:300;}}
.modal-content{{background:#0a0a2a;padding:35px;border-radius:25px;max-width:400px;width:90%;border:1px solid #00ffcc;text-align:center;}}
.modal-content input{{width:100%;padding:14px;margin:10px 0;background:rgba(255,255,255,0.08);border:1px solid #00ffcc;border-radius:12px;color:white;}}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><div class="nav-links"><a href="#">DASHBOARD</a><a href="#" onclick="openAddCash()">ADD CASH</a><a href="/order-history">ORDERS</a><a href="/logout" class="balance">LOGOUT</a></div></div>
<div class="container">
<div class="welcome">WELCOME, <span>{user.username}</span></div>
<div class="stats"><div class="stat-card"><h3>BALANCE</h3><div class="value">RS {user.balance:.2f}</div></div><div class="stat-card"><h3>ORDERS</h3><div class="value">{len(orders)}</div></div></div>
<div class="platforms"><div class="platform-card" onclick="showPlatform('instagram')"><img src="https://i.ibb.co/SXBKM3cS/file-100.jpg"><h3>INSTAGRAM</h3></div><div class="platform-card" onclick="showPlatform('youtube')"><img src="https://i.ibb.co/6jQK0fK/file-99.jpg"><h3>YOUTUBE</h3></div></div>
<div id="serviceForm" class="service-form"><h3 id="serviceTitle" style="color:#00ffcc;">SELECT SERVICE</h3><select id="serviceSelect"></select><input type="text" id="serviceLink" placeholder="ENTER LINK"><input type="number" id="serviceQuantity" placeholder="ENTER QUANTITY"><p id="servicePrice" style="color:#00ffcc;"></p><button onclick="placeOrder()">PLACE ORDER</button></div>
<div id="orderResult"></div>
<h3 class="section-title">RECENT ORDERS</h3><div class="table-container"><table><thead><tr><th>ORDER ID</th><th>SERVICE</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{orders_html}</tbody></table></div></div>
<div id="addCashModal" class="modal"><div class="modal-content"><h2 style="color:#00ffcc;">ADD CASH</h2><input type="number" id="cashAmount" placeholder="AMOUNT (10-500)"><button onclick="generateQR()">GENERATE QR</button><button onclick="closeAddCash()">CANCEL</button><div id="qrResult"></div></div></div>
<script>
let services = {services_json};
let currentPlatform = null;
function showPlatform(p){{
currentPlatform=p;let s=document.getElementById('serviceSelect');s.innerHTML='';
services[p].services.forEach(svc=>{{let opt=document.createElement('option');opt.value=svc.id;opt.text=svc.name+' - RS '+svc.price+'/1K (MIN:'+svc.min+' MAX:'+svc.max+')';s.appendChild(opt);}});
document.getElementById('serviceTitle').innerHTML=services[p].name+' SERVICES';
document.getElementById('serviceForm').style.display='block';
updatePrice();s.onchange=updatePrice;
}}
function updatePrice(){{let sel=document.getElementById('serviceSelect');let id=parseInt(sel.value);let svc=null;for(let s of services[currentPlatform].services){{if(s.id===id){{svc=s;break;}}}}if(svc){{document.getElementById('servicePrice').innerHTML='PRICE: RS '+svc.price+'/1000 | MIN:'+svc.min+' | MAX:'+svc.max;}}}}
function placeOrder(){{let sid=document.getElementById('serviceSelect').value;let link=document.getElementById('serviceLink').value;let qty=document.getElementById('serviceQuantity').value;if(!link||!qty){{alert('FILL ALL FIELDS');return;}}fetch('/place-order',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'service_type='+currentPlatform+'&service_id='+sid+'&link='+encodeURIComponent(link)+'&quantity='+qty}}).then(res=>res.json()).then(data=>{{if(data.success){{document.getElementById('orderResult').innerHTML='<span style="color:#0f0;">ORDER PLACED! ID:'+data.order_id+'</span>';setTimeout(()=>location.reload(),1500);}}else{{document.getElementById('orderResult').innerHTML='<span style="color:#f33;">ERROR:'+data.error+'</span>';}}}});}}
function openAddCash(){{document.getElementById('addCashModal').style.display='flex';}}
function closeAddCash(){{document.getElementById('addCashModal').style.display='none';document.getElementById('qrResult').innerHTML='';}}
function generateQR(){{let amt=document.getElementById('cashAmount').value;if(amt<10||amt>500){{alert('AMOUNT 10-500');return;}}fetch('/add-cash',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'amount='+amt}}).then(res=>res.json()).then(data=>{{if(data.success){{document.getElementById('qrResult').innerHTML='<p style="color:#0ff;">PAY: RS '+data.qr_amount+'</p><img src="data:image/png;base64,'+data.qr_code+'" style="width:160px;"><p>TXN ID:'+data.transaction_id+'</p><p>SEND SCREENSHOT TO BOT</p>';}}else{{alert('ERROR');}}}});}}
</script>
</body>
</html>
    '''

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/')
    users = User.query.all()
    orders = Order.query.all()
    
    users_html = ''
    for u in users:
        if u.is_admin:
            users_html += f'<tr><td>{u.id}</td><td>{u.username}</td><td>RS {u.balance:.2f}</td><td>ACTIVE</td><td><span style="color:#00ffcc;">OWNER</span></td></tr>'
        else:
            users_html += f'<tr><td>{u.id}</td><td>{u.username}</td><td>RS {u.balance:.2f}</td><td>{"BANNED" if u.is_banned else "ACTIVE"}</td><td><button onclick="banUser({u.id})">BAN</button> <button onclick="unbanUser({u.id})">UNBAN</button> <input type="number" id="amt_{u.id}" placeholder="AMT" style="width:70px;"> <button onclick="addBalance({u.id})">+</button></td></tr>'
    
    orders_html = ''
    for o in orders[-50:]:
        orders_html += f'<tr><td>{o.order_id}</td><td>{o.user_id}</td><td>{o.service_name[:15]}</td><td>{o.quantity}</td><td>RS {o.total_amount}</td><td>{o.status}</td><td>{o.created_at.strftime("%Y-%m-%d")}</td></tr>'
    
    return f'''
<!DOCTYPE html>
<html>
<head><title>VENOM X - ADMIN</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}}
body{{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);}}
.navbar{{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ffcc;}}
.logo img{{height:45px;}}
.container{{padding:30px;}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px;}}
.stat-card{{background:rgba(255,255,255,0.05);border:1px solid #00ffcc;border-radius:20px;padding:25px;text-align:center;}}
.stat-card h3{{color:rgba(255,255,255,0.6);font-size:11px;}}
.stat-card .value{{color:#00ffcc;font-size:32px;font-weight:800;}}
.table-container{{background:rgba(255,255,255,0.05);border-radius:20px;overflow-x:auto;margin-top:20px;}}
table{{width:100%;border-collapse:collapse;}}
th,td{{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.08);font-size:12px;}}
th{{color:#00ffcc;}}
h3{{color:#00ffcc;margin:20px 0;}}
button{{background:#00ffcc;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-weight:600;}}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/VYf9Qq2p/file-97.jpg"></div><a href="/logout" style="color:#00ffcc;">LOGOUT</a></div>
<div class="container"><h2 style="color:#00ffcc;">ADMIN PANEL</h2>
<div class="stats"><div class="stat-card"><h3>TOTAL USERS</h3><div class="value">{len(users)}</div></div><div class="stat-card"><h3>TOTAL ORDERS</h3><div class="value">{len(orders)}</div></div></div>
<h3>USERS</h3><div class="table-container"><table><thead><tr><th>ID</th><th>USERNAME</th><th>BALANCE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{users_html}</tbody></table></div>
<h3>ORDERS</h3><div class="table-container"><table><thead><tr><th>ORDER ID</th><th>USER ID</th><th>SERVICE</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{orders_html}</tbody></table></div></div>
<script>
function banUser(id){{ fetch('/admin/ban-user',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'user_id='+id}}).then(()=>location.reload()); }}
function unbanUser(id){{ fetch('/admin/unban-user',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'user_id='+id}}).then(()=>location.reload()); }}
function addBalance(id){{ let amt=document.getElementById('amt_'+id).value; fetch('/admin/add-balance',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'user_id='+id+'&amount='+amt}}).then(()=>location.reload()); }}
</script>
</body>
</html>
    '''

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
        return jsonify({'error': f'Insufficient balance! Need RS {total_price}'}), 400
    
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
        return jsonify({'error': 'Amount must be between 10 and 500'}), 400
    
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
    
    rows = ''
    for o in orders:
        rows += f'<tr><td>{o.order_id}</td><td>{o.service_name}</td><td>{o.link[:30]}</td><td>{o.quantity}</td><td>RS {o.total_amount}</td><td>{o.status}</td><td>{o.created_at.strftime("%Y-%m-%d")}</td></tr>'
    
    return f'''
<!DOCTYPE html>
<html><head><title>ORDER HISTORY</title>
<style>body{{background:linear-gradient(135deg,#0a0a2a,#0f0f3a,#1a1a4a);font-family:monospace;}}.navbar{{background:rgba(10,10,42,0.95);padding:15px;border-bottom:1px solid #00ffcc;}}.container{{padding:30px;}}table{{width:100%;border-collapse:collapse;}}th,td{{padding:10px;color:white;border-bottom:1px solid #333;}}th{{color:#00ffcc;}}h2{{color:#00ffcc;}}</style>
</head>
<body><div class="navbar"><a href="/dashboard" style="color:#00ffcc;">BACK</a></div><div class="container"><h2>ORDER HISTORY</h2><table><thead><tr><th>ORDER ID</th><th>SERVICE</th><th>LINK</th><th>QTY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{rows}</tbody></table></div></body>
</html>
    '''

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
