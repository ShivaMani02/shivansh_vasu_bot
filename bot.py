import os
import re
import threading
import random
import requests
import xml.etree.ElementTree as ET
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from better_profanity import profanity
from waitress import serve

profanity.load_censor_words()
profanity.add_censor_words(["scam", "crypto", "bitcoin", "invest", "free money", "click here to win", "earn fast", "betting"])

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

WEBSITE = "https://theshivanshvasu.com/"
NOTES_LINK = "https://theshivanshvasu.com/notes"
LINKTREE = "https://linktr.ee/shivanshvasu"
YOUTUBE_HANDLE = "@shivanshvasu"
YOUTUBE = f"https://www.youtube.com/{YOUTUBE_HANDLE}"
INSTAGRAM = "https://instagram.com/theshivanshvasuofficial"
LINKEDIN = "https://www.linkedin.com/theshivanshvasu"
X_TWITTER = "https://x.com/theshivanshvasu"
WHATSAPP = "https://whatsapp.com/channel/0029VbAWGE5ICVfcjjKTAS0B"
COURSE_DSA = "https://theshivanshvasu.com/courses/master-dsa-360-series"
COURSE_SYSTEM_DESIGN = "https://theshivanshvasu.com/courses/system-design-mastery-series"
COURSE_FULL_STACK = "https://theshivanshvasu.com/courses/elevate-full-stack-series"
COMMUNITY_TAGLINE = f"Join the community and grow : {YOUTUBE}"

GROUP_ID_FILE = "group_id.txt"
CHANNEL_ID_FILE = "channel_id.txt"
ADMIN_ID_FILE = "admin_id.txt"
LAST_VIDEO_FILE = "last_video.txt"

IST = pytz.timezone('Asia/Kolkata')

def save_id(filename, id_val):
    with open(filename, "w") as f: f.write(str(id_val))

def get_id(filename, env_key=None):
    if env_key and os.environ.get(env_key):
        return os.environ.get(env_key)
    if os.path.exists(filename):
        with open(filename, "r") as f: return f.read().strip()
    return None

def is_admin(chat_id, user_id):
    admin_env_id = get_id(ADMIN_ID_FILE, "ADMIN_ID")
    if admin_env_id and str(user_id) == str(admin_env_id):
        return True
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except:
        return False

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🌐 Website", url=WEBSITE),
        InlineKeyboardButton("📚 Free Notes", url=NOTES_LINK),
        InlineKeyboardButton("🔴 YouTube", url=YOUTUBE),
        InlineKeyboardButton("🔗 All Links", url=LINKTREE),
        InlineKeyboardButton("🎓 View Premium Courses", callback_data="show_courses")
    )
    return markup

def get_courses_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🚀 Master DSA 360", url=COURSE_DSA),
        InlineKeyboardButton("🏗️ System Design", url=COURSE_SYSTEM_DESIGN),
        InlineKeyboardButton("💻 Full Stack", url=COURSE_FULL_STACK)
    )
    return markup

@bot.message_handler(commands=['setgroup'])
def set_group(message):
    if message.chat.type in ['group', 'supergroup'] and is_admin(message.chat.id, message.from_user.id):
        save_id(GROUP_ID_FILE, message.chat.id)
        bot.reply_to(message, "✅ **Success!** This group is now the official active group.", parse_mode="Markdown")

@bot.message_handler(commands=['setchannel'])
def set_channel(message):
    if message.chat.type == 'channel':
        save_id(CHANNEL_ID_FILE, message.chat.id)
        bot.send_message(message.chat.id, "✅ **Success!** This channel is now the official broadcast channel.", parse_mode="Markdown")
    else:
        if is_admin(message.chat.id, message.from_user.id):
            bot.reply_to(message, "Add me as an Admin to your Channel, and type /setchannel in the channel.")

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    if message.chat.type == 'private':
        save_id(ADMIN_ID_FILE, message.from_user.id)
        bot.reply_to(message, "✅ **Success!** You will now receive suggestions via DM.")
    else:
        bot.reply_to(message, "Please run this command in a direct message with me.")

@bot.message_handler(commands=['announce', 'newnotes'])
def channel_announcements(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    channel_id = get_id(CHANNEL_ID_FILE, "CHANNEL_ID")
    if not channel_id:
        return bot.reply_to(message, "❌ Channel not set. Check your .env file or use /setchannel.")
    
    command = message.text.split(' ')[0]
    text = message.text.replace(command, "").strip()
    if not text: return bot.reply_to(message, "❌ Please provide a message.")

    prefix = "📢 **Announcement:**" if command == "/announce" else "📚 **New Notes Uploaded!**"
    try:
        bot.send_message(channel_id, f"{prefix}\n\n{text}", parse_mode="Markdown")
        bot.reply_to(message, f"✅ Successfully broadcasted to the channel!")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed: {e}")

@bot.message_handler(commands=['ban', 'kick', 'mute', 'unban'])
def moderation(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return bot.reply_to(message, "❌ Please reply to the user's message to moderate them.")
    
    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    command = message.text.split(' ')[0]

    try:
        if command in ['/ban', '/kick']:
            bot.ban_chat_member(message.chat.id, target_id)
            bot.reply_to(message, f"🔨 **Banned** {target_name}.")
            if command == '/kick': bot.unban_chat_member(message.chat.id, target_id)
        elif command == '/mute':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=False)
            bot.reply_to(message, f"🔇 **Muted** {target_name}.")
        elif command == '/unban':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
            bot.reply_to(message, f"🔊 **Unmuted / Unbanned** {target_name}.")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to execute. Do I have admin rights? Error: {e}")

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}! 👋\n\n**{COMMUNITY_TAGLINE}**\n\nChoose an option below:", reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['notes'])
def notes_command(message):
    bot.send_message(message.chat.id, f"📚 **Notes Vault:**\n\n- DSA Notes: {NOTES_LINK}\n- Web Dev Notes: {NOTES_LINK}\n- System Design: {NOTES_LINK}")

@bot.message_handler(commands=['syllabus', 'roadmap'])
def syllabus_command(message):
    bot.send_message(message.chat.id, f"🗺️ **Roadmaps & Syllabus:**\nFind our structured curriculum on the website: {WEBSITE}")

@bot.message_handler(commands=['resources', 'sheet'])
def resources_command(message):
    bot.send_message(message.chat.id, f"🔥 **Free Resources & Problem Sheets:**\nAccess the Elite 51 DSA sheet and other resources here: {WEBSITE}")

@bot.message_handler(commands=['doubt'])
def doubt_command(message):
    bot.send_message(message.chat.id, "❓ **How to ask a doubt:**\n1. State the exact problem/question.\n2. Share your code snippet.\n3. Mention what you have tried so far.\n\n_Do not just say 'Bro help' or 'Code not working'._", parse_mode="Markdown")

@bot.message_handler(commands=['quiz'])
def quiz_command(message):
    bot.send_poll(message.chat.id, "What is the time complexity of Binary Search?", ["O(1)", "O(n)", "O(log n)", "O(n^2)"], is_anonymous=False, type='quiz', correct_option_id=2)

@bot.message_handler(commands=['suggest'])
def suggest_command(message):
    text = message.text.replace("/suggest", "").strip()
    if not text: return bot.reply_to(message, "❌ Format: /suggest <your topic/idea>")
    
    admin_id = get_id(ADMIN_ID_FILE, "ADMIN_ID")
    if admin_id:
        bot.send_message(admin_id, f"💡 **New Suggestion from {message.from_user.first_name}**: \n\n{text}")
        bot.reply_to(message, "✅ Thank you! Your suggestion has been sent directly to Shivansh.")
    else:
        bot.reply_to(message, "❌ Admin DM is not configured yet.")

@bot.message_handler(commands=['tip', 'interview'])
def random_tip(message):
    tips = [
        "💡 **Pro Tip**: In System Design, always ask clarifying questions before drawing architecture.",
        "💡 **DSA**: Fast and slow pointer approach (Tortoise and Hare) is great for cycle detection in LinkedLists.",
        "💡 **Interview**: When stuck on a DSA problem, think aloud. The interviewer wants to see your thought process.",
        "💡 **Fact**: Python's list `.sort()` uses Timsort, which runs in O(N log N) worst-case time!"
    ]
    bot.send_message(message.chat.id, random.choice(tips), parse_mode="Markdown")

@bot.message_handler(content_types=['new_chat_members'])
def handle_join(message):
    for new_member in message.new_chat_members:
        if new_member.is_bot: continue
        try:
            bot.restrict_chat_member(message.chat.id, new_member.id, can_send_messages=False)
        except: pass
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ I am Human (Click to verify)", callback_data=f"verify_{new_member.id}"))
        bot.send_message(
            message.chat.id, 
            f"Welcome to the community, [{new_member.first_name}](tg://user?id={new_member.id})! 🎉\n\nPlease click the button below to prove you are human and start chatting.", 
            reply_markup=markup, parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def handle_verification(call):
    user_id = int(call.data.split('_')[1])
    if call.from_user.id == user_id:
        try:
            bot.restrict_chat_member(call.message.chat.id, user_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, f"✅ Verified! Welcome [{call.from_user.first_name}](tg://user?id={user_id}). Check out /start for resources.", parse_mode="Markdown")
        except: pass
    else:
        bot.answer_callback_query(call.id, "❌ This button is not for you!")

@bot.callback_query_handler(func=lambda call: call.data == "show_courses")
def handle_courses(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🎓 **Premium Courses:**", reply_markup=get_courses_keyboard(), parse_mode='Markdown')

@bot.message_handler(content_types=['left_chat_member'])
def handle_leave(message):
    bot.send_message(message.chat.id, f"Goodbye {message.left_chat_member.first_name}! We'll miss you. 👋")

def broadcast_to_all(message_text, pin=False):
    channel_id = get_id(CHANNEL_ID_FILE, "CHANNEL_ID")
    group_id = get_id(GROUP_ID_FILE, "GROUP_ID")
    for target in [channel_id, group_id]:
        if target:
            try:
                msg = bot.send_message(target, message_text, parse_mode="Markdown", disable_web_page_preview=False)
                if pin and str(target) == str(channel_id):
                    bot.pin_chat_message(target, msg.message_id)
            except Exception as e: print(f"Broadcast failed to {target}: {e}")

def check_youtube_rss():
    print("Checking YouTube RSS...")
    channel_id = get_id(CHANNEL_ID_FILE, "CHANNEL_ID")
    group_id = get_id(GROUP_ID_FILE, "GROUP_ID")
    if not channel_id and not group_id: return
    try:
        # For YouTube handles, use the handle directly in RSS feed
        # If using channel ID, use: https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}
        # For handle-based feed (alternative method):
        rss_url = f"https://www.youtube.com/feeds/videos.xml?user={YOUTUBE_HANDLE.lstrip('@')}"
        
        try:
            resp_rss = requests.get(rss_url, timeout=10)
        except:
            # Fallback: Try to fetch from handle page and extract channel ID
            resp = requests.get(f"https://www.youtube.com/{YOUTUBE_HANDLE}", timeout=10)
            yt_channel_id_match = re.search(r'"channelId":"(UC[\w-]+)"', resp.text)
            if not yt_channel_id_match:
                print(f"Could not extract YouTube channel ID")
                return
            yt_channel_id = yt_channel_id_match.group(1)
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={yt_channel_id}"
            resp_rss = requests.get(rss_url, timeout=10)
        root = ET.fromstring(resp_rss.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        latest_entry = root.find('atom:entry', ns)
        
        if latest_entry is not None:
            video_id = latest_entry.find('yt:videoId', ns).text
            video_url = latest_entry.find('atom:link', ns).attrib['href']
            title = latest_entry.find('atom:title', ns).text
            
            last_seen_id = get_id(LAST_VIDEO_FILE)
            if video_id != last_seen_id:
                text = f"🚨 **NEW VIDEO UPLOADED!** 🚨\n\n🎬 **{title}**\n\nWatch it now and drop a like! 👇\n👉 {video_url}"
                broadcast_to_all(text, pin=True)
                save_id(LAST_VIDEO_FILE, video_id)
                print(f"Posted new video: {title}")
    except Exception as e: print(f"YouTube RSS Error: {e}")

def fetch_leetcode_potd():
    try:
        url = "https://leetcode.com/graphql"
        query = {
            "query": """
            query questionOfToday {
                activeDailyCodingChallengeQuestion {
                    link
                    question {
                        title
                        difficulty
                    }
                }
            }
            """
        }
        response = requests.post(url, json=query, timeout=10)
        data = response.json()['data']['activeDailyCodingChallengeQuestion']
        title = data['question']['title']
        difficulty = data['question']['difficulty']
        link = "https://leetcode.com" + data['link']
        return f"🎯 **LeetCode Problem of the Day:**\n\n**{title}** ({difficulty})\n\nSolve it here: {link}\n#POTD #LeetCode #DSA"
    except Exception as e:
        print(f"LeetCode API Error: {e}")
        return "🎯 **Problem of the Day:**\n\nTry solving 'Two Sum' optimally today. Hint: Use a HashMap to do it in O(N) time!\n#POTD #DSA"

def fetch_zenquote():
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        data = response.json()
        quote = data[0]['q']
        author = data[0]['a']
        return f"🌟 **Sunday Motivation:**\n\n_\"{quote}\"_\n— **{author}**"
    except:
        return "🌟 **Sunday Motivation:**\n\n_\"The only way to do great work is to love what you do.\"_\n— **Steve Jobs**"

def send_daily_dsa():
    broadcast_to_all("☀️ **Good Morning! Daily DSA Tip:**\n\nAlways analyze time and space complexity BEFORE you write the actual code. Think of edge cases like empty arrays or negative numbers!")

def send_potd():
    message = fetch_leetcode_potd()
    broadcast_to_all(message)

def send_weekly_topic():
    broadcast_to_all("📚 **Topic of the Week:**\n\nThis week we focus on **Dynamic Programming**. Start with Fibonacci, move to Knapsack, and understand state transitions.\nGood luck!")

def send_sunday_quote():
    message = fetch_zenquote()
    broadcast_to_all(message)

scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(func=check_youtube_rss, trigger="interval", hours=12)
scheduler.add_job(func=send_daily_dsa, trigger="cron", hour=8, minute=0)
scheduler.add_job(func=send_potd, trigger="cron", hour=9, minute=0)
scheduler.add_job(func=send_weekly_topic, trigger="cron", day_of_week='mon', hour=10, minute=0)
scheduler.add_job(func=send_sunday_quote, trigger="cron", day_of_week='sun', hour=13, minute=0)
scheduler.start()

@bot.message_handler(func=lambda message: True)
def auto_moderator_and_marketing(message):
    text = message.text.lower()
    if text.startswith('/'): return
    
    if profanity.contains_profanity(text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            warning = bot.send_message(message.chat.id, f"⚠️ [{message.from_user.first_name}](tg://user?id={message.from_user.id}), please do not use inappropriate language or spam.", parse_mode="Markdown")
            threading.Timer(5.0, lambda: bot.delete_message(message.chat.id, warning.message_id)).start()
        except: pass
        return

    if any(keyword in text for keyword in ["notes", "pdf", "study material", "resources"]):
        bot.reply_to(message, f"Hey! Need notes? 📚 Access our complete vault here: {NOTES_LINK}")
    elif any(keyword in text for keyword in ["dsa", "leetcode", "data structures"]):
        bot.reply_to(message, f"Struggling with DSA? Check out the **Master DSA 360 Series**: {COURSE_DSA}", parse_mode='Markdown')

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Shivansh Vasu Bot</title>
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #0f172a; color: white; font-family: 'Inter', sans-serif; margin: 0; overflow: hidden; }
        .container { text-align: center; padding: 40px; border-radius: 20px; background: rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.5); animation: float 4s ease-in-out infinite; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px); }
        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-15px); } 100% { transform: translateY(0px); } }
        .emoji { font-size: 70px; margin: 0; display: inline-block; animation: wave 2.5s infinite; transform-origin: 70% 70%; }
        @keyframes wave { 0% { transform: rotate( 0.0deg) } 10% { transform: rotate(14.0deg) } 20% { transform: rotate(-8.0deg) } 30% { transform: rotate(14.0deg) } 40% { transform: rotate(-4.0deg) } 50% { transform: rotate( 10.0deg) } 60% { transform: rotate( 0.0deg) } 100% { transform: rotate( 0.0deg) } }
        h1 { margin: 15px 0 5px; font-size: 26px; }
        p { color: #94a3b8; margin-bottom: 25px; }
        .btn { display: inline-block; padding: 12px 25px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; text-decoration: none; border-radius: 30px; font-weight: bold; transition: 0.3s; }
        .btn:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(139, 92, 246, 0.5); }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">👋🤖</div>
        <h1>Beep Boop! I'm Awake!</h1>
        <p>Your Telegram Bot is running perfectly on the cloud.</p>
        <a href="https://www.theshivanshvasu.com" class="btn" target="_blank">Visit theshivanshvasu.com</a>
    </div>
</body>
</html>"""
    return html

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
