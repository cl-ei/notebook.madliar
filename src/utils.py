import string
import random

from jinja2 import Template
from typing import *
from fastapi.responses import HTMLResponse


def randstr(byte_len: int = 32):
    chars = string.ascii_letters + string.digits
    return ''.join([random.choice(chars) for _ in range(byte_len)])


class TPLCache:
    templates: Dict[str, Template] = {}


def render_to_html(tpl: str, context: Dict = None) -> HTMLResponse:
    if tpl in TPLCache.templates:
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
