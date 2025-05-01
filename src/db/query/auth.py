import hashlib
from typing import *
from pydantic import BaseModel
from src.db.client.my_redis import redis_client, GlobalLock
from src.framework.error import ErrorWithPrompt
from src.operation import data_io
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

    @classmethod
    async def gen_temporary_token(cls) -> str:
        token_key = utils.randstr(24)
        return token_key

    @classmethod
    async def varify_token(cls, email: str,  token: str) -> LoginInfo:
        token_list = await data_io.load_user_token(email)
        if token in token_list:
            return LoginInfo(email=email)
        raise ErrorWithPrompt("认证失败")

    @classmethod
    async def register(cls, email: str, password: str) -> str:
        async with GlobalLock(redis=redis_client, name=f"login:{email}", try_times=1) as lock:
            if not lock.locked:
                raise ErrorWithPrompt("操作频繁，请稍后再试")

            encrypted_password = await data_io.get_encrypted_password(email)
            if encrypted_password:
                raise ErrorWithPrompt("用户已存在，请登录。如果遗忘密码，请联系站长")

            encrypted_key = Encryptor.encode(password)
            await data_io.set_encrypted_password(email, encrypted_key)
            token = await cls.gen_temporary_token()
            await data_io.add_user_token(email, token)
            return token

    @classmethod
    async def login(cls, email: str, password: str) -> str:
        async with GlobalLock(redis=redis_client, name=f"login:{email}", try_times=1) as lock:
            if not lock.locked:
                raise ErrorWithPrompt("登录频繁，请稍后再试")
            existed_encrypted = await data_io.get_encrypted_password(email)
            check_pass = Encryptor.encode(password)
            if check_pass != existed_encrypted:
                raise ErrorWithPrompt("email或密码错误")

            token = await cls.gen_temporary_token()
            await data_io.add_user_token(email, token)
            return token

    @classmethod
    async def logout(cls, email: str, token: str) -> None:
        await data_io.delete_user_token(email, token)

    @classmethod
    async def change_password(cls, email, old_password, new_password) -> None:
        async with GlobalLock(redis=redis_client, name=f"login:{email}", try_times=1) as lock:
            if not lock.locked:
                raise ErrorWithPrompt("操作频繁，请稍后再试")

            encrypted_password = await data_io.get_encrypted_password(email)
            encrypted_old = Encryptor.encode(old_password)
            if encrypted_old != encrypted_password:
                raise ErrorWithPrompt("email或密码错误")

            # 写入新密码
            encrypted_key = Encryptor.encode(new_password)
            await data_io.set_encrypted_password(email, encrypted_key)

            # 删除 token
            await data_io.delete_all_user_token(email)

    @classmethod
    async def get_login_info(cls, email: str, token: str) -> Optional[LoginInfo]:
        if not token or not email:
            return None

        token_list = await data_io.load_user_token(email)
        if token in token_list:
            return LoginInfo(email=email)
        return None

    @classmethod
    async def force_reset_password(cls, email: str, password: str):
        encrypted_key = Encryptor.encode(password)
        await data_io.set_encrypted_password(email, encrypted_key)
        await data_io.delete_all_user_token(email)
