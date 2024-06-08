import json, re, requests, pytz
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from tgbot.consts import MSG_COMPLETE_STUDY, MSG_COMPLETE_STUDY_AUDIO, MSG_COMPLETE_STUDY_TEXT
from tgbot.models import MeUser, StudySentence, UserStudyRecord
from uglypanda.settings import SSOUND_URL, TG_BOT_TOKEN, TG_FILE_URL_PREFIX


POINTS_FOR_TYPE = {UserStudyRecord.TYPE_CHOICES_TEXT: 1, UserStudyRecord.TYPE_CHOICES_AUDIO: 3, }  # 送积分


## 纯工具函数

def count_common_words(sentence1, sentence2):
    # 去掉标点符号，只保留字符集合 [a-zA-Z0-9_]
    sentence1 = re.sub(r'[^\w\s]', '', sentence1)
    sentence2 = re.sub(r'[^\w\s]', '', sentence2)

    # 将句子转换为单词集合，将字母转换为小写形式
    words_in_sentence1 = set(sentence1.lower().split())
    words_in_sentence2 = set(sentence2.lower().split())

    # 返回两个集合的交集的元素数量
    return len(words_in_sentence1.intersection(words_in_sentence2))

## 数据库相关

def create_user(user_id, username):
    print("[create_user]", user_id, username)

    me_user, _ = MeUser.objects.get_or_create(user_id=user_id)
    me_user.username = username
    me_user.save()
    return me_user

def get_user_from_id(user_id):
    me_user = MeUser.objects.get(user_id=user_id)
    return me_user

def get_user_from_name(username):
    me_user = MeUser.objects.get(username=username)
    return me_user

def get_bot_users():
    """
    获取所有bot用户
    """
    users = MeUser.objects.all()  # filter(~Q(refer_user_id=""))
    return [user for user in users]

def get_no_study_users():
    """
    获取本周还没有打卡的bot用户
    """
    now = timezone.now().astimezone(pytz.timezone('Asia/Shanghai'))  # 用北京时区，不然周一0点会出错
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    print("[get_no_study_users] monday:", monday)
    
    no_study_users = []
    for user in MeUser.objects.all():  # filter(~Q(refer_user_id="")):
        if not UserStudyRecord.objects.filter(user=user, time__gte=monday).exists():
            no_study_users.append(user)
    
    print("[get_no_study_users] no_study_users:", no_study_users)
    return no_study_users

def get_daily_sentence(delta_days=0):
    today = (timezone.localtime() + timedelta(days=delta_days)).date()
    daily_sentence = StudySentence.objects.filter(send_time__date=today).first()
    return daily_sentence

def has_sentence_study_record(user_id, sentence, type):
    return UserStudyRecord.objects.filter(user__user_id=user_id, sentence=sentence, type=type).exists()

def has_any_study_record(user_id):
    return UserStudyRecord.objects.filter(user__user_id=user_id).exists()

def save_study_record(user_id, sentence, type, score='{"overall": 100}'):
    points = POINTS_FOR_TYPE[type]
    user = get_user_from_id(user_id)
    record, _ = UserStudyRecord.objects.get_or_create(user=user, sentence=sentence, type=type)
    record.time = timezone.now()
    record.score = score
    record.points = points
    record.save()

    # 确保record记录成功之后再将积分保存到 MeUser
    user.points += points
    user.save()
    
    if type == UserStudyRecord.TYPE_CHOICES_TEXT:
        text = MSG_COMPLETE_STUDY_TEXT % (user.username, points)
    else:
        text = MSG_COMPLETE_STUDY_AUDIO % (user.username, points)
    return text

## 外部（请求）服务相关

def ssound_score(audio_url, text_eng):
    full_audio_url = TG_FILE_URL_PREFIX + audio_url

    form_data = {
        "bucket": "TG",
        "key": full_audio_url,
        "refText": text_eng
    }
    resp = requests.post(SSOUND_URL, json=form_data)
    if resp.status_code != 200:
        print("[send_message] Error Response:", resp.status_code, resp.text)
        return None
    
    print("resp.content:", resp.content)
    content = json.loads(resp.content)
    score = {"overall": content.get("overall", 0),
             "integrity": content.get("integrity", 0),
             "accuracy": content.get("accuracy", 0),
             "fluency": content.get("fluency", 0)}
    return score

    
## 测试函数

if __name__ == "__main__":
    pass
