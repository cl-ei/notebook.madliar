import json
from typing import Dict
from fastapi import APIRouter, Query, Path, Body, Cookie, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from src.utils import render_to_html, CustomEncode
from src.db.query.auth import AuthMgr
from src.operation.api_handler import SupportedAction, CustomRequest
from src.operation.data_io import get_share
router = APIRouter()


"""
URL允许不转义即可出现的特殊字符：$、-、_、.、+、!、*、'、(、)
base64编码的特殊字符: +、/、=
在notebook URL编码中，自定义规则：

1. base64编码后，"/"转化为"_", "="转化为"-" 
2. email: user@service.com => username的部分保留，service.com使用1编码,二者使用.连接
3. share url: email使用2的方式编码，file使用1方式编码  

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


@router.get("/notebook/share/{email}/{file}")
async def share(email: str = Path(...), file: str = Path(...)):
    user, service_enc = email.rsplit(".", 1)
    service = CustomEncode.decode(service_enc)
    real_email = f"{user}@{service}"
    real_file = CustomEncode.decode(file)
    content = await get_share(real_email, real_file)
    return Response(content, media_type="text/plain")
