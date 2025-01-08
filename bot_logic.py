import logging
import psutil
import subprocess
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

DIR_PATH = os.path.dirname(__file__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open(os.path.join(DIR_PATH, 'token.txt'), 'r') as token:
    TOKEN = token.read().strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def get_system_status():
    # Получение температуры
    temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
    temperature = temp_output.split('=')[1].strip()

    # Получение загрузки CPU и RAM
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    ram_usage = memory.percent

    # Фильтрация дисков
    allowed_mount_points = {"/", "/boot/firmware", "/mnt/SSD4TB/D"}
    allowed_devices = re.compile(r"mmcblk0p[12]|sd[a-z]+\d+")

    # Получение информации о дисках через psutil
    disk_info = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            # Фильтрация по точкам монтирования и устройствам
            if partition.mountpoint in allowed_mount_points or allowed_devices.match(partition.device.split("/")[-1]):
                usage = psutil.disk_usage(partition.mountpoint)
                # Форматирование с экранированием Markdown
                disk_info.append(
                    f"🔹 *Диск {partition.device.replace('.', '\.')}* ({partition.mountpoint.replace('.', '\.')})\n"
                    f"   📊 *{usage.percent}%* использовано\n"
                    f"   💾 *{usage.free / (1024 ** 3):.2f} GB* свободно"
                )
        except PermissionError:
            # Пропустить разделы, к которым нет доступа
            continue

    # Формирование итогового статуса с форматированием
    status = (
        f"🖥️ *Статус системы:* \n\n"
        f"🌡️ *Температура процессора:* {temperature.replace('.', '\.')}\n"
        f"⚙️ *Загрузка CPU:* {cpu_usage}%\n"
        f"🧠 *Загрузка RAM:* {ram_usage}%\n\n"
        f"💾 *Информация о дисках:* \n"
    )

    # Если данные о дисках есть, добавляем их в статус
    if disk_info:
        status += "\n".join(disk_info)
    else:
        status += "🔴 Нет данных о дисках"

    return status


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await get_system_status()
    await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="MarkdownV2", text=text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список доступных команд\n"
        "/status - Показать статус системы (температура, загрузка ЦП и ОЗУ)\n"
        "/check_ssd_2tb - Проверяет - доступен ли SSD для чтения\n"
        "/remount_ssd_2tb - Заново перемонтирует SSD\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


async def status_ssd_2tb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция проверяет статус SSD на 2 ГБ."""
    directory = "/mnt/SSD_4TB/D"
    try:
        # если диск размонтировался, то выпадет ошибка чтения
        os.listdir(directory)
        message = "Диск доступен для чтения"
    except OSError as e:
        message = f"Ошибка при чтении диска: {str(e)}"
    finally:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def remount_ssd_2tb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            ['/bin/bash', '/home/andrey/scripts/check_mount.sh'], capture_output=True, text=True, check=True
        )
        message = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        message = f'Ошибка при примонтировании SSD: {str(e)}'
    finally:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)
    help_handler = CommandHandler('help', help)
    check_ssd_handler = CommandHandler('check_ssd_2tb', status_ssd_2tb)
    remount_ssd_handler = CommandHandler('remount_ssd_2tb', remount_ssd_2tb)

    application.add_handler(start_handler)
    application.add_handler(status_handler)
    application.add_handler(help_handler)
    application.add_handler(check_ssd_handler)
    application.add_handler(remount_ssd_handler)

    application.run_polling()
