import os
import datetime
import sqlite3
from uuid import uuid4

from telegram import Update
from telegram.ext import ContextTypes

from lib.stickers import SAD_GOSLING

from constants import CONTENT_DB_NAME, STORAGE


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция для сохранения информации в хранилище."""

    def save_message_to_file(name, payload, db):
        """Save file to db and to disc."""
        file_name = str(uuid4())
        with open(os.path.join(STORAGE, file_name), 'w') as f:
            f.write(payload)

        creation = str(datetime.datetime.now())

        cursor = db.cursor()

        cursor.execute(
            'INSERT INTO Content (name, unique_name, creation, is_file) VALUES (?, ?, ?, ?)',
            (name, file_name, creation, False),
        )
        db.commit()

    async def save_file(update: Update, db):
        file = await update.message.document.get_file()
        unique_name = str(uuid4())
        file_name = update.message.text if update.message.text else update.message.document.file_name
        await file.download_to_drive(
            custom_path=os.path.join(STORAGE, unique_name),
        )
        cursor = db.cursor()

        cursor.execute(
            'INSERT INTO Content (name, unique_name, creation, is_file) VALUES (?, ?, ?, ?)',
            (file_name, unique_name, str(datetime.datetime.now()), True),
        )
        db.commit()

    if update.message.document:
        with sqlite3.connect(CONTENT_DB_NAME) as db:
            await save_file(update, db)

    else:
        file_name, payload = update.message.text.split(' ', 1)

        if not os.path.exists(STORAGE):
            os.makedirs(STORAGE)

        with sqlite3.connect(CONTENT_DB_NAME) as db:
            try:
                save_message_to_file(file_name, payload, db)
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
    """
    Get file by index.

    Format: /file <index>
    """
    try:
        db_id = update.message.text.split(' ')[1]
    except IndexError:
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=SAD_GOSLING)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text='🔴 Неверный запрос.\n Нужно - /file <index>.'
        )
        return

    with sqlite3.connect(CONTENT_DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f'SELECT name, unique_name, is_file FROM Content WHERE id = {db_id}')
        try:
            name, unique_name, is_file = cursor.fetchall()[0]
        except IndexError:
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=SAD_GOSLING)
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text='🔴 Не найден файл с подходящим индексом'
            )
            return
        # if it was a real file - return it as a file
        if is_file:
            with open(os.path.join(STORAGE, unique_name), 'rb') as f:
                await context.bot.send_document(update.effective_chat.id, f, filename=name)
        # else return it as a string
        else:
            with open(os.path.join(STORAGE, unique_name), 'r') as f:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f.read())


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
            # don't care if file doesn't exist on disk
            pass

    await context.bot.send_message(chat_id=update.effective_chat.id, text='🟢 Хранилище очищено')


async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Метод удаляет файл по id."""
    try:
        file_id = update.message.text.split(' ')[1]
    except IndexError:
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=SAD_GOSLING)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text='🔴 Неверный запрос.\n Нужно - /delete_file <index>.'
        )
        return

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
