import os
import json
import re
import random
import asyncio
import threading
import qrcode
from io import BytesIO
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ FLASK FOR RENDER ============
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "SMM Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host='0.0.0.0', port=port)

# ============ CONFIG ============
BOT_TOKEN = "8616568737:AAGqynqlVRjrcyTue4Zp9eCEd8-SFP88o14"
OWNER_ID = 8986441675
ADMIN_IDS = [OWNER_ID]

# Files
USERS_FILE = "users.json"
ORDERS_FILE = "orders.json"
PENDING_FILE = "pending.json"

# ============ FILE FUNCTIONS ============
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_pending(pending):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

users = load_users()
orders = load_orders()
pending_tx = load_pending()

# ============ SERVICES DATA ============
SERVICES = {
    "youtube": {
        "name": "📺 YouTube",
        "emoji": "📺",
        "services": [
            {"id": 1, "name": "YouTube Views", "price": 7, "min": 100, "max": 100000},
            {"id": 2, "name": "YouTube Likes", "price": 7, "min": 10, "max": 10000},
            {"id": 3, "name": "YouTube Subscribers", "price": 7, "min": 10, "max": 10000},
            {"id": 4, "name": "YouTube Comments", "price": 7, "min": 5, "max": 1000},
        ]
    },
    "instagram": {
        "name": "📸 Instagram",
        "emoji": "📸",
        "services": [
            {"id": 11, "name": "Instagram Followers", "price": 7, "min": 50, "max": 50000},
            {"id": 12, "name": "Instagram Likes", "price": 7, "min": 20, "max": 20000},
            {"id": 13, "name": "Instagram Views", "price": 7, "min": 100, "max": 100000},
            {"id": 14, "name": "Instagram Comments", "price": 7, "min": 5, "max": 1000},
        ]
    },
    "telegram": {
        "name": "✈️ Telegram",
        "emoji": "✈️",
        "services": [
            {"id": 21, "name": "Telegram Members", "price": 7, "min": 100, "max": 50000},
            {"id": 22, "name": "Telegram Post Views", "price": 7, "min": 100, "max": 100000},
            {"id": 23, "name": "Telegram Reactions", "price": 7, "min": 10, "max": 10000},
        ]
    },
    "spotify": {
        "name": "🎵 Spotify",
        "emoji": "🎵",
        "services": [
            {"id": 31, "name": "Spotify Plays", "price": 7, "min": 100, "max": 100000},
            {"id": 32, "name": "Spotify Followers", "price": 7, "min": 10, "max": 10000},
            {"id": 33, "name": "Spotify Saves", "price": 7, "min": 10, "max": 5000},
        ]
    }
}

# ============ HELPERS ============
def generate_random_paise():
    return random.randint(1, 99)

def generate_qr(amount, user_id, order_id):
    upi_id = "venomxpay@naviaxis"
    upi_link = f"upi://pay?pa={upi_id}&pn=SMM&am={amount}&cu=INR&tn={order_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def extract_amount_from_sms(text):
    patterns = [r'Rs\.?\s*(\d+\.?\d*)', r'₹\s*(\d+\.?\d*)', r'debited\s*Rs\.?\s*(\d+\.?\d*)']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

def extract_tx_id(text):
    patterns = [r'Txn ID[:\s]*(\d+)', r'Transaction ID[:\s]*(\d+)', r'(\d{10,15})']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📺 YouTube Services", callback_data="cat_youtube")],
        [InlineKeyboardButton("📸 Instagram Services", callback_data="cat_instagram")],
        [InlineKeyboardButton("✈️ Telegram Services", callback_data="cat_telegram")],
        [InlineKeyboardButton("🎵 Spotify Services", callback_data="cat_spotify")],
        [InlineKeyboardButton("💰 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📜 Order History", callback_data="history")],
        [InlineKeyboardButton("🛡️ Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wallet_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add Cash", callback_data="add_cash")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ============ WELCOME PHOTO ============
WELCOME_PHOTO_URL = "https://i.ibb.co/r2PJKntQ/file-62.jpg"

# ============ BOT COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or "NoUsername"
    first_name = user.first_name
    
    # Register new user
    if user_id not in users:
        users[user_id] = {
            "id": user_id,
            "username": username,
            "name": first_name,
            "balance": 0,
            "joined": str(datetime.now()),
            "banned": False
        }
        save_users(users)
        
        # Notify owner
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🆕 NEW USER!\n\nID: {user_id}\nUsername: @{username}\nName: {first_name}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    if users.get(user_id, {}).get("banned"):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    # Send welcome photo
    try:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=WELCOME_PHOTO_URL,
            caption=f"✨ Welcome to VENOM X SMM Panel, {first_name}! ✨\n\nYour ID: {user_id}\nYour Balance: ₹{users[user_id].get('balance', 0)}\n\nChoose a service below 👇",
            reply_markup=get_main_keyboard()
        )
    except:
        await update.message.reply_text(
            f"✨ Welcome to VENOM X SMM Panel, {first_name}! ✨\n\nYour ID: {user_id}\nYour Balance: ₹{users[user_id].get('balance', 0)}\n\nChoose a service below 👇",
            reply_markup=get_main_keyboard()
        )

# ============ CALLBACK HANDLER ============
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data
    
    if users.get(user_id, {}).get("banned"):
        await query.message.edit_text("❌ You are banned from using this bot.")
        return
    
    # Main Menu
    if data == "main_menu":
        await query.message.edit_text(
            f"✨ Welcome Back! ✨\n\nYour Balance: ₹{users[user_id].get('balance', 0)}",
            reply_markup=get_main_keyboard()
        )
    
    # Category Selection
    elif data == "cat_youtube":
        keyboard = []
        for s in SERVICES["youtube"]["services"]:
            keyboard.append([InlineKeyboardButton(f"{s['name']} - ₹{s['price']}/1K", callback_data=f"service_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("📺 **YouTube Services**\n\nSelect a service:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "cat_instagram":
        keyboard = []
        for s in SERVICES["instagram"]["services"]:
            keyboard.append([InlineKeyboardButton(f"{s['name']} - ₹{s['price']}/1K", callback_data=f"service_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("📸 **Instagram Services**\n\nSelect a service:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "cat_telegram":
        keyboard = []
        for s in SERVICES["telegram"]["services"]:
            keyboard.append([InlineKeyboardButton(f"{s['name']} - ₹{s['price']}/1K", callback_data=f"service_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("✈️ **Telegram Services**\n\nSelect a service:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "cat_spotify":
        keyboard = []
        for s in SERVICES["spotify"]["services"]:
            keyboard.append([InlineKeyboardButton(f"{s['name']} - ₹{s['price']}/1K", callback_data=f"service_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("🎵 **Spotify Services**\n\nSelect a service:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    # Service Selection
    elif data.startswith("service_"):
        service_id = int(data.split("_")[1])
        context.user_data['selected_service'] = service_id
        
        # Find service details
        service_info = None
        for cat, cat_data in SERVICES.items():
            for s in cat_data["services"]:
                if s["id"] == service_id:
                    service_info = s
                    break
            if service_info:
                break
        
        if service_info:
            await query.message.edit_text(
                f"📦 **{service_info['name']}**\n\n"
                f"💰 Price: ₹{service_info['price']} per 1000\n"
                f"📊 Minimum: {service_info['min']}\n"
                f"📈 Maximum: {service_info['max']}\n\n"
                f"Send the link/username to proceed:\n"
                f"Example: https://instagram.com/username\n\n"
                f"Send /cancel to abort.",
                parse_mode="Markdown"
            )
            context.user_data['step'] = 'waiting_link'
    
    # Wallet
    elif data == "wallet":
        balance = users[user_id].get('balance', 0)
        await query.message.edit_text(
            f"💰 **Your Wallet** 💰\n\n"
            f"Balance: ₹{balance}\n\n"
            f"Total Orders: {len([o for o in orders.values() if o['user_id'] == user_id])}\n\n"
            f"Use /addcash to add funds to your wallet.",
            reply_markup=get_wallet_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "add_cash":
        await query.message.edit_text(
            "💵 **Add Cash** 💵\n\n"
            "Send amount (₹10 - ₹500):\n\n"
            "Example: 100\n\n"
            "Send /cancel to abort."
        )
        context.user_data['step'] = 'waiting_amount'
    
    # Order History
    elif data == "history":
        user_orders = [o for o in orders.values() if o['user_id'] == user_id]
        if not user_orders:
            await query.message.edit_text("📭 No orders found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))
        else:
            msg = "📜 **Your Orders** 📜\n\n"
            for o in user_orders[-10:]:
                msg += f"🆔 {o['order_id']}\n📦 {o['service_name']}\n📊 {o['quantity']}\n💰 ₹{o['total']}\n📅 {o['date'][:16]}\n📌 Status: {o['status']}\n\n"
            await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")
    
    # Support
    elif data == "support":
        await query.message.edit_text(
            "🛡️ **Support** 🛡️\n\n"
            "For any issues, contact:\n"
            "👑 Developer: @iflexvenom\n\n"
            "For payment issues, send transaction ID to bot.\n\n"
            "Email: support@venomx.com",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

# ============ MESSAGE HANDLER ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if users.get(user_id, {}).get("banned"):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    step = context.user_data.get('step')
    
    if step == 'waiting_link':
        context.user_data['link'] = text
        context.user_data['step'] = 'waiting_quantity'
        
        service_id = context.user_data.get('selected_service')
        service_info = None
        for cat, cat_data in SERVICES.items():
            for s in cat_data["services"]:
                if s["id"] == service_id:
                    service_info = s
                    break
            if service_info:
                break
        
        if service_info:
            await update.message.reply_text(
                f"✅ Link received: {text}\n\n"
                f"Now send the quantity (Min: {service_info['min']}, Max: {service_info['max']}):\n\n"
                f"Example: 1000\n\n"
                f"Send /cancel to abort."
            )
    
    elif step == 'waiting_quantity':
        try:
            quantity = int(text)
            service_id = context.user_data.get('selected_service')
            link = context.user_data.get('link')
            
            service_info = None
            for cat, cat_data in SERVICES.items():
                for s in cat_data["services"]:
                    if s["id"] == service_id:
                        service_info = s
                        break
                if service_info:
                    break
            
            if quantity < service_info['min'] or quantity > service_info['max']:
                await update.message.reply_text(f"❌ Quantity must be between {service_info['min']} and {service_info['max']}. Try again:")
                return
            
            total_price = (quantity / 1000) * service_info['price']
            
            # Check balance
            balance = users[user_id].get('balance', 0)
            if balance < total_price:
                await update.message.reply_text(
                    f"❌ **Insufficient Balance!** ❌\n\n"
                    f"Required: ₹{total_price}\n"
                    f"Your Balance: ₹{balance}\n\n"
                    f"Please add cash using /addcash",
                    parse_mode="Markdown"
                )
                context.user_data['step'] = None
                return
            
            # Deduct balance
            users[user_id]['balance'] = balance - total_price
            save_users(users)
            
            # Create order
            order_id = f"SMM{random.randint(100000, 999999)}"
            orders[order_id] = {
                "order_id": order_id,
                "user_id": user_id,
                "service_id": service_id,
                "service_name": service_info['name'],
                "link": link,
                "quantity": quantity,
                "total": total_price,
                "status": "Processing",
                "date": str(datetime.now())
            }
            save_orders(orders)
            
            # Notify owner
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🆕 **NEW ORDER!**\n\n"
                     f"Order ID: {order_id}\n"
                     f"User: @{users[user_id].get('username', 'NoUsername')}\n"
                     f"Service: {service_info['name']}\n"
                     f"Quantity: {quantity}\n"
                     f"Total: ₹{total_price}\n"
                     f"Link: {link}"
            )
            
            await update.message.reply_text(
                f"✅ **ORDER PLACED!** ✅\n\n"
                f"Order ID: `{order_id}`\n"
                f"Service: {service_info['name']}\n"
                f"Quantity: {quantity}\n"
                f"Total: ₹{total_price}\n"
                f"Status: Processing\n\n"
                f"Your order will be delivered soon.\n"
                f"Use /history to check all orders.",
                parse_mode="Markdown"
            )
            
            context.user_data['step'] = None
            
        except ValueError:
            await update.message.reply_text("❌ Please send a valid number for quantity.")
    
    elif step == 'waiting_amount':
        try:
            amount = int(text)
            if amount < 10 or amount > 500:
                await update.message.reply_text("❌ Amount must be between ₹10 and ₹500. Try again:")
                return
            
            # Generate random paise
            random_paise = generate_random_paise()
            qr_amount = amount + (random_paise / 100)
            order_id = f"CASH{random.randint(100000, 999999)}"
            
            context.user_data['cash_order_id'] = order_id
            context.user_data['cash_amount'] = amount
            context.user_data['qr_amount'] = qr_amount
            context.user_data['step'] = 'waiting_payment'
            
            img_bytes = generate_qr(qr_amount, user_id, order_id)
            photo = InputFile(img_bytes, filename="qr.png")
            
            await context.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=f"💵 **ADD CASH** 💵\n\n"
                        f"Amount: ₹{amount}\n"
                        f"**Pay this exact amount: ₹{qr_amount}**\n\n"
                        f"📸 Send SCREENSHOT after payment\n"
                        f"🔖 Or send TRANSACTION ID\n\n"
                        f"UPI: venomxpay@naviaxis\n\n"
                        f"Send /cancel to abort.",
                parse_mode="Markdown"
            )
            
            # Store pending
            pending_tx[order_id] = {
                "user_id": user_id,
                "amount": amount,
                "qr_amount": qr_amount,
                "status": "pending"
            }
            save_pending(pending_tx)
            
        except ValueError:
            await update.message.reply_text("❌ Please send a valid number amount.")
    
    elif step == 'waiting_payment':
        # Handle screenshot or transaction ID
        if update.message.photo:
            photo = update.message.photo[-1]
            caption = f"💰 Payment from user {user_id}\nAmount: {context.user_data.get('cash_amount')}"
            await context.bot.send_photo(chat_id=OWNER_ID, photo=photo.file_id, caption=caption)
            await update.message.reply_text("✅ Screenshot forwarded to admin. Your wallet will be credited soon.")
            context.user_data['step'] = None
        else:
            # Check if it's a transaction ID
            tx_id = extract_tx_id(text)
            if tx_id:
                await verify_payment_manual(update, context, tx_id)
            else:
                await update.message.reply_text("❌ Please send a valid transaction ID or payment screenshot.")
    
    else:
        # Check if user sent transaction ID directly
        tx_id = extract_tx_id(text)
        if tx_id:
            await verify_payment_manual(update, context, tx_id)
        else:
            await update.message.reply_text("Use /start to begin using the bot.")

# ============ PAYMENT VERIFICATION ============
async def verify_payment_manual(update: Update, context: ContextTypes.DEFAULT_TYPE, tx_id):
    user_id = str(update.effective_user.id)
    
    # Check if this TXN is pending
    order_id = None
    for oid, data in pending_tx.items():
        if data.get('user_id') == user_id:
            order_id = oid
            break
    
    if order_id and order_id in pending_tx:
        amount = pending_tx[order_id]['amount']
        
        # Add balance to user
        users[user_id]['balance'] = users[user_id].get('balance', 0) + amount
        save_users(users)
        
        # Remove from pending
        del pending_tx[order_id]
        save_pending(pending_tx)
        
        await update.message.reply_text(
            f"✅ **PAYMENT VERIFIED!** ✅\n\n"
            f"Amount: ₹{amount}\n"
            f"Your new balance: ₹{users[user_id]['balance']}\n\n"
            f"Use /start to order services!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ No pending payment found for this transaction ID.")

# ============ SMS HANDLER ============
async def sms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    text = update.message.text
    sms_amount = extract_amount_from_sms(text)
    
    if not sms_amount:
        await update.message.reply_text("Could not extract amount from SMS.")
        return
    
    # Find pending payment with matching QR amount
    for order_id, data in pending_tx.items():
        if data.get('qr_amount') == sms_amount:
            user_id = data['user_id']
            amount = data['amount']
            
            users[user_id]['balance'] = users[user_id].get('balance', 0) + amount
            save_users(users)
            
            del pending_tx[order_id]
            save_pending(pending_tx)
            
            await update.message.reply_text(f"✅ AUTO-VERIFIED!\nUser {user_id} added ₹{amount}")
            
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"✅ **PAYMENT AUTO-VERIFIED!** ✅\n\n"
                     f"Amount: ₹{amount}\n"
                     f"Your new balance: ₹{users[user_id]['balance']}\n\n"
                     f"Use /start to order services!",
                parse_mode="Markdown"
            )
            return
    
    await update.message.reply_text(f"Payment detected but no matching pending order!\nAmount: ₹{sms_amount}")

# ============ ADD CASH COMMAND ============
async def addcash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if users.get(user_id, {}).get("banned"):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    await update.message.reply_text(
        "💵 **Add Cash** 💵\n\n"
        "Send amount (₹10 - ₹500):\n\n"
        "Example: 100\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )
    context.user_data['step'] = 'waiting_amount'

# ============ OWNER PANEL COMMANDS ============
async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 Users List", callback_data="owner_users")],
        [InlineKeyboardButton("📊 Total Orders", callback_data="owner_orders")],
        [InlineKeyboardButton("💰 Total Volume", callback_data="owner_volume")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="owner_ban")],
        [InlineKeyboardButton("✅ Unban User", callback_data="owner_unban")],
        [InlineKeyboardButton("➕ Add Balance", callback_data="owner_add_balance")],
    ]
    await update.message.reply_text("👑 **Owner Panel**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.message.edit_text("❌ Admin only!")
        return
    
    data = query.data
    
    if data == "owner_users":
        msg = "👥 **Users List**\n\n"
        for uid, u in users.items():
            msg += f"🆔 {uid}\n📛 @{u.get('username', 'NoUsername')}\n💰 ₹{u.get('balance', 0)}\n🚫 {'Banned' if u.get('banned') else 'Active'}\n\n"
        await query.message.edit_text(msg[:4000] if len(msg) > 4000 else msg, parse_mode="Markdown")
    
    elif data == "owner_orders":
        total_orders = len(orders)
        await query.message.edit_text(f"📊 **Total Orders:** {total_orders}", parse_mode="Markdown")
    
    elif data == "owner_volume":
        total_volume = sum([o.get('total', 0) for o in orders.values()])
        await query.message.edit_text(f"💰 **Total Volume:** ₹{total_volume}", parse_mode="Markdown")
    
    elif data == "owner_ban":
        await query.message.edit_text("Send /ban USER_ID to ban a user.\nExample: /ban 123456789")
    
    elif data == "owner_unban":
        await query.message.edit_text("Send /unban USER_ID to unban a user.\nExample: /unban 123456789")
    
    elif data == "owner_add_balance":
        await query.message.edit_text("Send /addbalance USER_ID AMOUNT\nExample: /addbalance 123456789 100")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /ban USER_ID")
        return
    
    user_id = context.args[0]
    if user_id in users:
        users[user_id]['banned'] = True
        save_users(users)
        await update.message.reply_text(f"✅ User {user_id} banned!")
    else:
        await update.message.reply_text("User not found!")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /unban USER_ID")
        return
    
    user_id = context.args[0]
    if user_id in users:
        users[user_id]['banned'] = False
        save_users(users)
        await update.message.reply_text(f"✅ User {user_id} unbanned!")
    else:
        await update.message.reply_text("User not found!")

async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addbalance USER_ID AMOUNT")
        return
    
    user_id = context.args[0]
    try:
        amount = float(context.args[1])
    except:
        await update.message.reply_text("Invalid amount!")
        return
    
    if user_id in users:
        users[user_id]['balance'] = users[user_id].get('balance', 0) + amount
        save_users(users)
        await update.message.reply_text(f"✅ Added ₹{amount} to user {user_id}")
        
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"✅ ₹{amount} has been added to your wallet!\nNew balance: ₹{users[user_id]['balance']}"
        )
    else:
        await update.message.reply_text("User not found!")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled. Use /start to begin again.")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_orders = [o for o in orders.values() if o['user_id'] == user_id]
    
    if not user_orders:
        await update.message.reply_text("📭 No orders found.")
        return
    
    msg = "📜 **Your Orders** 📜\n\n"
    for o in user_orders[-10:]:
        msg += f"🆔 {o['order_id']}\n📦 {o['service_name']}\n📊 {o['quantity']}\n💰 ₹{o['total']}\n📅 {o['date'][:16]}\n📌 Status: {o['status']}\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balance = users.get(user_id, {}).get('balance', 0)
    await update.message.reply_text(f"💰 Your balance: ₹{balance}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 **SMM Bot Commands**\n\n"
        "/start - Start the bot\n"
        "/balance - Check wallet balance\n"
        "/addcash - Add money to wallet\n"
        "/history - View order history\n"
        "/cancel - Cancel current operation\n"
        "/help - Show this help\n\n"
        "👑 Developer: @iflexvenom",
        parse_mode="Markdown"
    )

# ============ MAIN ============
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcash", addcash_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", owner_panel))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("addbalance", addbalance_command))
    
    # Handlers
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(owner_callback, pattern="owner_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sms_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    print("=" * 50)
    print("🤖 SMM BOT STARTED - FULLY FIXED")
    print(f"👑 Owner: {OWNER_ID}")
    print("=" * 50)
    
    application.run_polling()

if __name__ == "__main__":
    main()