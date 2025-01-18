import sqlite3

from constant import CONTENT_DB_NAME

# Устанавливаем соединение с базой данных
connection = sqlite3.connect(CONTENT_DB_NAME)
cursor = connection.cursor()

# Создаем таблицу Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS Content (
id INTEGER PRIMARY KEY,
name TEXT NOT NULL,
unique_name TEXT NOT NULL,
creation TEXT NOT NULL,
is_file INTEGER NOT NULL
)
''')

cursor.execute('CREATE INDEX idx_unique_name ON Content (unique_name)')

# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()
