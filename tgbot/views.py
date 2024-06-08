import json
import urllib.parse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.http import HttpResponse
from django.http import JsonResponse

from tgbot.activity import activity_lottery, activity_withdraw_qualify
from tgbot.models import MeUser
from tgbot.tasks import tg_withdraw
from tgbot.utils import get_user_from_id

from aiogram import Bot
from uglypanda.settings import TG_BOT_TOKEN
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


bot = Bot(TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def get_user_id_from_request(request):
    """
        "id": 128129955,
        "first_name": "tbag",
        "last_name": "",
        "username": "tbag127",
        "language_code": "en",
        "allows_write_to_pm": true
    """
    data = json.loads(request.body)  # user_id or init_data
    user_id = data.get('user_id')
    if user_id:
        return user_id
    
    init_data = data.get('init_data')
    print("[get_user_from_request] init_data:", init_data)
    user_json = parse_init_data(init_data)
    return user_json["id"]


# Create your views here.

def parse_init_data(init_data: str):
    """
    解析telegram MiniApp的initData数据

    user=%7B%22id%22%3A128129955%2C%22first_name%22%3A%22tbag%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22tbag127%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%7D
    &chat_instance=8282237084861241898&chat_type=private&auth_date=1716791273
    &hash=290b118af296f30ac725c0af2d42aa8da45fbcc8302f1855a2c1f999bde1f7bb
    """
    # param_list = init_data.split('&')
    data_check = init_data  # param_list[0]
    print("[parse_init_data] data_check:", data_check)

    # 对整个初始化数据进行URL解码
    decoded_data = urllib.parse.unquote(data_check)
    print("[parse_init_data] decoded_data:", decoded_data)

    # 分割各个参数，这里假设参数以 "&" 符号分隔
    param_pairs = decoded_data.split('&')  # '\n'

    # 创建字典来存储键值对
    data_dict = {}
    for pair in param_pairs:
        # 分割每一对键值
        if '=' in pair:
            key, value = pair.split('=', 1)
            if key == "user":
                # 如果键是"user"，它的值是一个嵌套的JSON字符串，因此需要进行额外的解析
                value = json.loads(value.replace('\n', '\\n'))  # 替换换行符，以确保JSON格式正确
            data_dict[key] = value

    # 将字典转换为JSON格式的字符串
    json_output = json.dumps(data_dict, indent=4)
    print("[parse_init_data] json_output:", json_output)
    return data_dict["user"]


@csrf_exempt
def get_user_info(request):
    user_id = get_user_id_from_request(request)
    user: MeUser = get_user_from_id(user_id)
    points = user.points
    tons = "%.4f" % user.tons
    return JsonResponse({'status': 'success', 'username': user.username, 'points': points, "tons": tons})


@csrf_exempt
def lottery(request):
    user_id = get_user_id_from_request(request)
    user: MeUser = get_user_from_id(user_id)
    text = activity_lottery(user)
    user: MeUser = get_user_from_id(user_id)  # 抽奖后有变化
    points = user.points
    tons = "%.4f" % user.tons
    return JsonResponse({'status': 'success', 'text': text, 'points': points, "tons": tons})


@csrf_exempt
def withdraw(request):
    user_id = get_user_id_from_request(request)
    user: MeUser = get_user_from_id(user_id)

    qualify, text = activity_withdraw_qualify(user)
    if qualify:
        print("[withdraw] user_id:", user_id)
        tg_withdraw.delay(user_id)

    return JsonResponse({'status': 'success', 'text': text})


@csrf_exempt
def miniapp(request):
    template = loader.get_template("miniapp.html")
    context = { "param": 0, }
    return HttpResponse(template.render(context, request))

