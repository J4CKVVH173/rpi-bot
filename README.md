# RPI Server Monitor

## Описание

Бот для Telegram, который предоставляет информацию о статусе системы, включая температуру процессора, загрузку CPU и RAM.

## Требования

* Python 3.13
* Установка зависимостей из requirements.txt
* Наличие команды vcgencmd (для получения температуры процессора)
* Файл token.txt с токеном бота

## Установка

* Установите зависимости: pip install -r requirements.txt
* Создайте файл token.txt и введите токен бота
* Создать файл users.txt и ввести туда id пользователей telegram которым будет дан доступ к системе. Разделять пробелом
* Запустите бота: python bot.py

## Описание работы

Бот отображает приветственное сообщение при запуске, список доступных команд и статус системы, включая температуру процессора, загрузку CPU и RAM.
Примечания
Бот использует поллинг для получения обновлений от Telegram API. Для использования вебHOOK'ов необходимо изменить код и настроить веб-сервер.
Бот требует наличия файла token.txt с токеном бота. Токен можно получить в настройках бота в Telegram.
