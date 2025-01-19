import psutil
import re
import subprocess
import os

from telegram import Update
from telegram.ext import ContextTypes


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


async def top_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve the top 20 CPU-consuming processes."""
    top_output = (
        subprocess.check_output(['top', '-n', '1', '-o', '-%CPU', '-b'], stderr=subprocess.STDOUT)
        .decode('utf-8')
        .split('\n')
    )
    message = f"<b>Топ 20 процессов по использованию CPU:</b>\n<pre>{'\n'.join(top_output[-20:])}</pre>"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')
