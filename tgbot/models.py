from decimal import Decimal
import json
from django.db import models
from pytoniq_core import Address


class MeUser(models.Model):
    """
    早安英文（TG）用户
    """
    REFER_USER_ID_NONE = "NO-ONE"

    user_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=200, default="")
    refer_user_id = models.CharField(max_length=50, default="", blank=True, verbose_name="邀请人")

    credits = models.TextField(default="", blank=True, verbose_name="积分（废弃）")

    ton_connect = models.TextField(default="", blank=True, verbose_name="TonConnect数据")
    points = models.IntegerField(default=0, verbose_name="竹子")
    tons = models.DecimalField(default=Decimal("0.0"), max_digits=20, decimal_places=10, verbose_name="TON币")
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s (%s)" % (self.username, self.user_id)
    
    def get_ton_connect(self):
        if self.ton_connect == "":
            return {}
        else:
            return json.loads(self.ton_connect)

    def set_ton_connect(self, key, value):
        tc_json = self.get_ton_connect()
        tc_json[key] = value
        self.ton_connect = json.dumps(tc_json)
        self.save()

    def remove_ton_connect(self, key):
        tc_json = self.get_ton_connect()
        tc_json.pop(key)
        self.ton_connect = json.dumps(tc_json)
        self.save()

    def get_ton_address(self):
        ton_connect_json = self.get_ton_connect()
        if not "connection" in ton_connect_json:
            return ""
        
        connection_str: str = ton_connect_json["connection"]
        conn_json = json.loads(connection_str.replace('\\"', '"'))

        if not "connect_event" in conn_json:
            return ""
        if conn_json["connect_event"]["payload"]["items"] == []:
            return ""
        if not "address" in conn_json["connect_event"]["payload"]["items"][0]:
            return ""
        
        raw_address = conn_json["connect_event"]["payload"]["items"][0]["address"]
        ton_address = Address(raw_address).to_str(is_bounceable=False)
        print("[get_ton_address] %s -> %s" % (raw_address, ton_address))
        return ton_address


class StudySentence(models.Model):
    """
    每日一句
    """
    text_chs = models.CharField(max_length=300, unique=True)
    text_eng = models.CharField(max_length=300, unique=True)
    youtube_url = models.CharField(max_length=300, default="")
    audio_url = models.CharField(max_length=300, default="")

    send_time = models.DateTimeField()
    is_sent = models.BooleanField(default=False)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s (%s)" % (self.send_time.date(), self.text_eng[:30])


class UserStudyRecord(models.Model):
    """
    用户学习记录
    """
    TYPE_CHOICES_TEXT, TYPE_CHOICES_AUDIO, TYPE_CHOICES_OTHER = 'text', 'audio', 'other'
    TYPE_CHOICES = [
        (TYPE_CHOICES_TEXT, '文字'),
        (TYPE_CHOICES_AUDIO, '语音'),
        (TYPE_CHOICES_OTHER, '其他'),
    ]

    user = models.ForeignKey(MeUser, on_delete=models.CASCADE)  # 默认会在外键字段名后追加字符串 "_id"
    sentence = models.ForeignKey(StudySentence, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    time = models.DateTimeField(null=True, blank=True)
    score = models.TextField(default="", blank=True, verbose_name="打分")  # 不同type不一样，比如audio: overall/integrity/accuracy/fluency

    points = models.IntegerField(default=0, verbose_name="竹子")

    class Meta:
        unique_together = ('user', 'sentence', 'type')

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s @ %s" % (self.user.username, self.time)


class UserActivity(models.Model):
    """
    用户参加活动的记录
    """
    TYPE_CHOICES_BOT, TYPE_CHOICES_REFER, TYPE_CHOICES_LOTTERY = 'bot', 'refer', 'lottery'
    TYPE_CHOICES_WITHDRAW, TYPE_CHOICES_OTHER = 'withdraw', 'other'
    TYPE_CHOICES = [
        (TYPE_CHOICES_BOT, '关注bot'),
        (TYPE_CHOICES_REFER, '推荐用户'),
        (TYPE_CHOICES_LOTTERY, '抽奖'),
        (TYPE_CHOICES_WITHDRAW, '提现'),
        (TYPE_CHOICES_OTHER, '其他'),
    ]

    user = models.ForeignKey(MeUser, on_delete=models.CASCADE)
    sats = models.IntegerField(default=0, verbose_name="聪/竹子")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_CHOICES_BOT)
    desc = models.CharField(max_length=200, default="")

    tons = models.DecimalField(default=Decimal("0.0"), max_digits=20, decimal_places=10, verbose_name="TON币")
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

