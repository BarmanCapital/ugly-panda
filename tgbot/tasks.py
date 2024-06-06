# Create your tasks here

from celery import shared_task

import asyncio

from aiogram import Bot
from tgbot import tgbot_api
from tgbot.activity import activity_withdraw
from tgbot.models import MeUser
from uglypanda.settings import TG_BOT_TOKEN
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


bot = Bot(TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

@shared_task
def tg_withdraw(user_id):
    print("[tg_withdraw] user_id:", user_id)
    user = MeUser.objects.get(user_id=user_id)
    text = asyncio.run(activity_withdraw(user))
    tgbot_api.send_message(user_id, text)


@shared_task
def tg_send_message(user_id, text):
    asyncio.run(bot.send_message(user_id, text))


@shared_task
def xsum(numbers):  # sample
    return sum(numbers)
