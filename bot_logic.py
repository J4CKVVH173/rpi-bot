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


def is_jellifyn_running() -> bool:
    try:
        # Проверка статуса процесса через systemctl
        subprocess.run(['systemctl', 'is-active', '--quiet', 'jellyfin'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


async def check_jellyfin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_jellifyn_running():
        message = "Jellyfin запущен"
    else:
        message = "Jellyfin остановлен"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def get_jellyfin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получение последних 15 строк логов из systemd
    logs = subprocess.check_output(['journalctl', '-u', 'jellyfin', '--lines', '15'], stderr=subprocess.STDOUT)
    message = f"Логи:\n {logs.decode('utf-8')}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def get_jellyfin_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем последние 15 ошибок (предполагаем, что они содержат слово "error")
    logs = subprocess.check_output(
        ['journalctl', '-u', 'jellyfin', '--lines', '15', '--grep', 'error'], stderr=subprocess.STDOUT
    )
    message = f"Логи:\n {logs.decode('utf-8')}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def restart_jellyfin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Перезапуск сервиса Jellyfin
        subprocess.run(['sudo', 'systemctl', 'restart', 'jellyfin'], check=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jellyfin перезапущен")
    except subprocess.CalledProcessError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка перезапуска Jellyfin: {e}")


async def top_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_output = subprocess.check_output(['top', '-n', '1', '-o', '-%CPU', '-b'], stderr=subprocess.STDOUT).decode(
        'utf-8'
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<pre>{top_output}</pre>", parse_mode='HTML')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def get_system_status():
    # Получение температуры и напряжения
    temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
    voltage_output = subprocess.check_output(["vcgencmd", "measure_volts"]).decode("utf-8")
    temperature = temp_output.split('=')[1].strip()
    voltage = voltage_output.split('=')[1].strip()

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
            if partition.mountpoint in allowed_mount_points or allowed_devices.match(partition.device.split("/")[-1]):
                usage = psutil.disk_usage(partition.mountpoint)
                total_size = usage.total / (1024**3)  # В гигабайтах
                disk_info.append(
                    f"  🔹 <b>Диск {partition.device}</b> ({partition.mountpoint}):"
                    f"\n  📊 <b>{usage.percent}%</b> использовано"
                    f"\n  💾 <b>{usage.free / (1024 ** 3):.2f} GB</b> свободно из <b>{total_size:.2f} GB</b>\n"
                )
        except PermissionError:
            continue

    # Формирование итогового статуса с форматированием
    status = (
        f"🖥️ <b>Статус системы:</b>\n\n"
        f"🌡️ <b>Температура процессора:</b> {temperature}\n"
        f"⚡️ <b>Напряжение:</b> {voltage}\n"
        f"⚙️ <b>Загрузка CPU:</b> {cpu_usage}%\n"
        f"🧠 <b>Загрузка RAM:</b> {ram_usage}%\n\n"
        f"💾 <b>Информация о дисках:</b>\n\n"
    )

    if disk_info:
        status += "\n".join(disk_info)
    else:
        status += "🔴 Нет данных о дисках"

    return status


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await get_system_status()
    await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="html", text=text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список доступных команд\n"
        "/status - Показать статус системы (температура, загрузка ЦП и ОЗУ)\n"
        "/check_ssd_2tb - Проверяет - доступен ли SSD для чтения\n"
        "/remount_ssd_2tb - Заново перемонтирует SSD\n"
        "/check_jellyfin_status - Статус jellyfin\n"
        "/get_jellyfin_logs - Лог jellyfin\n"
        "/restart_jellyfin - Перезапуск jellyfin\n"
        "/get_jellyfin_errors - Лог ошибок jellyfin\n"
        "/top_statistics - Статистика процессов\n"
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
    check_jellyfin_status_handler = CommandHandler('check_jellyfin_status', check_jellyfin_status)
    get_jellyfin_logs_handler = CommandHandler('get_jellyfin_logs', get_jellyfin_logs)
    restart_jellyfin_handler = CommandHandler('restart_jellyfin', restart_jellyfin)
    get_jellyfin_errors_handler = CommandHandler('get_jellyfin_errors', get_jellyfin_errors)
    top_statistics_handler = CommandHandler('top_statistics', top_statistics)

    application.add_handler(start_handler)
    application.add_handler(status_handler)
    application.add_handler(help_handler)
    application.add_handler(check_ssd_handler)
    application.add_handler(remount_ssd_handler)
    application.add_handler(check_jellyfin_status_handler)
    application.add_handler(get_jellyfin_logs_handler)
    application.add_handler(restart_jellyfin_handler)
    application.add_handler(get_jellyfin_errors_handler)
    application.add_handler(top_statistics_handler)

    application.run_polling()
