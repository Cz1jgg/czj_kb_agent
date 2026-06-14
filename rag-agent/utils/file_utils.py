"""
文件工具函数：路径拼接、目录创建、文件类型判断等
"""
import os
import shutil
import uuid
from typing import Optional


SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".txt", ".md"}


def ensure_dir(path: str) -> str:
    """确保目录存在，不存在则创建。"""
    os.makedirs(path, exist_ok=True)
    return path


def project_root() -> str:
    """返回项目根目录（当前文件所在路径的上一级）。"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def abs_path(relative: str) -> str:
    """相对路径 -> 绝对路径（基于项目根目录）。"""
    return os.path.join(project_root(), relative)


def is_supported(filename: str) -> bool:
    """根据扩展名判断是否为可解析的文档。"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTS


def save_bytes_to_dir(content: bytes, filename: str, target_dir: str) -> str:
    """将字节内容保存到目标目录，返回最终路径。"""
    ensure_dir(target_dir)
    target = os.path.join(target_dir, filename)
    with open(target, "wb") as f:
        f.write(content)
    return target


def unique_filename(filename: str) -> str:
    """生成带 UUID 的唯一文件名，保留原扩展名。"""
    base, ext = os.path.splitext(filename)
    return f"{base}_{uuid.uuid4().hex[:8]}{ext}"


def list_files(directory: str, suffixes: Optional[set] = None) -> list:
    """列出目录下指定后缀的文件。"""
    if not os.path.isdir(directory):
        return []
    files = []
    for name in os.listdir(directory):
        full = os.path.join(directory, name)
        if not os.path.isfile(full):
            continue
        if suffixes and os.path.splitext(name)[1].lower() not in suffixes:
            continue
        files.append(full)
    return files


def remove_file(path: str) -> bool:
    """删除单个文件。"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError:
        return False
    return False


def remove_dir(path: str) -> bool:
    """递归删除目录。"""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return True
    except OSError:
        return False
    return False


def file_size(path: str) -> int:
    """返回文件字节大小，不存在则返回 0。"""
    if not os.path.isfile(path):
        return 0
    return os.path.getsize(path)
