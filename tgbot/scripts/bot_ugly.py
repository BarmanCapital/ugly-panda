from io import BytesIO
import qrcode
import asyncio, datetime, sys, logging
import time
from asgiref.sync import sync_to_async

from telegram import constants
from tgbot.activity import MSG_WITHDRAW_WAIT, activity_withdraw_qualify

from tgbot.connector import get_connector
from tgbot.consts import COMMON_WORDS_COUNT, DEFAULT_SCORE, MSG_CMD_HELP, MSG_DAILY_STUDY, MSG_DEFAULT, MSG_HAS_RECORD, MSG_HISTORY_STUDY, MSG_LOTTERY, MSG_ORAL_SCORE_BAD, MSG_ORAL_SCORE_GOOD, MSG_SENTENCE_ERROR, MSG_WELCOME
from tgbot.tasks import tg_withdraw
from tgbot.ton_api import get_comment_message
from tgbot.utils import count_common_words, create_user, get_daily_sentence, has_sentence_study_record, save_study_record, ssound_score
from tgbot.models import UserStudyRecord
from uglypanda.settings import TG_BOT_TOKEN, WEB_APP_URL

import pytonconnect.exceptions
from pytoniq_core import Address
from pytonconnect import TonConnect

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import User, Message, CallbackQuery, BufferedInputFile, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


logger = logging.getLogger(__file__)

dp = Dispatcher()
bot = Bot(TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def get_user_info(message: Message):
    from_user = message.from_user
    user_id = from_user.id
    username = from_user.username if from_user.username else from_user.first_name
    return user_id, username


async def complete_study(chat_id, user_id, username, sentence, type, message: Message, score=DEFAULT_SCORE, in_group=True):
    """
    完成打卡学习
    """
    print("[complete_study]", chat_id, user_id, username)

    # 判断是否当日已有记录
    has_record = await sync_to_async(has_sentence_study_record)(user_id, sentence, type)
    if has_record:
        await message.answer(text=MSG_HAS_RECORD % username)
        return

    text = await sync_to_async(save_study_record)(user_id, sentence, type, score)
    await message.answer(text=text)


async def connect_wallet(message: Message, wallet_name: str):
    connector = get_connector(message.chat.id)

    wallets_list = connector.get_wallets()
    wallet = None

    for w in wallets_list:
        if w['name'] == wallet_name:
            wallet = w

    if wallet is None:
        raise Exception(f'不支持的未知钱包：{wallet_name}')

    generated_url = await connector.connect(wallet)

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='绑定', url=generated_url)

    img = qrcode.make(generated_url)
    stream = BytesIO()
    img.save(stream)
    file = BufferedInputFile(file=stream.getvalue(), filename='qrcode')

    await message.answer_photo(photo=file, caption='请在2分钟内绑定钱包', reply_markup=mk_b.as_markup())

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='解除绑定', callback_data='disconnect')

    for i in range(1, 150):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_str(is_bounceable=False)
                await message.answer(f'绑定成功：绑定的钱包地址是 <code>{wallet_address}</code>', reply_markup=mk_b.as_markup())
                logger.info(f'Connected with address: {wallet_address}')
            return

    await message.answer(f'已经超时，请重新绑定', reply_markup=mk_b.as_markup())


async def disconnect_wallet(message: Message):
    connector = get_connector(message.chat.id)
    await connector.restore_connection()
    await connector.disconnect()
    await message.answer('钱包解绑成功')

####

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    print(message)
    print("message.text:", message.text)
    user_id, username = await get_user_info(message)
    await sync_to_async(create_user)(user_id, username)
    
    webapp_url = WEB_APP_URL % user_id
    button1 = KeyboardButton(text="🔥抽奖", web_app=WebAppInfo(url=webapp_url))
    button2 = KeyboardButton(text="🎙️句子打卡")
    button3 = KeyboardButton(text="💸绑定钱包")
    button4 = KeyboardButton(text="📝往期句子")
    button_list = [[button1, button2], [button3, button4]]

    keyboard = types.ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)
    await message.answer(MSG_CMD_HELP, reply_markup=keyboard)


@dp.message(Command('transaction'))  # TODO: 测试发起交易
async def send_transaction(message: Message):
    connector = get_connector(message.chat.id)
    connected = await connector.restore_connection()
    if not connected:
        await message.answer('请先绑定钱包')
        return

    dest_addr = '0:d50ebc92e3d6ccbda1b2e2412421bc87ca744d01d0853f688a9b921f70c6b41e'

    transaction = {
        'valid_until': int(time.time() + 3600),
        'messages': [
            get_comment_message(
                destination_address=dest_addr, # '0:0000000000000000000000000000000000000000000000000000000000000000',
                amount=int(0.0001 * 10 ** 9),
                comment='hello Web3.'
            )
        ]
    }

    await message.answer(text='请在你的钱包App里面批准这笔交易')
    try:
        await asyncio.wait_for(connector.send_transaction(
            transaction=transaction
        ), 300)
    except asyncio.TimeoutError:
        await message.answer(text='已经超时，请重新操作')
    except pytonconnect.exceptions.UserRejectsError:
        await message.answer(text='你已经在钱包App拒绝这笔交易')
    except Exception as e:
        await message.answer(text=f'未知错误，请找管理员：{e}')

SUPPORTED_WALLETS = ["Wallet", "Tonkeeper", "MyTonWallet"]
@dp.message(Command('connect'))
async def command_connect_handler(message: Message):
    print(message)
    chat_id = message.chat.id
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()

    mk_b = InlineKeyboardBuilder()
    if connected:
        wallet_address = connector.account.address
        wallet_address = Address(wallet_address).to_str(is_bounceable=False)
        # mk_b.button(text='发送交易', callback_data='send_tr')
        mk_b.button(text='解除绑定', callback_data='disconnect')
        await message.answer(text=f'已经绑定，钱包地址是 <code>{wallet_address}</code>', reply_markup=mk_b.as_markup())

    else:
        wallets_list = TonConnect.get_wallets()
        for wallet in wallets_list:
            if wallet['name'] in SUPPORTED_WALLETS:
                mk_b.button(text=wallet['name'], callback_data=f'connect:{wallet["name"]}')
        mk_b.adjust(1, )
        await message.answer(text='选择你想绑定的钱包Dapps', reply_markup=mk_b.as_markup())


@dp.message(Command('help'))
async def command_help_handler(message: Message):
    print(message)
    await message.answer(text=MSG_CMD_HELP)


@dp.message(Command('daily'))
async def command_daily_handler(message: Message):
    print(message)
    await message.answer(text=MSG_DAILY_STUDY)


@dp.message(Command('lottery'))
async def command_help_handler(message: Message):
    print(message)
    # user_id, username = await get_user_info(message)
    # user = await sync_to_async(create_user)(user_id, username)
    # text = await sync_to_async(activity_lottery)(user)
    await message.answer(text=MSG_LOTTERY)


@dp.message(Command('withdraw'))
async def command_withdraw_handler(message: Message):
    print(message)
    user_id, username = await get_user_info(message)
    user = await sync_to_async(create_user)(user_id, username)
    
    qualify, text = await sync_to_async(activity_withdraw_qualify)(user)
    if qualify:
        tg_withdraw.delay(user_id)
        text = MSG_WITHDRAW_WAIT

    await message.answer(text=text)


@dp.message(~F.text.startswith('/'))
async def process_message_handler(message: Message):
    print(message)
    user_id, username = await get_user_info(message)
    await sync_to_async(create_user)(user_id, username)
    
    # 处理群消息
    if message.chat.type in ["group", "supergroup"]:
        await process_group_message(user_id, username, message)
        return

    # 处理菜单
    text = message.text
    if text == "📖帮助":
        await message.answer(text=MSG_CMD_HELP)
    elif text == "🎙️句子打卡":
        await message.answer(text=MSG_DAILY_STUDY)
    elif text == "📝往期句子":
        await message.answer(text=MSG_HISTORY_STUDY)
    elif text == "💸绑定钱包":
        await command_connect_handler(message)
    else:
        await message.answer(text=MSG_DEFAULT)


@dp.callback_query(lambda call: True)
async def main_callback_handler(call: CallbackQuery):
    await call.answer()
    message = call.message
    data = call.data
    if data == "start":
        await command_connect_handler(message)
    elif data == "send_tr":
        await send_transaction(message)
    elif data == 'disconnect':
        await disconnect_wallet(message)
    else:
        data = data.split(':')
        if data[0] == 'connect':
            await connect_wallet(message, data[1])

####

async def welcome_new_members(users: list[User], message: Message):
    user_list = ["@" + (user.username if user.username else user.first_name) for user in users]
    user_list_str = " ".join(user_list)
    sentence = await sync_to_async(get_daily_sentence)()
    text = MSG_WELCOME % (user_list_str, sentence.text_eng)
    print("[welcome_new_members]", text)
    await message.answer(text, parse_mode=constants.ParseMode.MARKDOWN_V2)


async def process_group_message(user_id, username, message: Message):
    print("[process_group_message] @", datetime.datetime.now())

    # 转发到群的消息（包括 tbag 转发的每日一句订阅号内容）不处理
    if message.forward_date or message.forward_from_chat:
        print("[process_group_message] message is forward_from_chat")
        return

    # 进群新用户
    if message.new_chat_members:
        await welcome_new_members(message.new_chat_members, message)
        return

    sentence = await sync_to_async(get_daily_sentence)()
    text_eng = sentence.text_eng

    text = message.text
    chat_id = message.chat.id
    if text:  # 处理文字消息
        if text == text_eng:
            await complete_study(chat_id, user_id, username, sentence, UserStudyRecord.TYPE_CHOICES_TEXT, message)
        elif count_common_words(text, text_eng) >= COMMON_WORDS_COUNT:
            text = MSG_SENTENCE_ERROR % (username, sentence.text_eng)
            await message.answer(text=text, parse_mode=constants.ParseMode.MARKDOWN_V2)            

    voice = message.voice
    if voice:  # 处理音频消息
        file_info = await bot.get_file(voice.file_id)
        print("audio URL:", file_info.file_path)
        
        # 口语打分>60才算完成打卡
        score = ssound_score(file_info.file_path, sentence.text_eng)
        if not score:
            print("[process_group_message] Error in ssound_score.")
            return
        
        if score["overall"] >= 60:
            text = MSG_ORAL_SCORE_GOOD % (score["integrity"], score["accuracy"], score["fluency"], score["overall"])
        else:
            text = MSG_ORAL_SCORE_BAD % (score["integrity"], score["accuracy"], score["fluency"], score["overall"])
        await message.answer(text=text)

        if score["overall"] >= 60:
            await complete_study(chat_id, user_id, username, sentence, UserStudyRecord.TYPE_CHOICES_AUDIO, message)


async def get_updates() -> None:
    await bot.delete_webhook(drop_pending_updates=True)  # skip_updates = True
    await dp.start_polling(bot)


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(get_updates())

