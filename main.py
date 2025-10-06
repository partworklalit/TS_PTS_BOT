import telebot
import os
import json
import time
import threading
import requests
from operator import itemgetter

# === CONFIG ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "partworklalit/TS_PTS_BOT_POINTS_DATA"
FILE_PATH = "points.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATA_FILE = "points.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Ping loop ke liye global control variable
ping_active = False

# === Data functions ===
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# === /addpoints ===
@bot.message_handler(commands=['addpoints'])
def add_points(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Ye command sirf admin ke liye hai.")
    try:
        parts = message.text.split()
        task_no = parts[1]      # "#001"
        points = int(parts[2].replace('+', ''))
        user_tag = parts[3]     # "@username" ya numeric ID

        data = load_data()
        user_id = user_tag.replace('@', '')

        if user_id not in data["users"]:
            data["users"][user_id] = {"username": user_tag, "points": 0}
        data["users"][user_id]["points"] += points

        save_data(data)
        bot.reply_to(message, f"✅ {user_tag} ko {points} points diye gaye (Task {task_no})")
    except Exception as e:
        bot.reply_to(message, "⚠️ Format galat hai.\nSahi format: /addpoints #001 +5 @username")

# === /mypoints ===
@bot.message_handler(commands=['mypoints'])
def my_points(message):
    data = load_data()
    user_id = str(message.from_user.id)
    username = f"@{message.from_user.username}" if message.from_user.username else user_id

    if user_id not in data["users"]:
        data["users"][user_id] = {"username": username, "points": 0}
        save_data(data)

    points = data["users"][user_id]["points"]
    bot.reply_to(message, f"💰 {username}, aapke total points: {points}")

# === /requestupdate ===
@bot.message_handler(commands=['requestupdate'])
def request_update(message):
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    bot.send_message(ADMIN_ID, f"📬 {username} ne request bheji hai apne points update karne ke liye.")
    bot.reply_to(message, "🕒 Aapki request admin ko bhej di gayi hai.")

# === /ranking ===
@bot.message_handler(commands=['ranking'])
def user_ranking(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data["users"]:
        return bot.reply_to(message, "Aapke abhi 0 points hain.")
    
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["points"], reverse=True)
    rank = next((i+1 for i, u in enumerate(sorted_users) if u[0] == user_id), None)
    total = len(sorted_users)
    bot.reply_to(message, f"🏅 Aapki ranking: {rank}/{total}")

# === /rank ===
@bot.message_handler(commands=['rank'])
def leaderboard(message):
    data = load_data()
    if not data["users"]:
        return bot.reply_to(message, "Abhi tak koi points nahi diye gaye.")
    
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["points"], reverse=True)
    top10 = sorted_users[:10]
    msg = "🏆 Top 10 Members:\n\n"
    for i, (uid, info) in enumerate(top10, start=1):
        msg += f"{i}. {info['username']} — {info['points']} pts\n"
    bot.reply_to(message, msg)

# === Ping system ===
def ping_bot():
    global ping_active
    while ping_active:
        try:
            start = time.time()
            # Telegram ke getMe se ping calculate karte hain
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            ping_time = int((time.time() - start) * 1000)
            bot.send_message(ADMIN_ID, f"💓 Bot Active | Ping: {ping_time} ms")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ Ping error: {e}")
        time.sleep(3)  # 5 minutes = 300 seconds

@bot.message_handler(commands=['pingactive'])
def start_ping(message):
    global ping_active
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Ye command sirf admin ke liye hai.")
    if ping_active:
        return bot.reply_to(message, "✅ Ping system already active hai.")
    ping_active = True
    threading.Thread(target=ping_bot, daemon=True).start()
    bot.reply_to(message, "🚀 Ping system active ho gaya! Har 3 second me ping message aayega.")

@bot.message_handler(commands=['pingdisable'])
def stop_ping(message):
    global ping_active
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Ye command sirf admin ke liye hai.")
    ping_active = False
    bot.reply_to(message, "🛑 Ping system disable kar diya gaya.")

# === /removeuser ===
@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Ye command sirf admin ke liye hai.")
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "⚠️ Format galat hai.\nSahi format: /removeuser @username ya /removeuser 123456789")
        
        user_tag = parts[1].replace('@', '')
        data = load_data()

        if user_tag in data["users"]:
            del data["users"][user_tag]
            save_data(data)
            bot.reply_to(message, f"🗑️ {user_tag} ko points list se remove kar diya gaya.")
        else:
            bot.reply_to(message, f"❌ {user_tag} list me nahi mila.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error aaya: {e}")

# === Start bot ===
print("Bot is running...")
bot.polling(non_stop=True)
