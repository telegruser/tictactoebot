from urllib.parse import urljoin

# from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import Update
from flask import request, Flask

from bot_types import User
from rooms import rooms

import logging
import os

from aiogram import Bot, Dispatcher, executor, types
# from aiogram.utils.executor import start_webhook

# import aiohttp
# from aiohttp import web
# from aiogram import Bot, Dispatcher, types
# from aiogram.utils import context
# from aiogram.dispatcher.webhook import get_new_configured_app
# from lxml import etree


API_TOKEN = os.environ.get('API_TOKEN')
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
# WEBHOOK_PATH = '/webhook/' + API_TOKEN
WEBHOOK_URL = WEBHOOK_HOST + API_TOKEN
# WEBAPP_HOST = os.environ.get('WEBAPP_HOST')
# WEBAPP_PORT = int(os.environ.get('WEBAPP_PORT'))
LOCAL_MODE = bool(int(os.environ.get('LOCAL_MODE', '0')))
CONNECTION_TYPE = 'polling' if LOCAL_MODE else 'webhook'
PROXY = os.environ.get('PROXY', 'socks5://127.0.0.1:9150')  # Tor proxy
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, **dict(proxy=PROXY) if LOCAL_MODE else {})
User.bot = bot
dp = Dispatcher(bot)
# dp.middleware.setup(LoggingMiddleware())
updates = {}
app = None


if CONNECTION_TYPE == 'webhook':
    app = Flask(__name__) if CONNECTION_TYPE == 'webhook' else None
    app.logger.disabled = True


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
    # await dp.storage.close()
    # await dp.storage.wait_closed()
    logging.warning('Завершено')


if app is not None:
    @app.route('/' + API_TOKEN, methods=['POST'])
    async def get_message():
        update = Update.to_object(request.stream.read().decode("utf-8"))
        global updates
        if update.update_id not in updates:
            updates[update.update_id] = update
            await dp.process_update(update)
        return "OK", 200


if __name__ == '__main__':
    logging.info('Запуск приложения..')
    if CONNECTION_TYPE == 'polling':
        logging.info('Вариант подключения: polling.')
        executor.start_polling(dp, skip_updates=True)
    elif CONNECTION_TYPE == 'webhook':
        logging.info('Вариант подключения: webhook.')
        # app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL)
        # app.on_startup.append(on_startup)
        # dp.loop.set_task_factory(context.task_factory)
        # web.run_app(app, host='0.0.0.0', port=os.getenv('PORT'))
        # start_webhook(
        #     dispatcher=dp,
        #     webhook_path=WEBHOOK_PATH,
        #     on_startup=on_startup,
        #     on_shutdown=on_shutdown,
        #     skip_updates=True,
        #     host=WEBAPP_HOST,
        #     port=WEBAPP_PORT,)
        app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    await bot.send_message(ADMIN_ID, 'Приложение запущено')
