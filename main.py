import os
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client

# ========== ТАНЗИМОТИ ОШКОР ==========
BOT_TOKEN = "8628746700:AAE2ue_5X3WqR8P53rLGwsVlyM6tZT8WiVI"
ADMIN_ID = 6484601057
SUPABASE_URL = "https://dwjgughlyefxkfpqnekc.supabase.co"
SUPABASE_KEY = "sb_publishable_J-gOSzG40A3ulv6Wa6htHw_6f6A6cv7"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Захираи муваққатӣ
user_photos = {}

# ========== ВИКИ АЗ САЙТИ РАСМӢ ==========
WIKI_BASE_URL = "https://www.playdeltaforce.com/act/officialwiki/ru/"

async def fetch_wiki(topic: str = ""):
    """Гирифтани маълумот аз Wiki-и расмӣ"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if topic:
                url = f"{WIKI_BASE_URL}{topic}"
            else:
                url = WIKI_BASE_URL
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text[:4000]  # Маҳдудияти Telegram
            return f"❌ Маълумот барои '{topic}' ёфт нашуд."
    except Exception as e:
        return f"⚠️ Хатогӣ дар пайвастшавӣ: {e}"

async def update_wiki_cache():
    """Навсозии кеши Wiki дар Supabase"""
    topics = ["weapons", "maps", "operators", "guides"]
    for topic in topics:
        content = await fetch_wiki(topic)
        supabase.table("wiki_cache").upsert({
            "topic": topic,
            "content": content,
            "updated_at": datetime.now().isoformat()
        }).execute()

# ========== ФАРМОНҲО ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Delta Force TJ Bot**\n\n"
        "✅ Бот фаъол аст!\n\n"
        "**Фармонҳо:**\n"
        "/start - Маълумот дар бораи бот\n"
        "/status - Маълумоти шахсии шумо\n"
        "/top - Рӯйхати аъзоён\n"
        "/wiki [мавзӯъ] - Маълумот аз Wiki\n"
        "/alive - Санҷиши зинда будани бот\n\n"
        "**Сабти ном:**\n"
        "1. Номи бозигариро ба `TJ丶Ном` иваз кунед\n"
        "2. 4 скриншот (Профиль, Операции, Сражения, Сведения)\n"
        "3. Дар матн нависед: `#NICK-ID TJ丶Ном 123456789`",
        parse_mode="Markdown"
    )

async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Санҷиши зинда будани бот"""
    await update.message.reply_text(
        "🟢 **Бот фаъол аст!**\n\n"
        f"🕐 Вақт: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"📊 Supabase: пайваст\n"
        f"🌐 Wiki API: фаъол\n"
        f"👥 Аъзоён: {supabase.table('members').select('id', count='exact').execute().count}",
        parse_mode="Markdown"
    )

async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ҷустуҷӯ дар Wiki"""
    if not context.args:
        await update.message.reply_text(
            "📚 **Дастури Wiki**\n\n"
            "Истифода: `/wiki [мавзӯъ]`\n\n"
            "Мавзӯъҳо:\n"
            "• weapons - яроқҳо\n"
            "• maps - харитаҳо\n"
            "• operators - амалкунандагон\n"
            "• guides - роҳнамоҳо\n\n"
            "Мисол: `/wiki weapons`",
            parse_mode="Markdown"
        )
        return
    
    topic = context.args[0].lower()
    
    # Аввал аз кеши Supabase меҷӯем
    cached = supabase.table("wiki_cache").select("content").eq("topic", topic).execute()
    
    if cached.data:
        content = cached.data[0]["content"]
        await update.message.reply_text(
            f"📖 **Wiki: {topic}**\n\n{content[:3800]}",
            parse_mode="Markdown"
        )
    else:
        # Агар дар кеш набошад, аз сайт мегирем
        await update.message.reply_text(f"🔄 Дар ҳоли гирифтани маълумот барои '{topic}'...")
        content = await fetch_wiki(topic)
        supabase.table("wiki_cache").upsert({
            "topic": topic,
            "content": content,
            "updated_at": datetime.now().isoformat()
        }).execute()
        await update.message.reply_text(f"📖 **Wiki: {topic}**\n\n{content[:3800]}", parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = supabase.table("members").select("*").eq("tg_user_id", user_id).execute()
    
    if not result.data:
        await update.message.reply_text(
            "❌ Шумо ҳанӯз сабти ном накардаед.\n"
            "Барои сабти ном /start-ро истифода баред."
        )
        return
    
    m = result.data[0]
    await update.message.reply_text(
        f"📊 **Маълумоти шумо**\n\n"
        f"👤 Ном: `{m['nickname']}`\n"
        f"🆔 UID: `{m['uid']}`\n"
        f"📅 Сабт: `{m['joined_at'][:10]}`\n"
        f"✅ Вазъ: `{m['status']}`",
        parse_mode="Markdown"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table("members").select("nickname, uid").eq("status", "active").execute()
    
    if not result.data:
        await update.message.reply_text("Ҳанӯз аъзое нест.")
        return
    
    text = "🏆 **Аъзоёни клан**\n\n"
    for i, m in enumerate(result.data[:15], 1):
        text += f"{i}. {m['nickname']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if chat_id > 0:
        return
    
    if user_id not in user_photos:
        user_photos[user_id] = []
    
    if update.message.photo:
        user_photos[user_id].append(update.message.photo[-1].file_id)
    
    caption = update.message.caption or ""
    if "#NICK-ID" in caption:
        parts = caption.replace("#NICK-ID", "").strip().split()
        if len(parts) >= 2:
            context.user_data["nickname"] = parts[0]
            context.user_data["uid"] = parts[1]
    
    if len(user_photos.get(user_id, [])) >= 4:
        nickname = context.user_data.get("nickname")
        uid = context.user_data.get("uid")
        
        if not nickname or not uid:
            await update.message.reply_text("❌ Формат: #NICK-ID TJ丶Ном 123456")
            user_photos[user_id] = []
            return
        
        if not nickname.startswith("TJ丶"):
            await update.message.reply_text("⚠️ Ном бояд бо TJ丶 оғоз шавад!")
            user_photos[user_id] = []
            return
        
        existing = supabase.table("members").select("*").eq("tg_user_id", user_id).execute()
        if existing.data:
            await update.message.reply_text(f"✅ Шумо аллакай сабт шудаед: {existing.data[0]['nickname']}")
        else:
            supabase.table("members").insert({
                "tg_user_id": user_id,
                "tg_username": update.effective_user.username,
                "nickname": nickname,
                "uid": uid
            }).execute()
            await update.message.reply_text(f"✅ Сабт шуд! Хуш омадед {nickname}")
        
        user_photos[user_id] = []
        context.user_data.clear()

# ========== ОҒОЗ ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alive", alive))
    app.add_handler(CommandHandler("wiki", wiki))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_photos))
    
    print("🤖 Delta Force TJ Bot фаъол шуд!")
    print(f"🕐 Вақт: {datetime.now()}")
    print(f"🔗 Supabase: {SUPABASE_URL}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
