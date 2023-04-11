import os
import shutil
from pydantic import BaseModel
from typing import *
from src.config import DEBUG
from src import utils
from src.error import ErrorWithPrompt


storage_root = "./storage" if DEBUG else "/data/storage"
"""
在文件同级目录，有 "{file_name}.meta"的文件夹，存储该文件的元信息
file:   - {storage_root}/{email}/user_root/readme.md
meta:   - {storage_root}/{email}/user_root/readme.md.meta/
 * share.txt - 创建过的分享

"""


class FileLike(BaseModel):
    id: Optional[str] = ""
    type: Optional[str] = ""
    text: Optional[str] = ""
    children: bool = True


async def mkdir(email: str, path: str):
    _, last_dir = os.path.split(path)
    if last_dir.endswith(".meta"):
        raise ErrorWithPrompt("名称不可以\".meta\"结尾")

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
            if f.endswith(".meta"):
                continue
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
    if os.path.isdir(dist) and new_name.endswith(".meta"):
        raise ErrorWithPrompt("名称不可以\".meta\"结尾")

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


async def create_share(email: str, file: str):
    """创建文件分享"""
    rel_file_path = file.lstrip("/")
    dist_file = os.path.join(storage_root, email, rel_file_path)
    if not os.path.exists(dist_file) or not os.path.isfile(dist_file):
        raise ErrorWithPrompt("文件不存在")

    meta_path = dist_file + ".meta"
    os.makedirs(meta_path, exist_ok=True)
    with open(os.path.join(meta_path, "share.txt"), "w") as _:
        ...
    return True


async def get_share(email: str, file: str) -> str:
    rel_file_path = file.lstrip("/")
    share_meta = os.path.join(storage_root, email, f"{rel_file_path}.meta", "share.txt")
    if not os.path.exists(share_meta) or not os.path.isfile(share_meta):
        raise ErrorWithPrompt("权限错误")

    dist_file = os.path.join(storage_root, email, rel_file_path)
    if not os.path.exists(share_meta) or not os.path.isfile(share_meta):
        raise ErrorWithPrompt("文件不存在")
    with open(dist_file, "rb") as f:
        content = f.read()
    return content.decode("utf-8")
