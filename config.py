# нужен импорт обязательно тчобы проинициализировать БД
import init_db  # noqa
import logging
import os

DIR_PATH = os.path.dirname(__file__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open(os.path.join(DIR_PATH, 'token.txt'), 'r') as token:
    TOKEN = token.read().strip()

with open(os.path.join(DIR_PATH, 'users.txt'), 'r') as token:
    ALLOWED_USERS = list(map(int, token.read().strip().split(' ')))
