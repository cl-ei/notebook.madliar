import base64
import hashlib
from typing import *
from pydantic import BaseModel
from src.db.client.my_redis import redis_client
from src.error import ErrorWithPrompt
from src import utils


class Encryptor:
    @staticmethod
    def encode(text: str) -> str:
        hash_object = hashlib.sha256(text.encode())
        return hash_object.hexdigest()


class LoginInfo(BaseModel):
    email: str


class AuthMgr:
    _key_token = "TK:{email}:{token_key}"
    _key_email_password = "USR:{email}"

    @classmethod
    async def gen_token(cls, email: str) -> str:
        token_key = utils.randstr(12)
        token_value = utils.randstr()
        flag = await redis_client.set(key=f"TK:{email}:{token_key}", value=token_value, timeout=3600*24*30)
        if flag:
            return f"{email}:{token_key}:{token_value}"
        raise ErrorWithPrompt("未能生成token")

    @classmethod
    async def register(cls, email: str, password: str) -> str:
        password_key = f"USR:{email}"
        origin = await redis_client.get(password_key)
        if origin is not None:
            raise ErrorWithPrompt("用户已存在")

        encrypted_key = Encryptor.encode(password)
        await redis_client.set(password_key, value=encrypted_key)
        return await cls.gen_token(email)

    @classmethod
    async def varify_token(cls, token: str) -> LoginInfo:
        try:
            email, token_key, token_value = token.split(":", 2)
        except ValueError:
            raise ErrorWithPrompt("认证失败")

        saved_value = await redis_client.get(f"TK:{email}:{token_key}")
        if saved_value == token_value:
            return LoginInfo(email=email)
        raise ErrorWithPrompt("认证失败")

    @classmethod
    async def login(cls, email: str, password: str) -> str:
        password_key = f"USR:{email}"
        origin = await redis_client.get(password_key)
        if origin is None or origin != Encryptor.encode(password):
            raise ErrorWithPrompt("email或密码错误")
        return await cls.gen_token(email)

    @classmethod
    async def logout(cls, token) -> None:
        try:
            email, token_key, token_value = token.split(":", 2)
        except ValueError:
            return

        saved_value = await redis_client.get(f"TK:{email}:{token_key}")
        if saved_value == token_value:
            await redis_client.delete(f"TK:{email}:{token_key}")

    @classmethod
    async def change_password(cls, token, old_password, new_password) -> None:
        try:
            email, token_key, token_value = token.split(":", 2)
        except ValueError:
            raise ErrorWithPrompt("认证失败")

        # 验证旧密码
        password_key = f"USR:{email}"
        origin = await redis_client.get(password_key)
        if origin is None or origin != Encryptor.encode(old_password):
            raise ErrorWithPrompt("email或密码错误")

        # 写入新密码
        encrypted_key = Encryptor.encode(new_password)
        await redis_client.set(password_key, value=encrypted_key)

        # 删除 token
        saved_value = await redis_client.get(f"TK:{email}:{token_key}")
        if saved_value == token_value:
            await redis_client.delete(f"TK:{email}:{token_key}")

    @classmethod
    async def get_login_info(cls, token: str) -> Optional[LoginInfo]:
        if not token:
            return None
        try:
            email, key, value = token.split(":", 2)
        except ValueError:
            return None
        saved_tv = await redis_client.get(f"TK:{email}:{key}")
        if saved_tv and saved_tv == value:
            return LoginInfo(email=email)
        return None
