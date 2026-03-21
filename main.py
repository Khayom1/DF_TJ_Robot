import os
from supabase import create_client, Client
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Маълумот аз Supabase
url: str = os.getenv("dwjgughlyefxkfpqnekc")
key: str = os.getenv("sb_publishable_J-gOSzG40A3ulv6Wa6htHw_6f6A6cv7")
supabase: Client = create_client(url, key)

# Маълумоти Бот
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=['register'])
async def register_player(message: types.Message):
    # Сабти бозингар дар базаи Supabase
    user_id = message.from_user.id
    username = message.from_user.username
    
    data, count = supabase.table("players").insert({
        "tg_id": user_id, 
        "name": username, 
        "points": 0
    }).execute()
    
    await message.answer("✅ Шумо дар базаи Delta Force TAJIKISTAN (TJ)🇹🇯 сабт шудед!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
