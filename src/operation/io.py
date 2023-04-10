import os
import shutil
from pydantic import BaseModel
from typing import *
from src.config import DEBUG
from src import utils
from src.error import ErrorWithPrompt


storage_root = "./storage" if DEBUG else "/data/storage"


class FileLike(BaseModel):
    id: Optional[str] = ""
    type: Optional[str] = ""
    text: Optional[str] = ""
    children: bool = True


async def mkdir(email: str, path: str):
    dist = os.path.join(storage_root, email, path.lstrip("/"))
    os.makedirs(dist, exist_ok=True)


async def listdir(email: str, path: str) -> List[FileLike]:
    dist = os.path.join(storage_root, email, path.lstrip("/"))
    result: List[FileLike] = []
    try:
        files = os.listdir(dist)
    except FileNotFoundError:
        return []

    for f in files:
        full = os.path.join(dist, f)
        if os.path.isdir(full):
            result.append(FileLike(id=os.path.join(path, f), type="folder", text=f))
        if os.path.isfile(full):
            if "." in f:
                ext = f.split(".")[-1]
                filetype = utils.get_file_type(ext)
            else:
                filetype = "bin"
            result.append(FileLike(id=os.path.join(path, f), type=filetype, text=f, children=False))
    return result


async def rm(email: str, path: str):
    dist = os.path.join(storage_root, email, path.lstrip("/"))
    if not os.path.exists(dist):
        return
    if os.path.isdir(dist):
        shutil.rmtree(dist)
    elif os.path.isfile(dist):
        os.remove(dist)


async def newfile(email: str, file: str):
    dist = os.path.join(storage_root, email, file.lstrip("/"))
    path, _ = os.path.split(dist)
    os.makedirs(path, exist_ok=True)
    with open(dist, "w") as _:
        ...
    return


async def rename(email: str, old_path: str, new_name: str):
    dist = os.path.join(storage_root, email, old_path.lstrip("/"))
    if not os.path.exists(dist):
        raise ErrorWithPrompt("路径不存在")
    path, _ = os.path.split(dist)
    new_path = os.path.join(path, new_name)
    os.rename(dist, new_path)


async def openfile(email: str, file: str) -> str:
    dist = os.path.join(storage_root, email, file.lstrip("/"))
    if not os.path.exists(dist) or not os.path.isfile(dist):
        raise ErrorWithPrompt("文件不存在")
    if os.stat(dist).st_size > 1024*1024:
        raise ErrorWithPrompt("文件过大，最大支持1MB")
    with open(dist, "rb") as f:
        bin_data = f.read()
    try:
        content = bin_data.decode("utf-8")
    except UnicodeDecodeError:
        raise ErrorWithPrompt("编码错误，请使用utf-8编码")
    return content


async def savefile(email: str, file: str, content: Union[str, bytes], create=False):
    dist = os.path.join(storage_root, email, file.lstrip("/"))
    if not os.path.exists(dist) or not os.path.isfile(dist):
        if not create:
            raise ErrorWithPrompt("文件不存在")

        parent, _ = os.path.split(dist)
        os.makedirs(parent, exist_ok=True)

    if isinstance(content, str):
        try:
            bin_content = content.encode("utf-8")
        except UnicodeEncodeError:
            raise ErrorWithPrompt("编码错误，请使用utf-8编码")
    else:
        bin_content = content
    with open(dist, "wb") as f:
        f.write(bin_content)
