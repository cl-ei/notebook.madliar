import re
import os
from pydantic import BaseModel
from typing import *
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from src.db.query.auth import AuthMgr
from src.error import ErrorWithPrompt
from src.operation import data_io
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
            mad_token = req.cookies.get("token")
            try:
                login_info = await AuthMgr.varify_token(mad_token)
            except ErrorWithPrompt as e:
                return {"code": 403, "msg": e.msg}
            req.email = login_info.email
        return await picked_func(req)


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
    resp.set_cookie("token", value=token, httponly=True)
    return resp


@SupportedAction(action="register")
async def register(request):
    email = request.body.get("email")
    password = request.body.get("password", "")

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
    await data_io.mkdir(email, "/")
    return resp


@SupportedAction(action="logout", login_required=True)
async def logout(request):
    token = request.cookies.get("token")
    await AuthMgr.logout(token)
    resp = JSONResponse({"code": 0})
    resp.delete_cookie(key="token", httponly=True)
    return resp


@SupportedAction(action="change_password", login_required=True)
async def change_password(request):
    token = request.cookies.get("token")
    old_password = request.body.get("old_password", "")
    new_password = request.body.get("new_password", "")

    if not 5 < len(old_password) < 48 or not 5 < len(new_password) < 48:
        return {"code": 403, "msg": u"email或密码错误"}

    try:
        await AuthMgr.change_password(token, old_password, new_password)
    except ErrorWithPrompt as e:
        return {"code": 403, "msg": e.msg}

    resp = JSONResponse({"code": 0})
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

    获取文件：
        request args:
            file（node_id）: 文件路径
            version: numeric str, 版本号，可为空。为空时，返回最新版本号
        response:
            version: str 版本号，可为空。
                - 为空，则为原始文件。
                - 否则为某版本，从0开始，每个版本必关联一个 base: 原始文件，版本号是基于base的差异，版本之间无关联
            content: 全量内容

            img: bool 若为图片文件，则此 value 为 True

    保存文件:
        request args:
            range: str, "all" 或 "delta", 全量或增量
                - all: 此时直接保存 content 为新的 base，并为此 base 创建version
                - delta: 此时需要增量保存，需要根据based version 还原出 base，验证 md5 是否正确，并将增量（diff）保存为新版本。
                    若md5不正确，则返回 错误，改为全量保存

                note: 没有version时，必须采用全量保存

            content: Optional[str]

            based_version: str
            base_md5: str
            diff: List
        response:
            version: str, 保存之后的版本号
    """
    file = request.body.get("node_id")
    version = request.body.get("version", "")

    # special logic: judge img
    path, inner = os.path.split(file)
    if "." in inner:
        ext = inner.split(".")[-1]
        if utils.get_file_type(ext) == "img":
            # TODO: add shared key
            shared_key = ""
            return {
                "err_code": 0,
                "key": shared_key,
                "bin": True,
                "path": file
            }

    content, version = await data_io.openfile(request.email, file, version)
    return {
        "code": 0,
        "content": content,
        "version": version,
        "path": file,
    }


@SupportedAction(action="save", login_required=True)
async def save(request: CustomRequest):
    file = request.body.get("node_id")
    save_range = request.body.get("range")
    if save_range == "all":
        content = request.body.get("content")
        version = await data_io.savefile(request.email, file, content)

    elif save_range == "delta":
        based_version: str = request.body.get("based_version")
        base_md5: str = request.body.get("base_md5")
        diff = [data_io.DiffItem(**d) for d in request.body.get("diff")]
        version = await data_io.savefile_delta(request.email, file, based_version, base_md5, diff)

    else:
        raise ErrorWithPrompt("不支持此保存方式")

    return {"code": 0, "version": version}


@SupportedAction(action="share", login_required=True)
async def share(request: CustomRequest):
    file = request.body.get("node_id")
    await data_io.create_share(request.email, file=file)
    return {"code": 0, "key": f"/notebook/share/{request.email}?file={file}"}


@SupportedAction(action="upload_file", login_required=True)
async def upload_file(request: CustomRequest):
    path: str = request.body.get("node_id")
    filename = request.file.filename
    savefile = os.path.join(path.lstrip("/"), filename)
    content: bytes = await request.file.read(1024*1024*5)
    await data_io.savefile(request.email, savefile, content, create=True)
    return {"code": 0}
