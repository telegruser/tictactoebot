from bot_types import User
from rooms import rooms

import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook
from aiogram.contrib.middlewares.logging import LoggingMiddleware


API_TOKEN = os.environ.get('API_TOKEN')
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', '')
WEBHOOK_PATH = '/' + API_TOKEN
WEBHOOK_URL = WEBHOOK_HOST + API_TOKEN
LOCAL_MODE = bool(int(os.environ.get('LOCAL_MODE', '0')))
CONNECTION_TYPE = os.environ.get('CONNECTION_TYPE', None)
if not CONNECTION_TYPE:
    CONNECTION_TYPE = 'polling' if LOCAL_MODE else 'webhook'
PROXY = os.environ.get('PROXY', 'socks5://127.0.0.1:9150')  # Tor proxy

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, proxy=PROXY) if LOCAL_MODE else Bot(API_TOKEN)
User.bot = bot
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


async def process_update(user, message, callback_data=None):
    user.check_state(message, callback_data)
    await rooms(user)


@dp.message_handler()
async def handle_message(message: types.Message):
    logging.info(f'Получено сообщение от {message.from_user.id}')
    user = User.identification(message.from_user.id)
    if message.message_id != user.control_message_id:
        await bot.delete_message(user.account_id, message.message_id)
    await process_update(user, message)


@dp.callback_query_handler()
async def callback_handler(messages: types.CallbackQuery):
    logging.info(f'Полученн callback от {messages.from_user.id}')
    user = User.identification(messages.from_user.id)

    await process_update(user, messages.message, messages.data)


async def on_startup(d):
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(d):
    logging.warning('Завершение приложения..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning('Завершено')


if __name__ == '__main__':
    logging.info('Запуск приложения..')
    if CONNECTION_TYPE == 'polling':
        logging.info('Вариант подключения: polling.')
        executor.start_polling(dp, skip_updates=True)
    elif CONNECTION_TYPE == 'webhook':
        logging.info('Вариант подключения: webhook.')
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5000)))
