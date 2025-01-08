import logging
import psutil
import subprocess
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

DIR_PATH = os.path.dirname(__file__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open(os.path.join(DIR_PATH, 'token.txt'), 'r') as token:
    TOKEN = token.read().strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def get_system_status():
    # Получение температуры
    temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
    temperature = temp_output.split('=')[1].strip()

    # Получение загрузки CPU и RAM
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    ram_usage = memory.percent

    status = f"Температура процессора: {temperature}\n" f"Загрузка CPU: {cpu_usage}%\n" f"Загрузка RAM: {ram_usage}%"
    return status


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_system_status())


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список доступных команд\n"
        "/status - Показать статус системы (температура, загрузка ЦП и ОЗУ)\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)
    help_handler = CommandHandler('help', help)

    application.add_handler(start_handler)
    application.add_handler(status_handler)
    application.add_handler(help_handler)

    application.run_polling()
