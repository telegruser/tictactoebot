from bot_types import User
from rooms import rooms

import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook


API_TOKEN = os.environ.get('API_TOKEN')
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PATH = os.environ.get('WEBHOOK_PATH')
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = os.environ.get('WEBAPP_HOST')
WEBAPP_PORT = int(os.environ.get('WEBAPP_PORT'))
LOCAL_MODE = bool(int(os.environ.get('LOCAL_MODE', '0')))
CONNECTION_TYPE = 'polling' if LOCAL_MODE else 'webhook'
PROXY = os.environ.get('PROXY', 'socks5://127.0.0.1:9150')  # Tor proxy

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, **dict(proxy=PROXY) if LOCAL_MODE else {})
User.bot = bot
dp = Dispatcher(bot)


async def process_update(user, message, callback_data=None):
    user.check_state(message, callback_data)
    await rooms(user)


@dp.message_handler()
async def handle_message(message: types.Message):
    print('handle message')
    user = User.identification(message.from_user.id)
    if message.message_id != user.control_message_id:
        await bot.delete_message(user.account_id, message.message_id)
    await process_update(user, message)


@dp.callback_query_handler()
async def callback_handler(messages: types.CallbackQuery):
    print('handle callback query')
    user = User.identification(messages.from_user.id)

    await process_update(user, messages.message, messages.data)


async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown():
    logging.warning('Завершение приложения..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning('Завершено')


if __name__ == '__main__':
    if CONNECTION_TYPE == 'polling':
        executor.start_polling(dp, skip_updates=True)
    elif CONNECTION_TYPE == 'webhook':
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,)
