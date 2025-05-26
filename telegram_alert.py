from telegram import Bot
import asyncio

BOT_TOKEN = "8023492193:AAEmP7PnAHuxpI169VPZj6JoK9y1hSc4jvk"
CHAT_ID = 5168341266  # Replace with integer

async def send_alert(message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)

def send_telegram_alert(message):
    asyncio.run(send_alert(message))
