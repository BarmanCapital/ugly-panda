import asyncio, time
from asgiref.sync import sync_to_async
import pytz
from telegram import Bot
from tgbot.utils import get_daily_sentence
from uglypanda.settings import TG_BOT_TOKEN, TG_WEB3_CHANNEL_ID, TG_WEB3_GROUP_ID

MSG_IN_CHANNEL = """
日期：%s

句子：%s

译文：%s

视频讲解：%s
"""

async def send_sentence(bot):
    """
    每天晚上0点，把句子发送到「Web3英语每日一句订阅号」频道，并且转发到「Web3英语每日一句」社群
    """
    # print("I'am function <send_sentence>.")

    sentence = await sync_to_async(get_daily_sentence)()
    send_time_formatted = sentence.send_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日')
    text = MSG_IN_CHANNEL % (send_time_formatted, sentence.text_eng, sentence.text_chs, sentence.youtube_url)
    
    message = await bot.send_message(chat_id=TG_WEB3_CHANNEL_ID, text=text)
    await bot.forward_message(chat_id=TG_WEB3_GROUP_ID, from_chat_id=TG_WEB3_CHANNEL_ID, message_id=message.message_id)

def run(*args):
    start_time = time.time()  #开始计时

    bot = Bot(TG_BOT_TOKEN)
    asyncio.run(send_sentence(bot))

    end_time = time.time()  #结束计时
    duration = end_time - start_time  #计算运行时间
    print(f'运行时间是 {round(duration, 1)} 秒')
