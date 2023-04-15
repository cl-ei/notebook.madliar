import datetime
import json
import mimetypes
import os
import shutil
from pydantic import BaseModel
from typing import *
from src.config import DEBUG
from src import utils
from src.error import ErrorWithPrompt, NotFound


storage_root = "./storage" if DEBUG else "/data/storage"
"""
隐藏文件:
1. 在文件同级目录，有 "{file_name}.meta"的文件夹，存储该文件的元信息
file:   - {storage_root}/{email}/user_root/readme.md
meta:   - {storage_root}/{email}/user_root/readme.md.meta/
 * share.txt - 创建过的分享
2. 每个用户下有 "/blog.meta" 的文件夹，存储 blog 的索引
"""


class DiffItem(BaseModel):
    count: int
    added: bool = False
    removed: bool = False
    value: str = ""


class VersionFile(BaseModel):
    base: int
    diff: List[DiffItem] = []
    create_time: str


class FileLike(BaseModel):
    id: Optional[str] = ""
    type: Optional[str] = ""
    text: Optional[str] = ""
    children: bool = True


class FileOpenRespData(BaseModel):
    version: int
    base: int
    base_content: str
    diff: List[DiffItem] = []


def merge_content(base_content: str, diff: List) -> str:
    result = []
    index = 0
    for d in diff:
        if d.added is True:
            result.append(d.value)
        elif d.removed is True:
            index += d.count
        else:
            result.append(base_content[index: index + d.count])
            index += d.count
    result.append(base_content[index:])
    target_content = "".join(result)
    return target_content


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


async def _get_file_by_version(file: str, version: int) -> FileOpenRespData:
    """
    通过 version file 还原 全量文件

    Params
    ------
    version: int，必须存在，当其为0时，返回原文件

    Returns
    -------
    content: str 全量内容
    """
    # version 为 0，返回源文件
    if version < 0:
        raise ErrorWithPrompt(f"文件版本({version})不存在")

    if version == 0:
        try:
            with open(file, "rb") as f:
                bin_content = f.read()
            content = bin_content.decode("utf-8")
        except FileNotFoundError:
            raise ErrorWithPrompt("文件不存在")
        except UnicodeDecodeError:
            raise ErrorWithPrompt("文件编码错误，请使用utf-8编码")

        return FileOpenRespData(version=0, base=0, base_content=content)

    meta_path = f"{file}.meta"
    try:
        with open(os.path.join(meta_path, f"v{version}"), "rb") as f:
            ver_content = f.read()
    except FileNotFoundError:
        raise ErrorWithPrompt(f"文件版本({version})不存在")

    vf = VersionFile(**json.loads(ver_content))

    # 读取 base 文件
    base_file = os.path.join(meta_path, f"b{vf.base}") if vf.base > 0 else file
    try:
        with open(base_file, "rb") as f:
            bin_content = f.read()
        content = bin_content.decode("utf-8")
    except FileNotFoundError:
        raise ErrorWithPrompt("该版本源文件已不存在")
    except UnicodeDecodeError:
        raise ErrorWithPrompt("文件编码错误，请使用utf-8编码")
    return FileOpenRespData(version=version, base=vf.base, base_content=content, diff=vf.diff)


async def _get_last_vb_of_file(file) -> Tuple[Optional[int], Optional[int]]:
    """
    当 version 或者 base file 不存在时，返回 0。按照约定，0代表原文件

    Returns
    -------
    version: int
    base: int
    """
    meta_path = f"{file}.meta"
    last_version = 0
    last_base = 0
    try:
        for filename in os.listdir(meta_path):
            if not os.path.isfile(os.path.join(meta_path, filename)):
                continue

            if filename.startswith("v"):
                this_version = int(filename[1:])
                if this_version > last_version:
                    last_version = this_version
            elif filename.startswith("b"):
                this_base = int(filename[1:])
                if this_base > last_base:
                    last_base = this_base
    except FileNotFoundError:
        pass
    return last_version, last_base


async def openfile(email: str, file: str, version: int = None) -> FileOpenRespData:
    """
    获取文件：
        request args:
            file（node_id）: 文件路径
            version: numeric str, 版本号，可为空。为空时，返回最新版本号，没有最新版，则返回空
        response:
            version: int
            base: int
            base_content: str
            diff: List[DiffItem] = []
    """
    dist = os.path.join(storage_root, email, file.lstrip("/"))
    if not os.path.exists(dist) or not os.path.isfile(dist):
        raise ErrorWithPrompt("文件不存在")

    if version is None:
        version, _ = await _get_last_vb_of_file(dist)

    return await _get_file_by_version(dist, version)


async def savefile(email: str, file: str, content: Union[str, bytes], create=False) -> Tuple[int, int]:
    """
    全量保存文件

    1. 寻找最新 version 和 base，创建 base，并根据该 base 创建 version

    Returns
    -------
    version: int 版本号
    base: int base

    # TODO: add lock
    """
    if isinstance(content, str):
        try:
            bin_content = content.encode("utf-8")
        except UnicodeEncodeError:
            raise ErrorWithPrompt("编码错误，请使用utf-8编码")
    else:
        bin_content = content

    dist = os.path.join(storage_root, email, file.lstrip("/"))
    meta_path = f"{dist}.meta"
    if not os.path.exists(dist) or not os.path.isfile(dist):
        if not create:
            raise ErrorWithPrompt("文件不存在")

        # 创建新文件。只有 upload 接口才会触发至此，未创建就保存文件。此时应当清除 meta 文件夹
        parent, _ = os.path.split(dist)
        os.makedirs(parent, exist_ok=True)
        with open(dist, "wb") as f:
            f.write(bin_content)
        if os.path.exists(meta_path):
            shutil.rmtree(meta_path)
        return 0, 0

    # 创建
    # 寻找最新版本
    last_version, last_base = await _get_last_vb_of_file(dist)
    target_version, target_base = last_version + 1, last_base + 1

    # 创建base
    os.makedirs(meta_path, exist_ok=True)
    with open(os.path.join(meta_path, f"b{target_base}"), "wb") as f:
        f.write(bin_content)

    # 创建version
    version_data = VersionFile(base=target_base, create_time=f"{datetime.datetime.now()}")
    with open(os.path.join(meta_path, f"v{target_version}"), "wb") as f:
        f.write(version_data.json(ensure_ascii=False).encode("utf-8"))

    return target_version, target_base


async def savefile_delta(email: str, path: str, base: int, dist_md5: str, diff: List[DiffItem]) -> Tuple[int, int]:
    """
    增量保存文件

    1. 获取原始 base
    2. 根据 diff 生成目标内容
    3. 判断 md5 是否一致
    4. 存储 version 文件，（如果与base差距过大，重新分配base）（取最大version）
    4. 将 version 和 base 返回

    # TODO: 当 diff 过大，不值得保存增量文件时，重新生成 base，并基于新 base 生成 version

    Returns
    -------
    version: int 版本号
    base: int, rebuild 之后的 base
    """
    file = os.path.join(storage_root, email, path.lstrip("/"))
    meta_path = os.path.join(f"{file}.meta")
    base_file = os.path.join(meta_path, f"b{base}") if base > 0 else file
    try:
        with open(base_file, "rb") as f:
            bin_content = f.read()
        content = bin_content.decode("utf-8")
    except FileNotFoundError:
        raise ErrorWithPrompt("原文件不存在")
    except UnicodeDecodeError:
        raise ErrorWithPrompt("文件编码错误")

    target_content = merge_content(content, diff)
    result_md5 = utils.calc_md5(target_content)
    if result_md5 != dist_md5:
        raise ErrorWithPrompt("文件不一致")

    version, max_base = await _get_last_vb_of_file(file)
    target_version = version + 1
    os.makedirs(meta_path, exist_ok=True)
    if (
        (target_version > 0 and target_version % 10 == 0) or
        len(diff) > 10 or
        sum([d.count for d in diff if d.added is True or d.removed is True]) > 512
    ):
        # rebuild base
        target_base = target_version

        # save base file
        target_base_file = os.path.join(meta_path, f"b{target_base}")
        os.makedirs(meta_path, exist_ok=True)
        with open(target_base_file, "wb") as f:
            f.write(target_content.encode("utf-8"))
        # save version file
        vf = VersionFile(base=target_base, diff=[], create_time=f"{datetime.datetime.now()}")

    else:
        target_base = base
        vf = VersionFile(base=base, diff=diff, create_time=f"{datetime.datetime.now()}")

    with open(os.path.join(meta_path, f"v{target_version}"), "wb") as f:
        f.write(json.dumps(vf.dict()).encode("utf-8"))
    return target_version, target_base


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
        raise NotFound()

    dist_file = os.path.join(storage_root, email, rel_file_path)
    if not os.path.exists(share_meta) or not os.path.isfile(share_meta):
        raise ErrorWithPrompt("文件不存在")

    version, base = await _get_last_vb_of_file(dist_file)
    if version == 0:
        with open(dist_file, "rb") as f:
            content = f.read().decode("utf-8")
    else:
        version_file = os.path.join(f"{dist_file}.meta", f"v{version}")
        with open(version_file, "rb") as f:
            vf = VersionFile(**json.loads(f.read()))
        base_file = dist_file if vf.base == 0 else os.path.join(f"{dist_file}.meta", f"b{base}")
        with open(base_file, "rb") as f:
            base_content = f.read().decode("utf-8")
        content = merge_content(base_content, vf.diff)

    return content


async def get_original_file(email: str, file) -> Tuple[str, bytes]:
    dist_file = os.path.join(storage_root, email, file)
    if not os.path.isfile(dist_file):
        raise ErrorWithPrompt("文件不存在")

    mimetype, _ = mimetypes.guess_type(dist_file)
    with open(dist_file, "rb") as f:
        bin_content = f.read()
    return mimetype, bin_content
