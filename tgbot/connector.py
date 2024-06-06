from pytonconnect import TonConnect
from tgbot.models import MeUser
from tgbot.utils import get_user_from_id
from uglypanda.settings import MANIFEST_URL
from pytonconnect.storage import IStorage
import redis.asyncio as redis
from asgiref.sync import sync_to_async

## django ##

class TcStorageDj(IStorage):

    def __init__(self, chat_id):
        self.chat_id = chat_id

    async def set_item(self, key: str, value: str):
        me_user = await sync_to_async(get_user_from_id)(self.chat_id)
        # me_user = await get_user_from_id(self.chat_id)
        await sync_to_async(me_user.set_ton_connect)(key, value)

    async def get_item(self, key: str, default_value: str = None):
        me_user = await sync_to_async(get_user_from_id)(self.chat_id)
        # me_user = await get_user_from_id(self.chat_id)
        storage = me_user.get_ton_connect()
        return storage[key] if key in storage else default_value

    async def remove_item(self, key: str):
        me_user = await sync_to_async(get_user_from_id)(self.chat_id)
        await sync_to_async(me_user.remove_ton_connect)(key)

def get_connector(chat_id: int):
    return TonConnect(MANIFEST_URL, storage=TcStorageDj(chat_id))

## redis ##

client = redis.Redis(host='localhost', port=6379)

class TcStorage(IStorage):

    def __init__(self, chat_id: int):
        self.chat_id = chat_id

    def _get_key(self, key: str):
        return str(self.chat_id) + key

    async def set_item(self, key: str, value: str):
        await client.set(name=self._get_key(key), value=value)

    async def get_item(self, key: str, default_value: str = None):
        value = await client.get(name=self._get_key(key))
        return value.decode() if value else default_value

    async def remove_item(self, key: str):
        await client.delete(self._get_key(key))

def get_connector_redis(chat_id: int):
    return TonConnect(MANIFEST_URL, storage=TcStorage(chat_id))

