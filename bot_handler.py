import os
from mqtt_handler import latest_status
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from mqtt_handler import last_status

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

@bot.message_handler(commands=['status'])
def status_handler(message):
    if last_status:
        bot.send_message(message.chat.id, last_status, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Данных ещё нет.")


def status_command(update, context):
    if latest_status:
        context.bot.send_message(chat_id=update.effective_chat.id, text=latest_status, parse_mode='Markdown')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Данных ещё нет.")

def start_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", status_command))
    updater.start_polling()
