import datetime
import json
import logging
import mimetypes
import os
import shutil
from pathlib import Path
from pydantic import BaseModel, BaseConfig
from typing import *
from src.framework.config import DEBUG, STORAGE_ROOT, BLOG_ROOT
from src import utils
from src.framework.error import ErrorWithPrompt, NotFound


storage_root = STORAGE_ROOT
"""
目录结构

STORAGE_ROOT
├── blog  (因为 blog 必须静态挂载)
│    ├── i@caoliang.net
│   ...   ├── version.txt
│         ├── xxx.html
│
├── i@caoliang.net
│    ├── auth
│    │    ├── pass.txt
│    │    └── tokens.txt
│    ├── storage
│    │    ├── readme.md (file)
│    │    ├── blog
│    │    ...
│    └── meta
│         ├── readme.md (dir)
│         │      ├── index.json
│         │      ├── v1
│         │      ├── b1
│         │      │
...       ...    ...
"""


def convert_datetime_to_realworld(dt: datetime.datetime) -> str:
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def convert_field_to_camel_case(string: str) -> str:
    return "".join(
        word if index == 0 else word.capitalize()
        for index, word in enumerate(string.split("_"))
    )


class RWModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")}


class DiffItem(RWModel):
    count: int
    added: bool = False
    removed: bool = False
    value: str = ""


class VersionBrief(RWModel):
    version: int
    base: int
    create_time: datetime.datetime
    lines: int = 0


IndexFileT = TypeVar("IndexFileT", bound="IndexFile")


class IndexFile(RWModel):
    versions: List[VersionBrief] = []

    @classmethod
    def parse_file(cls, file: str) -> IndexFileT:
        try:
            return super().parse_file(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return cls()


class VersionFile(RWModel):
    base: int
    diff: List[DiffItem] = []
    create_time: datetime.datetime


class FileLike(RWModel):
    id: Optional[str] = ""
    type: Optional[str] = ""
    text: Optional[str] = ""
    children: bool = True


class FileOpenRespData(RWModel):
    version: int
    base: int
    base_content: str
    diff: List[DiffItem] = []


class DiffResp(RWModel):
    last_version: int
    last_content: str
    current_version: int
    current_content: str


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
    dist = Path(STORAGE_ROOT) / email / "storage" / path.lstrip("/")
    dist.mkdir(parents=True, exist_ok=True)


async def listdir(email: str, path: str) -> List[FileLike]:
    user_storage_root = Path(STORAGE_ROOT) / email / "storage"
    curr_dir = user_storage_root / path.lstrip("/")
    if not curr_dir.exists():
        return []

    result: Dict[str, List[FileLike]] = {}
    for child in curr_dir.iterdir():
        if child.is_dir():
            filetype = "folder"
        elif child.is_file():
            if child.suffix:
                ext = child.suffix.lstrip(".")
                filetype = utils.get_file_type(ext)
            else:
                filetype = "bin"
        else:
            continue
        jstree_id = "/" + child.relative_to(user_storage_root).as_posix()
        this_item = FileLike(id=jstree_id, type=filetype, text=child.name, children=bool(filetype == "folder"))
        result.setdefault(filetype, []).append(this_item)

    # 排序，folder优先在上，其他的子类按名称排序
    return_data = []
    keys = sorted([k for k in result.keys() if k != "folder"])
    if "folder" in result:
        keys.insert(0, "folder")
    for key in keys:
        return_data.extend(sorted(result[key], key=lambda x: x.text))
    return return_data


async def rm(email: str, path: str):
    delete_path = Path(STORAGE_ROOT) / email / "storage" / path.lstrip("/")
    dist = str(delete_path)

    if not os.path.exists(dist):
        return
    if os.path.isdir(dist):
        shutil.rmtree(dist)
    elif os.path.isfile(dist):
        os.remove(dist)
        if os.path.exists(f"{dist}.meta"):
            shutil.rmtree(f"{dist}.meta")


async def rename(email: str, old_path: str, new_name: str):
    origin = Path(STORAGE_ROOT) / email / "storage" / old_path.lstrip("/")
    if not origin.exists():
        raise ErrorWithPrompt("路径不存在")
    new_path = origin.parent / new_name
    os.rename(str(origin), str(new_path))

    # 重命名meta
    if not new_path.is_file():
        return
    old_meta = Path(STORAGE_ROOT) / email / "meta" / old_path.lstrip("/")
    if not old_meta.exists():
        return
    new_meta = old_meta.parent / new_name
    logging.debug(f"rename old meta: {old_meta} => {new_meta}")
    os.rename(f"{old_meta}", f"{new_meta}")


def _get_file_by_version(email: str, file: str, version: int) -> FileOpenRespData:
    """
    通过 version 还原全量文件

    version <= 0 时，返回原文件。否则严格还原。

    Params
    ------
    version: int，必须存在，当其为 0 时，返回空。

    Returns
    -------
    content: str 全量内容
    """
    origin_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if version <= 0:
        try:
            content = origin_file.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            raise ErrorWithPrompt("文件不存在")
        return FileOpenRespData(version=0, base=0, base_content=content, diff=[])

    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    try:
        target_version = str(meta_path / f"v{version}")
        vf = VersionFile.parse_file(target_version)
    except FileNotFoundError:
        raise ErrorWithPrompt(f"文件版本({version})不存在")

    # 读取 base 文件
    base_file = meta_path / f"b{vf.base}"
    if not base_file.exists() or not base_file.is_file():
        raise ErrorWithPrompt(f"base（{vf.base}）文件不存在")

    try:
        base_content = base_file.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise ErrorWithPrompt("该版本源文件已不存在")

    return FileOpenRespData(version=version, base=vf.base, base_content=base_content, diff=vf.diff)


def _get_last_vb_of_file(email: str, file: str) -> Tuple[Optional[int], Optional[int]]:
    """
    当 version 或者 base file 不存在时，返回 0。

    Returns
    -------
    version: int
    base: int
    """
    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    index_file = meta_path / "index.json"
    last_version = 0
    last_base = 0

    try:
        index_f: IndexFile = IndexFile.parse_file(str(index_file))
    except FileNotFoundError:
        return 0, 0
    for v in index_f.versions:
        if v.base > last_base:
            last_base = v.base
        if v.version > last_version:
            last_version = v.version
    return last_version, last_base


def openfile(email: str, file: str, version: int = None) -> FileOpenRespData:
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
    dist = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if not dist.exists() or not dist.is_file():
        raise ErrorWithPrompt("文件不存在")

    logging.info(f"get version: {version}")
    if version is None:
        version, _ = _get_last_vb_of_file(email, file)

    logging.info(f"get last version: {version}")
    return _get_file_by_version(email, file, version)


async def create_file(email: str, file: str, content: Union[str, bytes] = None):
    """
    upload 和 new 接口会触发至此, 其他操作皆为更新文件
    1. 不允许覆盖
    2. 需要清除 meta 目录

    """
    dist_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if dist_file.exists() and dist_file.is_file():
        raise ErrorWithPrompt("文件已存在")

    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    if meta_path.exists():
        shutil.rmtree(str(meta_path))

    dist_file.parent.mkdir(exist_ok=True, parents=True)
    dist_file.touch(exist_ok=True)
    if not content:
        return

    if isinstance(content, str):
        bin_content = content.encode("utf-8", errors="replace")
    else:
        bin_content = content
    dist_file.write_bytes(bin_content)


async def savefile(email: str, file: str, content: Union[str, bytes]) -> Tuple[int, int]:
    """
    全量保存文件
    1. 读取原文件，如果内容与上报的相同，则不保存。取该文件的 base 和 version 返回
    1. 寻找最新 version 和 base，创建 base，并根据该 base 创建 version

    Returns
    -------
    version: int 版本号
    base: int base
    """
    # 保存的 API 不再触发到这里，获取文件之时，即获取了 version 、 base（首版均为0）。
    # 函数的实现没有问题。但后续更新皆基于 delta, 因此在此处加日志以记录，不在执行此逻辑
    if datetime.datetime.now().year >= 2025:
        logging.error(f"does not support save file all range. email: {email}, file: {file}")
        raise ErrorWithPrompt("不再支持此操作！")

    dist_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if not dist_file.exists() or not dist_file.is_file():
        raise ErrorWithPrompt("文件不存在")

    version, base = _get_last_vb_of_file(email, file)
    fr: FileOpenRespData = _get_file_by_version(email, file, version)
    old_content = merge_content(base_content=fr.base_content, diff=fr.diff)

    # 检查内容是否有改变
    new_content = content.encode(encoding="utf-8", errors="replace") if isinstance(content, str) else content
    if new_content == (old_content.encode("utf-8")):
        logging.debug("content not change")
        return fr.version, fr.base
    dist_file.write_bytes(new_content)

    # 创建
    # 寻找最新版本
    target_version, target_base = fr.version + 1, fr.base + 1

    # 创建base
    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    meta_path.mkdir(exist_ok=True, parents=True)
    base_file = meta_path / f"b{target_base}"
    base_file.touch(exist_ok=True)
    base_file.write_bytes(new_content)

    # 创建version
    now = datetime.datetime.now()
    version_data = VersionFile(base=target_base, create_time=now)
    version_file = meta_path / f"v{target_version}"
    version_file.touch(exist_ok=True)
    version_file.write_bytes(version_data.json(ensure_ascii=False).encode("utf-8"))

    # 更新 index
    index_file = meta_path / "index.json"
    index_f: IndexFile = IndexFile.parse_file(str(index_file))
    index_f.versions.append(VersionBrief(version=target_version, base=target_base, create_time=now))
    index_file.write_bytes(index_f.json(ensure_ascii=False).encode("utf-8"))
    return target_version, target_base


async def savefile_delta(email: str, file: str, base: int, dist_md5: str, diff: List[DiffItem]) -> Tuple[int, int]:
    """
    增量保存文件
    参数中 dist_md5 是原文件的全量的 md5。由于源文件会一直改变，因此 base0 不可以代表原文件。

    1. 获取原始 base
    2. 根据 diff 生成目标内容
    3. 判断 md5 是否一致
    4. 存储 version 文件，（如果与base差距过大，重新分配base）（取最大version）
    4. 将 version 和 base 返回

    # 当 diff 过大，不值得保存增量文件时，重新生成 base，并基于新 base 生成 version

    Returns
    -------
    version: int 版本号, 存储系统里最新的版本号
    base: int, rebuild 之后的 base
    """
    origin_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    meta_path.mkdir(exist_ok=True, parents=True)

    try:
        if base == 0:
            base_content = origin_file.read_text(encoding="utf-8", errors="replace")
        else:
            base_file = meta_path / f"b{base}"
            base_content = base_file.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise ErrorWithPrompt("无法读取 base 内容")

    target_content = merge_content(base_content, diff)
    result_md5 = utils.calc_md5(target_content)
    if result_md5 != dist_md5:
        raise ErrorWithPrompt("文件不一致")

    # 读取原文件内容，若无改变，则不保存
    version, max_base = _get_last_vb_of_file(email, file)
    fr: FileOpenRespData = _get_file_by_version(email, file, version)
    old_content = merge_content(base_content=fr.base_content, diff=fr.diff)
    old_md5 = utils.calc_md5(old_content)
    if old_md5 == dist_md5:
        logging.debug(f"on save content delta, md5 not change. file: \n\t{file}")
        return version, max_base
    # 更新原文件
    origin_file.write_bytes(target_content.encode("utf-8", errors="replace"))

    # 更新base文件
    target_version = version + 1
    now = datetime.datetime.now()
    if (
        base == 0 or
        (target_version > 0 and target_version % 10 == 0) or
        len(diff) > 10 or
        sum([d.count for d in diff if d.added is True or d.removed is True]) > 512
    ):  # 这一步是在有较大改动的时候，重新派生出 base

        # rebuild base
        target_base = target_version

        # save base file
        target_base_file = meta_path / f"b{target_base}"
        target_base_file.touch(exist_ok=True)
        target_base_file.write_bytes(target_content.encode("utf-8"))
        vf = VersionFile(base=target_base, diff=[], create_time=now)

    else:
        target_base = base
        vf = VersionFile(base=base, diff=diff, create_time=now)

    # 更新version文件
    version_file = meta_path / f"v{target_version}"
    version_file.touch(exist_ok=True)
    version_file.write_bytes(vf.json(ensure_ascii=False).encode("utf-8"))

    # 更新 index file
    index_file = meta_path / "index.json"
    index_file.touch(exist_ok=True)
    index_f: IndexFile = IndexFile.parse_file(str(index_file))
    index_f.versions.append(VersionBrief(
        version=target_version, base=target_base, create_time=now,
        lines=len([d for d in diff if d.added is True or d.removed is True])
    ))
    index_file.write_bytes(index_f.json(ensure_ascii=False).encode("utf-8"))

    return target_version, target_base


async def create_share(email: str, file: str):
    """创建文件分享"""
    dist_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if not dist_file.exists() or not dist_file.is_file():
        raise ErrorWithPrompt("文件不存在")

    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    meta_path.mkdir(exist_ok=True, parents=True)
    share_file = meta_path / "share"
    share_file.touch(exist_ok=True)
    return True


async def get_share(email: str, file: str) -> Tuple[str, Union[str, bytes]]:
    """

    Returns
    -------
    mimetype: str, 文件类型
    content: str or bytes, 文件内容
    """
    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    share_flag = meta_path / "share"
    if not share_flag.exists() or not share_flag.exists():
        raise NotFound()

    dist_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    mimetype, _ = mimetypes.guess_type(str(dist_file))
    if isinstance(mimetype, str) and mimetype.startswith("image/"):
        bin_content = dist_file.read_bytes()
        return mimetype, bin_content

    version, base = _get_last_vb_of_file(email, file)
    if version == 0:
        content = dist_file.read_text(encoding="utf-8", errors="replace")
        return mimetype or "", content

    version_file = meta_path / f"v{version}"
    vf = VersionFile(**json.loads(version_file.read_bytes()))
    base_file = dist_file if vf.base == 0 else (meta_path / f"v{base}")
    base_content = base_file.read_text(encoding="utf-8", errors="replace")
    content = merge_content(base_content, vf.diff)
    return mimetype or "", content


async def get_original_file(email: str, file: str) -> Tuple[str, bytes]:
    dist_file = Path(STORAGE_ROOT) / email / "storage" / file.lstrip("/")
    if not dist_file.exists():
        raise NotFound()

    mimetype, _ = mimetypes.guess_type(str(dist_file))
    return mimetype, dist_file.read_bytes()


async def get_history(email: str, file: str) -> List[VersionBrief]:
    index_file = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/") / "index.json"
    try:
        data: IndexFile = IndexFile.parse_file(str(index_file))
    except FileNotFoundError:
        raise ErrorWithPrompt("没有版本历史")
    return sorted(data.versions, key=lambda x: x.version, reverse=True)


async def get_diff(email: str, file: str, version: int) -> DiffResp:
    meta_path = Path(STORAGE_ROOT) / email / "meta" / file.lstrip("/")
    index_file = meta_path / "index.json"
    index_data: IndexFile = IndexFile.parse_file(str(index_file))

    version_map: Dict[int, VersionBrief] = {v.version: v for v in index_data.versions}
    # 寻找比当前版本稍小一个版本的 version 和 base
    last_version = version - 1
    while last_version > 0:
        if last_version in version_map:
            break
        last_version -= 1

    # 读取旧文件
    r = _get_file_by_version(email, file, last_version)
    last_content = merge_content(r.base_content, r.diff)

    # 读取新文件
    r = _get_file_by_version(email, file, version)
    cur_content = merge_content(r.base_content, r.diff)

    return DiffResp(
        last_version=last_version,
        last_content=last_content,
        current_version=version,
        current_content=cur_content,
    )


async def get_blog_version(email: str) -> str:
    user, service = email.split("@", 1)
    blog_ver_file = Path(BLOG_ROOT) / user / service / "version.txt"
    try:
        return blog_ver_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


# for auth
async def get_encrypted_password(email: str) -> str:
    dist_file = Path(STORAGE_ROOT) / email / "auth" / "pass.txt"
    try:
        return dist_file.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


async def set_encrypted_password(email: str, token: str) -> None:
    dist_file = Path(STORAGE_ROOT) / email / "auth" / "pass.txt"
    dist_file.parent.mkdir(parents=True, exist_ok=True)
    dist_file.touch(exist_ok=True)
    dist_file.write_text(token, encoding="utf-8")


async def add_user_token(email: str, token: str) -> None:
    """
    将 token 追加到用户文件中，如果文件超过 100KB，则清理最久远的

    """
    token_file = Path(STORAGE_ROOT) / email / "auth" / "tokens.txt"
    token_file.parent.mkdir(exist_ok=True)
    token_file.touch(exist_ok=True)

    old = token_file.read_text(encoding="utf-8", errors="replace")
    token_list = [a for a in old.split("\n") if a.strip()]
    new_content = "\n".join(token_list[-9:] + [token])

    token_file.write_text(new_content, encoding="utf-8")


async def delete_user_token(email: str, token: str) -> None:
    tokens_file = Path(STORAGE_ROOT) / email / "auth" / "tokens.txt"
    tokens_file.parent.mkdir(exist_ok=True)
    if not tokens_file.exists():
        return

    content = tokens_file.read_text(encoding="utf-8")
    token_list = content.split("\n")
    new_content = "\n".join([t for t in token_list if t != token])
    tokens_file.write_text(new_content, encoding="utf-8")


async def delete_all_user_token(email: str) -> None:
    tokens_file = Path(STORAGE_ROOT) / email / "auth" / "tokens.txt"
    tokens_file.write_text("")


async def load_user_token(email: str) -> List[str]:
    token_file = Path(STORAGE_ROOT) / email / "auth" / "tokens.txt"
    if not token_file.exists():
        return []
    return token_file.read_text(encoding="utf-8").split("\n")
