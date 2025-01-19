"""Функции для обработки простых входных команд присущих боту."""
from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting message when the bot starts."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Привет! Я ваш бот помощник.", parse_mode="HTML"
    )


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
        "🔹 /files - Файла сохраненные в хранилище\n"
        "🔹 /file - Получить файл по id\n"
        "🔹 /delete_file - Удалить файл по id\n"
        "🔹 /clear - Очистить хранилище\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode="HTML")
