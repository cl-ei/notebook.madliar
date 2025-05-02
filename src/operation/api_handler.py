import mimetypes
import re
import os

from pydantic import BaseModel
from typing import *
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from src.framework.config import DEBUG
from src.db.client.my_redis import GlobalLock, redis_client
from src.db.query.auth import AuthMgr
from src.framework.error import ErrorWithPrompt
from src.operation import data_io
from src.operation.blog import fresh_blog
from src import utils


class CustomRequest(BaseModel):
    body: Dict
    headers: Dict
    cookies: Dict
    email: str = ""
    file: Optional[UploadFile]


class SupportedAction(object):
    __function: Dict[str, Tuple[Callable, bool]] = {}

    def __init__(self, action, login_required=False):
        self.__action = action
        self.login_required = login_required

    def __call__(self, func):
        self.__class__.__function[self.__action] = (func, self.login_required)
        return func

    @classmethod
    async def handler(cls, req: CustomRequest):
        action = req.body.get("action")
        cached = cls.__function.get(action)
        if not cached:
            return {"code": 404, "msg": f"Action({action}) is not supported."}
        picked_func, login_required = cached
        if login_required:
            email = req.cookies.get("email")
            token = req.cookies.get("token")
            try:
                login_info = await AuthMgr.varify_token(email, token)
            except ErrorWithPrompt as e:
                return {"code": 403, "msg": e.msg}
            req.email = login_info.email
        return await picked_func(req)


@SupportedAction(action="register")
async def register(request):
    email = request.body.get("email")
    password = request.body.get("password", "")

    if not DEBUG:
        return {
            "code": 400,
            "msg": "由于此站点遭受攻击，不再支持注册。你可以自行部署此网站的开源版本，具体请访问："
                   '<a href="https://github.com/cl-ei/notebook.madliar">https://github.com/cl-ei/notebook.madliar</a>'
        }

    email_pattern = re.compile(r"^[A-Za-z\d]+([-_.][A-Za-z\d]+)*@([A-Za-z\d]+[-.])+[A-Za-z\d]{2,4}$")
    if not email_pattern.match(email):
        return {"code": 403, "msg": "错误的邮箱"}

    if not 5 < len(password) < 48:
        return {"code": 403, "msg": "密码长度限定为6~47字符"}

    try:
        token = await AuthMgr.register(email, password)
    except ErrorWithPrompt as e:
        return {"code": 403, "msg": e.msg}

    resp = JSONResponse({"code": 0, "email": email})
    resp.set_cookie(key="token", value=token, httponly=True)
    resp.set_cookie(key="email", value=email, httponly=True)
    await data_io.mkdir(email, "/")
    return resp


@SupportedAction(action="logout", login_required=True)
async def logout(request):
    email = request.cookies.get("email")
    token = request.cookies.get("token")

    await AuthMgr.logout(email, token)
    resp = JSONResponse({"code": 0})

    resp.delete_cookie(key="email", httponly=True)
    resp.delete_cookie(key="token", httponly=True)
    return resp


@SupportedAction(action="login")
async def login(request: CustomRequest):
    email = request.body["email"]
    password = request.body["password"]

    email_pattern = re.compile(r"^[A-Za-z\d]+([-_.][A-Za-z\d]+)*@([A-Za-z\d]+[-.])+[A-Za-z\d]{2,4}$")
    if not email_pattern.match(email):
        return {"code": 403, "msg": u"错误的邮箱"}

    if not 5 < len(password) < 48:
        return {"code": 403, "msg": u"密码过长或过短"}

    try:
        token = await AuthMgr.login(email, password)
    except ErrorWithPrompt as e:
        return {"code": 403, "msg": e.msg}

    resp = JSONResponse({"code": 0, "email": email})
    resp.set_cookie("email", value=email, httponly=True)
    resp.set_cookie("token", value=token, httponly=True)
    return resp


@SupportedAction(action="change_password", login_required=True)
async def change_password(request):
    email = request.cookies.get("email")
    old_password = request.body.get("old_password", "")
    new_password = request.body.get("new_password", "")

    if not 5 < len(old_password) < 48 or not 5 < len(new_password) < 48:
        return {"code": 403, "msg": u"email或密码错误"}

    try:
        await AuthMgr.change_password(email, old_password, new_password)
    except ErrorWithPrompt as e:
        return {"code": 403, "msg": e.msg}

    resp = JSONResponse({"code": 0})
    resp.delete_cookie(key="email", httponly=True)
    resp.delete_cookie(key="token", httponly=True)
    return resp


@SupportedAction(action="listdir", login_required=True)
async def listdir(request: CustomRequest):
    path = request.body.get("path")
    if path == "#":
        return JSONResponse([{
            "id": "/",
            "type": "folder",
            "text": request.email,
            "children": True
        }])

    files = await data_io.listdir(request.email, path)
    return [f.dict() for f in files]


@SupportedAction(action="mkdir", login_required=True)
async def mkdir(request: CustomRequest):
    node_id = request.body.get("node_id")
    dir_name = request.body.get("dir_name")

    try:
        rel_path = os.path.join(node_id, dir_name)
        await data_io.mkdir(request.email, rel_path)
    except ErrorWithPrompt as e:
        return {"code": 403, "msg": e.msg}
    return {"code": 0}


@SupportedAction(action="rm", login_required=True)
async def rm(request: CustomRequest):
    node_id = request.body.get("node_id")
    await data_io.rm(request.email, node_id)
    return {"code": 0}


@SupportedAction(action="rename", login_required=True)
async def rename(request: CustomRequest):
    node_id = request.body.get("node_id")
    new_name = request.body.get("new_name")
    if "/" in new_name or "\\" in new_name:
        raise ErrorWithPrompt("新路径名不可包含特殊字符")

    await data_io.rename(request.email, node_id, new_name)
    return {"code": 0}


@SupportedAction(action="new", login_required=True)
async def newfile(request: CustomRequest):
    node_id = request.body.get("node_id")
    file_name = request.body.get("file_name")
    file = os.path.join(node_id, file_name)
    try:
        await data_io.newfile(email=request.email, file=file)
    except ErrorWithPrompt as e:
        return {"code": 400, "msg": e.msg}
    return{"code": 0}


@SupportedAction(action="open", login_required=True)
async def openfile(request: CustomRequest):
    """
    打开文件和保存文件的逻辑
    创建 base 的规则：
    - 初始 base 与该version对应，如：b0 <=> v0, b10 <=> v10
    - 当基于某个 base 的 version 超过10的时候，rebuild base
    - 当某个 diff 超过100K的时候，rebuild base

    获取文件：
        request args:
            file（node_id）: 文件路径
            version: int, 版本号，可为空。为空时，返回最新版本号

        response:
            version: int 版本号，不可为空。从0开始，每个版本必关联一个。版本号是基于 base 的差异，版本之间无关联
            base: int, base的版本，不可为空，从0开始。
                - 约定：version 0 与 base 0 对应，当获取不到 meta 文件时，content 返回原文件，base 和 version 都返回 0；
                    即，meta 文件当中，真正的 base 和 version 都是从 1 开始
            base_content: str, base 的内容
            diff: List, 从 base 到该版本的增量，可为空列表。为空时，代表无差异

            # TODO:
            img: bool 若为图片文件，则此 value 为 True

    保存文件:
        request args:
            range: str, "all" 或 "delta", 全量或增量
                - all: 此时直接保存 content 为新的 base，并为此 base 创建 version
                - delta: 此时需要增量保存，根据 base 取原始内容，根据 diff 生成新文本，再验证md5。
                    并将增量（diff）保存为新版本。若md5不正确，则返回 错误，前端改为全量保存
                    这一步，根据diff大小适时改变 base，前端收到后比对 base 值，更新自身 base
                没有version时，必须采用全量保存

            content: Optional[str]

            base: int
            dist_md5: str
            diff: List

        response:
            base: int, 保存之后的 base
            version: int, 保存之后的版本号
    """
    file: str = request.body.get("node_id")
    try:
        version = request.body.get("version")
    except (ValueError, TypeError):
        version = None

    # special logic: judge img
    mimetype, _ = mimetypes.guess_type(file)
    if isinstance(mimetype, str) and "image/" in mimetype:
        user, service = request.email.split("@", 1)

        img_url = f"/notebook/img_preview/{user}/{service}/{file.lstrip('/')}"
        return {
            "code": 0,
            "img": True,
            "url": img_url,
            "path": file
        }

    fr: data_io.FileOpenRespData = data_io.openfile(request.email, file, version)
    resp_dict = fr.dict()
    resp_dict["code"] = 0
    return resp_dict


@SupportedAction(action="save", login_required=True)
async def save(request: CustomRequest):
    file = request.body.get("node_id")
    save_range = request.body.get("range")

    lock_key = f"LK:save:{request.email}:{utils.calc_md5(file)}"
    async with GlobalLock(redis_client, name=lock_key, lock_time=600) as lock:
        if not lock.locked:
            raise ErrorWithPrompt("访问频繁，请稍后再试")

        if save_range == "all":
            content = request.body.get("content")
            version, base = await data_io.savefile(request.email, file, content)

        elif save_range == "delta":
            try:
                base: int = int(request.body.get("base"))
            except (ValueError, TypeError):
                raise ErrorWithPrompt("错误的base")
            dist_md5: str = request.body.get("dist_md5", "")
            diff = [data_io.DiffItem(**d) for d in request.body.get("diff", [])]
            version, base = await data_io.savefile_delta(request.email, file, base, dist_md5, diff)

        else:
            raise ErrorWithPrompt("不支持此保存方式")

    return {"code": 0, "version": version, "base": base}


@SupportedAction(action="share", login_required=True)
async def share(request: CustomRequest):
    file: str = request.body.get("node_id")
    await data_io.create_share(request.email, file=file)
    user, service = request.email.split("@", 1)
    return {"code": 0, "key": f"/notebook/share/{user}/{service}/{file.lstrip('/')}"}


@SupportedAction(action="upload_file", login_required=True)
async def upload_file(request: CustomRequest):
    path: str = request.body.get("node_id")
    filename = request.file.filename
    savefile = os.path.join(path.lstrip("/"), filename)
    content: bytes = await request.file.read(1024*1024*25)
    await data_io.savefile(request.email, savefile, content, create=True)
    return {"code": 0}


@SupportedAction(action="history", login_required=True)
async def get_history(request: CustomRequest):
    path: str = request.body.get("node_id")
    history = await data_io.get_history(email=request.email, file=path)
    return {"code": 0, "history": history}


@SupportedAction(action="diff", login_required=True)
async def diff(request: CustomRequest):
    path: str = request.body.get("node_id")
    version: int = request.body.get("version")
    if version < 1:
        raise ErrorWithPrompt("无更新版本")

    history = await data_io.get_diff(email=request.email, file=path, version=version)
    resp = history.dict()
    resp["code"] = 0
    return resp


@SupportedAction(action="refresh_blog", login_required=True)
async def refresh_blog(request: CustomRequest):
    email = request.email
    await fresh_blog(email)
    return {"code": 0}


@SupportedAction(action="get_blog_info", login_required=True)
async def get_blog_info(request: CustomRequest):
    email = request.email
    last_ver = await data_io.get_blog_version(email)
    return {"code": 0, "last_update": last_ver}
