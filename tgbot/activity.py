from decimal import Decimal
import random
from django.utils import timezone
from tgbot.models import MeUser, UserActivity
from tgbot.ton_api import send_ton
from asgiref.sync import sync_to_async


def get_lottery_tons():
    # 生成一个0到1之间的随机浮点数
    r = random.random()

    # 根据概率返回不同的值
    if r < 0.5:  # 50%的概率返回0.0001
        return Decimal("0.0001")
    if r < 0.95:  # 45%的概率返回0.001
        return Decimal("0.001")
    else:  # 剩下5%的概率返回0.01
        return Decimal("0.01")


ACT_DESC_LOTTERY = "消耗竹子抽TON"
LOTTERY_DAILY_TIMES = 2
LOTTERY_POINTS = 2
MSG_LOTTERY_COUNT = "今天已经抽奖%d次，达到上限，请明日再来。" % LOTTERY_DAILY_TIMES
MSG_LOTTERY_POINTS = "你的竹子不到%d个，无法参加抽奖，请先打卡获取更多竹子。" % LOTTERY_POINTS
MSG_LOTTERY_OK = "恭喜你！消耗%s个竹子抽到%s个TON币。"
def activity_lottery(user: MeUser, desc=ACT_DESC_LOTTERY):
    """
    消耗竹子抽TON，返回消息（成功/失败等）
    """
    if user.points < LOTTERY_POINTS:
        return MSG_LOTTERY_POINTS

    # 判断是否当天已经抽奖2次，如果是就不能再抽奖了
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)
    if UserActivity.objects.filter(user=user, type=UserActivity.TYPE_CHOICES_LOTTERY,
                                   created_time__gte=today_start, created_time__lt=today_end).count() >= LOTTERY_DAILY_TIMES:
        print("[activity_lottery] Already 2 lotteries today:", user.username)
        return MSG_LOTTERY_COUNT
    
    # 随机抽TON币
    tons = get_lottery_tons()
    activity = UserActivity(user=user, type=UserActivity.TYPE_CHOICES_LOTTERY, tons=tons, sats=-LOTTERY_POINTS, desc=desc)
    activity.save()

    # 将积分（竹子）和TON币更新到MeUser表
    user.points -= LOTTERY_POINTS
    user.tons += tons
    user.save()

    return MSG_LOTTERY_OK % (LOTTERY_POINTS, tons)


WITHDRAW_THRESHOLD = Decimal("0.02")
WITHDRAW_GAS = Decimal("0.01")
WITHDRAW_DAILY_TIMES = 1
MSG_WITHDRAW_THRESHOLD = "你的TON的余额 %.4f 小于 %s，无法提现。"
MSG_WITHDRAW_DAILY = "你今天已经提现过一次了，1天只能提现1次。"
MSG_WITHDRAW_NOWALLET = "没有钱包无法提现，请先绑定你的钱包。"
MSG_WITHDRAW_OK = "提现成功：扣除gas费 0.01 TON，你的余额 %.4f 已经全部提现到钱包 %s"
MSG_WITHDRAW_ERROR = "提现有错误，请在群内联系管理员：https://t.me/ZaoAnYingWen"
MSG_WITHDRAW_WAIT = "发起提现，稍等片刻"
def activity_withdraw_qualify(user: MeUser):
    """
    是否可以提现
    返回：True/False和消息
    """
    if user.tons < WITHDRAW_THRESHOLD:
        text = MSG_WITHDRAW_THRESHOLD % (user.tons, WITHDRAW_THRESHOLD)
        return False, text
    
    if user.tons > 10:  # TODO: 为了安全，高于10个TON的提现暂时不支持
        print("[activity_withdraw] user.tons > 10:", user.username)
        return False, MSG_WITHDRAW_ERROR

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)
    daily_count = UserActivity.objects.filter(user=user, type=UserActivity.TYPE_CHOICES_WITHDRAW,
                                              created_time__gte=today_start, created_time__lt=today_end).count()
    if daily_count >= WITHDRAW_DAILY_TIMES:
        print("[activity_withdraw] daily withdraw tims > %s:" % WITHDRAW_DAILY_TIMES, user.username)
        return False, MSG_WITHDRAW_DAILY
    
    ton_addr = user.get_ton_address()
    if ton_addr == "":
        return False, MSG_WITHDRAW_NOWALLET
    
    return True, MSG_WITHDRAW_WAIT

async def activity_withdraw(user: MeUser):
    """
    提现所有TON余额，返回消息（成功/失败等）
    提前之前，先通过 activity_withdraw_qualify 函数查询是否可以提现
    """
    if user.tons < WITHDRAW_THRESHOLD or user.tons > 10:  # 默认通过 activity_withdraw_qualify 之后不会出错
        print("[activity_withdraw] ERROR in tons.")
        return MSG_WITHDRAW_ERROR
    
    withdraw_tons = user.tons - WITHDRAW_GAS
    ton_addr = user.get_ton_address()
    if ton_addr == "":
        print("[activity_withdraw] ERROR in wallet address.")
        return MSG_WITHDRAW_ERROR
    mask_ton_addr = ton_addr[:4] + "****" + ton_addr[-4:]
    text = MSG_WITHDRAW_OK % (withdraw_tons, mask_ton_addr)
    activity = UserActivity(user=user, type=UserActivity.TYPE_CHOICES_WITHDRAW, tons=-user.tons, desc=text)
    await sync_to_async(activity.save)()

    # 扣除0.01的gas费之后，将余额全部提现
    user.tons = Decimal("0.0")
    await sync_to_async(user.save)()

    await send_ton(withdraw_tons, ton_addr)
    return text


if __name__ == "__main__":
    pass
