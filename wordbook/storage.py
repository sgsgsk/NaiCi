"""词库目录与 Markdown 读写。"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

WordPair = Tuple[str, str]

INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
TABLE_ROW = re.compile(
    r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|?\s*$"
)

RECORDS_DIR_NAME = "记录文件"


def _is_writable_dir(path: Path) -> bool:
    """检测目录是否可创建文件（避免在受保护路径下要求管理员）。"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test_tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def app_base_dir() -> Path:
    """
    运行目录：
    - 开发：项目下「发布」
    - 打包：优先 exe 同级；若不可写（如装在系统目录），回退到用户目录
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if _is_writable_dir(exe_dir):
            return exe_dir
        # 不要求管理员：回退到可写用户目录
        fallback = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "背诵单词"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    project_root = Path(__file__).resolve().parent.parent
    release_dir = project_root / "发布"
    release_dir.mkdir(parents=True, exist_ok=True)
    return release_dir


def collection_dir() -> Path:
    path = app_base_dir() / RECORDS_DIR_NAME
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        # 最后兜底：临时目录旁的用户文档
        fallback = Path.home() / "Documents" / "背诵单词" / RECORDS_DIR_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def list_wordbooks() -> List[str]:
    """返回词库显示名（不含 .md）。"""
    folder = collection_dir()
    names = sorted(p.stem for p in folder.glob("*.md") if p.is_file())
    return names


def wordbook_path(display_name: str) -> Path:
    name = display_name.strip()
    if name.lower().endswith(".md"):
        name = name[:-3]
    return collection_dir() / f"{name}.md"


def sanitize_filename(name: str) -> Tuple[str | None, str | None]:
    """返回 (合法文件名不含扩展名, 错误信息)。"""
    raw = name.strip()
    if raw.lower().endswith(".md"):
        raw = raw[:-3].strip()
    if not raw:
        return None, "文件名不能为空"
    if INVALID_FILENAME_CHARS.search(raw) or raw in {".", ".."}:
        return None, '文件名不能包含 \\ / : * ? " < > |'
    return raw, None


def parse_markdown_table(text: str) -> List[WordPair]:
    pairs: List[WordPair] = []
    lines = text.splitlines()
    seen_header = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-{3,}:?\s*\|", stripped):
            continue
        match = TABLE_ROW.match(stripped)
        if not match:
            continue
        left, right = match.group(1).strip(), match.group(2).strip()
        if not seen_header:
            if left == "英文" and right == "中文":
                seen_header = True
            continue
        if left and right:
            pairs.append((left, right))
    return pairs


def load_wordbook(display_name: str) -> List[WordPair] | None:
    path = wordbook_path(display_name)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return parse_markdown_table(text)


def save_wordbook(display_name: str, pairs: List[WordPair]) -> Path:
    stem, err = sanitize_filename(display_name)
    if err or stem is None:
        raise ValueError(err or "文件名无效")
    path = wordbook_path(stem)
    lines = [
        f"# {stem}",
        "",
        "| 英文 | 中文 |",
        "|------|------|",
    ]
    for en, zh in pairs:
        lines.append(f"| {en} | {zh} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
