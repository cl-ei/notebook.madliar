import os
import platform
from datetime import datetime
from urllib.parse import unquote
from fastapi import APIRouter
from fastapi.responses import Response
from fastapi.requests import Request
from fastapi import Query


router = APIRouter()

MAX_RECORDS = 500

# ---------- 路径判定 ----------
SYSTEM = platform.system()

if SYSTEM == "Windows":
    BASE_DIR = r"C:\_PRIVATE_ROOT\tmp"
else:  # Linux / Docker / Server
    BASE_DIR = "/storage_root"
os.makedirs(BASE_DIR, exist_ok=True)

SMS_FILE = os.path.join(BASE_DIR, "sms_list.txt")
TOKEN_FILE = os.path.join(BASE_DIR, "sms_token.txt")
MAX_RECORDS = 500


def parse_sms_body(body: bytes) -> dict:
    """
    解析 x-www-form-urlencoded 数据
    """
    text = body.decode("utf-8")
    params = {}
    for part in text.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key] = unquote(value)
    return params


def save_sms_record(record: dict):
    """
    保存 SMS 记录，并保持最多 500 条，最新在最前
    """
    # 可读时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_entry = (
        f"===== {now} =====\n"
        f"FROM     : {record.get('from')}\n"
        f"CONTENT  :\n{record.get('content')}\n"
        f"TIMESTAMP: {record.get('timestamp')}\n"
        f"{'='*40}\n\n"
    )

    # 读取已有内容
    try:
        with open(SMS_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = ""

    # 合并并限制条数
    all_content = new_entry + old_content
    records = all_content.split("\n\n")
    limited_content = "\n\n".join(records[:MAX_RECORDS])

    # 写回文件
    with open(SMS_FILE, "w", encoding="utf-8") as f:
        f.write(limited_content)


@router.get("/notebook/sms_list")
async def get_sms(token: str = Query("")) -> Response:
    """
    返回当前保存的 SMS 列表
    """

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            true_token = f.read().strip()
    except:  # noqa
        true_token = "-no-token-"
    if token != true_token:
        return Response(
            content="=== forbidden ===",
            media_type="text/plain; charset=utf-8"
        )

    try:
        with open(SMS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "No SMS records found."

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8"
    )


@router.post("/notebook/sms_list")
async def post_sms(req: Request) -> Response:
    """
    接收远端设备发送的 SMS 数据
    """
    req_body = await req.body()
    data = parse_sms_body(req_body)

    save_sms_record(data)

    return Response(
        content="OK",
        status_code=200
    )
