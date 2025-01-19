from telegram.ext import CommandHandler, MessageHandler, ContextTypes

from config import ALLOWED_USERS
from lib.stickers import LOOKING


class GuardedCommandHandler(CommandHandler):
    """Protected command handler."""

    async def handle_update(self, update, application, check_result, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id not in ALLOWED_USERS:
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=LOOKING)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Go away.')
            return
        return await super().handle_update(update, application, check_result, context)


class GuardedMessageHandler(MessageHandler):
    """Protected command handler."""

    async def handle_update(self, update, application, check_result, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id not in ALLOWED_USERS:
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=LOOKING)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Go away.')
            return
        return await super().handle_update(update, application, check_result, context)
