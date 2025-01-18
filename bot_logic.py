import logging
import datetime
import psutil
import subprocess
import os
import re
import sqlite3
from uuid import uuid4
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT, ATTACHMENT

from constant import CONTENT_DB_NAME, STORAGE

DIR_PATH = os.path.dirname(__file__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open(os.path.join(DIR_PATH, 'token.txt'), 'r') as token:
    TOKEN = token.read().strip()


def is_jellifyn_running() -> bool:
    """Check if the Jellyfin service is running."""
    try:
        subprocess.run(['systemctl', 'is-active', '--quiet', 'jellyfin'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


async def check_jellyfin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the current status of the Jellyfin service."""
    if is_jellifyn_running():
        message = "🟢 <b>Jellyfin запущен</b>"
    else:
        message = "🔴 <b>Jellyfin остановлен</b>"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode="HTML")


async def get_jellyfin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve the last 10 lines of the Jellyfin service logs."""
    logs = subprocess.check_output(['journalctl', '-u', 'jellyfin', '--lines', '10'], stderr=subprocess.STDOUT)
    message = f"<b>Логи Jellyfin:</b>\n<pre>{logs.decode('utf-8')}</pre>"
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"�� Ошибка получения логов Jellyfin: {e}"
        )


async def get_jellyfin_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve the last 10 error entries from the Jellyfin logs."""
    logs = subprocess.check_output(
        ['journalctl', '-u', 'jellyfin', '--lines', '10', '--grep', 'error'], stderr=subprocess.STDOUT
    )
    message = f"<b>Ошибки Jellyfin:</b>\n<pre>{logs.decode('utf-8')}</pre>"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


async def restart_jellyfin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the Jellyfin service."""
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'jellyfin'], check=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="🔄 <b>Jellyfin перезапущен</b>", parse_mode='HTML'
        )
    except subprocess.CalledProcessError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"❌ Ошибка перезапуска Jellyfin: {e}", parse_mode='HTML'
        )


async def top_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve the top 20 CPU-consuming processes."""
    top_output = (
        subprocess.check_output(['top', '-n', '1', '-o', '-%CPU', '-b'], stderr=subprocess.STDOUT)
        .decode('utf-8')
        .split('\n')
    )
    message = f"<b>Топ 20 процессов по использованию CPU:</b>\n<pre>{'\n'.join(top_output[-20:])}</pre>"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting message when the bot starts."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Привет! Я ваш бот для мониторинга системы.", parse_mode="HTML"
    )


async def get_system_status():
    """Retrieve system status, including CPU temperature, voltage, CPU and RAM usage, and disk usage."""
    temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
    voltage_output = subprocess.check_output(["vcgencmd", "measure_volts"]).decode("utf-8")
    temperature = temp_output.split('=')[1].strip()
    voltage = voltage_output.split('=')[1].strip()

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    ram_usage = memory.percent

    allowed_mount_points = {"/", "/boot/firmware", "/mnt/SSD4TB/D"}
    allowed_devices = re.compile(r"mmcblk0p[12]|sd[a-z]+\d+")

    disk_info = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            if partition.mountpoint in allowed_mount_points or allowed_devices.match(partition.device.split("/")[-1]):
                usage = psutil.disk_usage(partition.mountpoint)
                total_size = usage.total / (1024**3)
                disk_info.append(
                    f"  🔹 <b>Диск {partition.device}</b> ({partition.mountpoint}):"
                    f"\n  📊 <b>{usage.percent}%</b> использовано"
                    f"\n  💾 <b>{usage.free / (1024 ** 3):.2f} GB</b> свободно из <b>{total_size:.2f} GB</b>\n"
                )
        except PermissionError:
            continue

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
    """Send system status to the user."""
    text = await get_system_status()
    await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide a list of available commands."""
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "🔹 /start - Начать работу с ботом\n"
        "🔹 /help - Показать список доступных команд\n"
        "🔹 /status - Показать статус системы (температура, загрузка ЦП и ОЗУ)\n"
        "🔹 /check_ssd_2tb - Проверяет - доступен ли SSD для чтения\n"
        "🔹 /remount_ssd_2tb - Заново перемонтирует SSD\n"
        "🔹 /check_jellyfin_status - Статус jellyfin\n"
        "🔹 /get_jellyfin_logs - Лог jellyfin\n"
        "🔹 /restart_jellyfin - Перезапуск jellyfin\n"
        "🔹 /get_jellyfin_errors - Лог ошибок jellyfin\n"
        "🔹 /top_statistics - Статистика 20 самых нагруженных процессов\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode="HTML")


async def status_ssd_2tb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if the 2TB SSD is available for reading."""
    directory = "/mnt/SSD_4TB/D"
    try:
        os.listdir(directory)
        message = "🟢 <b>Диск доступен для чтения</b>"
    except OSError as e:
        message = f"🔴 <b>Ошибка при чтении диска:</b> {str(e)}"
    finally:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


async def remount_ssd_2tb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remount the 2TB SSD."""
    try:
        result = subprocess.run(
            ['/bin/bash', '/home/andrey/scripts/check_mount.sh'], capture_output=True, text=True, check=True
        )
        message = f"🟢 <b>{result.stdout.strip()}</b>"
    except subprocess.CalledProcessError as e:
        message = f'🔴 <b>Ошибка при примонтировании SSD:</b> {str(e)}'
    finally:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция для сохранения информации в хранилище."""

    def save_to_file(name, content, db):
        file_name = str(uuid4())
        with open(os.path.join(STORAGE, file_name), 'w') as f:
            f.write(content)

        creation = str(datetime.datetime.now())

        cursor = db.cursor()

        cursor.execute(
            'INSERT INTO Content (name, unique_name, creation, is_file) VALUES (?, ?, ?, ?)',
            (name, file_name, creation, False),
        )
        db.commit()

    if update.message.document:
        file = await update.message.document.get_file()
        unique_name = str(uuid4())
        file_name = update.message.text if update.message.text else update.message.document.file_name
        await file.download_to_drive(
            custom_path=os.path.join(STORAGE, unique_name),
        )
        with sqlite3.connect(CONTENT_DB_NAME) as db:
            cursor = db.cursor()

            cursor.execute(
                'INSERT INTO Content (name, unique_name, creation, is_file) VALUES (?, ?, ?, ?)',
                (file_name, unique_name, str(datetime.datetime.now()), True),
            )
            db.commit()
    else:
        incoming_request = update.message.text.split(' ', 1)

        if not os.path.exists(STORAGE):
            os.makedirs(STORAGE)

        with sqlite3.connect(CONTENT_DB_NAME) as db:
            try:
                save_to_file(incoming_request[0], incoming_request[1], db)
            except IndexError:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='🔴 Не сохранено\n Нужно передать в виде: <Имя файла> <Контент>',
                )
                return

    await context.bot.send_message(chat_id=update.effective_chat.id, text='🟢 Файл записан в хранилище')


async def all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect(CONTENT_DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute('SELECT id, name, creation FROM Content')
        files = cursor.fetchall()
        # Добавляем строки таблицы
        message = "ID - Name - Creation Date\n"

        # Добавляем строки таблицы с выравниванием
        for file_id, name, creation in files:
            creation_date = datetime.datetime.strptime(creation, '%Y-%m-%d %H:%M:%S.%f')
            formatted_creation = creation_date.strftime('%Y-%m-%d %H:%M')
            message += f"{file_id} - {name} - {str(formatted_creation)}\n"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_id = update.message.text.split(' ')[1]
    with sqlite3.connect(CONTENT_DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f'SELECT name, unique_name, is_file FROM Content WHERE id = {db_id}')
        name, unique_name, is_file = cursor.fetchall()[0]
        if not is_file:
            with open(os.path.join(STORAGE, unique_name), 'r') as f:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f.read())
        else:
            with open(os.path.join(STORAGE, unique_name), 'rb') as f:
                await context.bot.send_document(update.effective_chat.id, f, filename=name)


async def clear_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Метод полностью очищает хранилище."""
    with sqlite3.connect(CONTENT_DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute('SELECT unique_name FROM Content')
        files = cursor.fetchall()
        cursor.execute('DELETE FROM Content')
        db.commit()

        try:
            for file_name in files:
                os.remove(os.path.join(STORAGE, file_name))
        except Exception:
            pass

    await context.bot.send_message(chat_id=update.effective_chat.id, text='🟢 Хранилище очищено')


async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Метод удаляет файл по id."""
    file_id = update.message.text.split(' ')[1]
    with sqlite3.connect(CONTENT_DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f'SELECT unique_name FROM Content WHERE id = {file_id}')
        file_name = cursor.fetchall()[0][0]
        cursor.execute(f'DELETE FROM Content WHERE id = {file_id}')
        db.commit()

        try:
            os.remove(os.path.join(STORAGE, file_name))
        except Exception:
            pass

    await context.bot.send_message(chat_id=update.effective_chat.id, text='🟢 Файл удален')


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
    files_handler = CommandHandler('files', all_files)
    clear_handler = CommandHandler('clear', clear_storage)
    get_file_handler = CommandHandler('file', get_file, has_args=True)
    delete_file_handler = CommandHandler('delete_file', delete_file, has_args=True)

    save_handler = MessageHandler(TEXT, save)
    attach_handler = MessageHandler(ATTACHMENT, save)

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
    application.add_handler(get_file_handler)
    application.add_handler(files_handler)
    application.add_handler(clear_handler)
    application.add_handler(delete_file_handler)

    application.add_handler(save_handler)
    application.add_handler(attach_handler)

    application.run_polling()
