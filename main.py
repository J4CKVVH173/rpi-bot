from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.ext.filters import TEXT, ATTACHMENT

from app.entrypoint import help, start
from app.jellyfin import check_jellyfin_status, get_jellyfin_errors, get_jellyfin_logs, restart_jellyfin
from app.rpi import remount_ssd_2tb, status, status_ssd_2tb, top_statistics
from app.storage import all_files, clear_storage, get_file, delete_file, save
from guard.guarded_handlers import GuardedCommandHandler, GuardedMessageHandler

from config import TOKEN


def run():
    """Функция для запуска бота."""
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    status_handler = GuardedCommandHandler('status', status)
    help_handler = GuardedCommandHandler('help', help)
    check_ssd_handler = GuardedCommandHandler('check_ssd_2tb', status_ssd_2tb)
    remount_ssd_handler = GuardedCommandHandler('remount_ssd_2tb', remount_ssd_2tb)
    check_jellyfin_status_handler = GuardedCommandHandler('check_jellyfin_status', check_jellyfin_status)
    get_jellyfin_logs_handler = GuardedCommandHandler('get_jellyfin_logs', get_jellyfin_logs)
    restart_jellyfin_handler = GuardedCommandHandler('restart_jellyfin', restart_jellyfin)
    get_jellyfin_errors_handler = GuardedCommandHandler('get_jellyfin_errors', get_jellyfin_errors)
    top_statistics_handler = GuardedCommandHandler('top_statistics', top_statistics)
    files_handler = GuardedCommandHandler('files', all_files)
    clear_handler = GuardedCommandHandler('clear', clear_storage)
    get_file_handler = GuardedCommandHandler('file', get_file, has_args=True)
    delete_file_handler = GuardedCommandHandler('delete_file', delete_file, has_args=True)

    save_handler = GuardedMessageHandler(TEXT, save)
    attach_handler = GuardedMessageHandler(ATTACHMENT, save)

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


if __name__ == "__main__":
    run()
