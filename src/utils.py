import os
import string
import random
import hashlib
from jinja2 import Template
from typing import *
from fastapi.responses import HTMLResponse
from src.framework.config import DEBUG


def randstr(byte_len: int = 32):
    chars = string.ascii_letters + string.digits
    return ''.join([random.choice(chars) for _ in range(byte_len)])


class TPLCache:
    templates: Dict[str, Template] = {}


def render_to_html(tpl: str, context: Dict = None) -> HTMLResponse:
    if not DEBUG and tpl in TPLCache.templates:
        template = TPLCache.templates[tpl]
    else:
        with open(tpl, "rb") as f:
            content = f.read().decode("utf-8")
        TPLCache.templates[tpl] = template = Template(content)
    if context is None:
        context = {}
    html = template.render(context)
    return HTMLResponse(html)


def get_file_type(ex_name):
    if ex_name and ex_name.lower() in ("txt", "text", "ini", "conf", "yml", "c", "cpp", "py", "json", "js"):
        return "text"
    elif ex_name.lower() in ("md", "markdown"):
        return "md"
    elif ex_name.lower() in ("png", "jpg", "jpeg", "gif", "bmp"):
        return "img"
    else:
        return "bin"


def calc_md5(content: str) -> str:
    md5 = hashlib.md5()
    md5.update(content.encode("utf-8"))
    return md5.hexdigest()


def safe_make_dir(path: str) -> bool:
    for _try_time in range(3):
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:  # noqa
            pass
    return False


def list_all_files(path: str) -> List[str]:
    result = []
    scan_list = [path]
    while scan_list:
        this_path = scan_list.pop(0)
        for file in os.listdir(this_path):
            full = os.path.join(this_path, file)
            if os.path.isdir(full):
                scan_list.append(full)
            elif os.path.isfile(full):
                result.append(full)
    return result
