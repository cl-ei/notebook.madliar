import json
import logging
import os.path
from typing import Dict
from fastapi import APIRouter, Query, Path, Body, Cookie, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from src.utils import render_to_html, get_file_type
from src.db.query.auth import AuthMgr
from src.operation.api_handler import SupportedAction, CustomRequest
from src.operation.data_io import get_share, get_original_file
from src import error
router = APIRouter()


"""
URL允许不转义即可出现的特殊字符：$、-、_、.、+、!、*、'、(、)
base64编码的特殊字符: +、/、=
在notebook URL编码中，使用/分隔 user 和 service 部分

 

"""


@router.get("/notebook")
async def homepage(
        token: str = Cookie("", alias="token")
) -> HTMLResponse:
    try:
        login_info = await AuthMgr.get_login_info(token)
        login_info = login_info.dict()
    except Exception:  # noqa
        login_info = {}

    return render_to_html(
        tpl="src/tpl/notebook.html",
        context={"login_info": login_info}
    )


@router.post("/notebook/api")
async def api(request: Request):
    try:
        body = await request.json()
    except json.decoder.JSONDecodeError:
        return {"code": 422, "msg": "请求参数错误"}

    headers = request.headers
    cookies = request.cookies
    return await SupportedAction.handler(CustomRequest(body=body, headers=headers, cookies=cookies))


@router.post("/notebook/upload")
async def upload(
        request: Request,
        file: UploadFile = File(...),
        node_id: str = Form(...),
):
    if file.size > 1024*1024*5:
        return {"code": 400, "msg": "文件过大，最大支持5MB"}

    headers = request.headers
    cookies = request.cookies
    return await SupportedAction.handler(CustomRequest(
        body={"node_id": node_id, "action": "upload_file"},
        headers=headers,
        cookies=cookies,
        file=file,
    ))


@router.get("/notebook/share/{email_user}/{email_service}/{file:path}")
async def share(
        email_user: str = Path(...),
        email_service: str = Path(...),
        file: str = Path(...),
):
    email = f"{email_user}@{email_service}"
    content = await get_share(email, file)
    return Response(content, media_type="text/plain")


@router.get("/notebook/img_preview/{email_user}/{email_service}/{file:path}")
async def img_preview(
        email_user: str = Path(...),
        email_service: str = Path(...),
        file: str = Path(...),
        token: str = Cookie(...),
):
    login_info = await AuthMgr.varify_token(token)
    email = f"{email_user}@{email_service}"
    if login_info.email != email:
        raise error.Forbidden()

    mimetype, content = await get_original_file(email, file)
    if not isinstance(mimetype, str) or "image/" not in mimetype:
        raise error.NotFound()

    return Response(content, media_type=mimetype)
