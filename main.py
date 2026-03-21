import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client

# Мутағйирҳо аз муҳит (дар хостинг гузошта мешаванд)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Захираи муваққатӣ барои скриншотҳо
user_photos = {}

async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Ба клани Delta Force Tajikistan хуш омадед!\n\n"
        "Барои сабти ном, 4 скриншоти зеринро якҷоя фиристед:\n"
        "1. Профиль\n2. Операции\n3. Сражения\n4. Сведения\n\n"
        "Формат: #NICK-ID [номи бозингар] [UID]\n\n"
        "Мисол: #NICK-ID TJ丶Alex 123456789"
    )

async def handle_photos(update: Update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Танҳо дар гурӯҳ кор мекунад
    if chat_id > 0:
        return
    
    # Захираи фото
    if user_id not in user_photos:
        user_photos[user_id] = []
    
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        user_photos[user_id].append(file_id)
    
    # Санҷиши матн
    caption = update.message.caption or ""
    if "#NICK-ID" in caption:
        parts = caption.replace("#NICK-ID", "").strip().split()
        if len(parts) >= 2:
            nickname = parts[0]
            uid = parts[1]
            context.user_data["nickname"] = nickname
            context.user_data["uid"] = uid
    
    # Агар 4 фото ҷамъ шуд
    if len(user_photos.get(user_id, [])) >= 4:
        nickname = context.user_data.get("nickname")
        uid = context.user_data.get("uid")
        
        if not nickname or not uid:
            await update.message.reply_text("❌ Формат нодуруст. Лутфан #NICK-ID [ном] [UID]-ро нависед.")
            user_photos[user_id] = []
            return
        
        # Санҷиши теги TJ丶
        if not nickname.startswith("TJ丶"):
            await update.message.reply_text("⚠️ Номи шумо бояд бо TJ丶 оғоз шавад. Номи худро дар бозӣ тағйир диҳед.")
            user_photos[user_id] = []
            return
        
        # Захира дар Supabase
        supabase.table("members").insert({
            "tg_user_id": user_id,
            "tg_username": update.effective_user.username,
            "nickname": nickname,
            "uid": uid,
            "status": "active"
        }).execute()
        
        await update.message.reply_text(f"✅ Сабти ном муваффақ! Хуш омадед, {nickname}")
        
        # Тоза кардан
        user_photos[user_id] = []
        context.user_data.clear()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_photos))
    app.run_polling()

if __name__ == "__main__":
    main()
