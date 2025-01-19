import subprocess

from telegram import Update
from telegram.ext import ContextTypes


def is_jellyfin_running() -> bool:
    """Check if the Jellyfin service is running."""
    try:
        subprocess.run(['systemctl', 'is-active', '--quiet', 'jellyfin'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


async def check_jellyfin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the current status of the Jellyfin service."""
    if is_jellyfin_running():
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
