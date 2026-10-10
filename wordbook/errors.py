"""按词库记录每个词条的背诵错误次数。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from wordbook.storage import collection_dir


def _stats_path(book_name: str) -> Path:
    stem = book_name.strip()
    if stem.lower().endswith(".md"):
        stem = stem[:-3]
    return collection_dir() / f"{stem}.errors.json"


def _word_key(en: str, zh: str) -> str:
    return f"{en.strip()}\t{zh.strip()}"


def load_error_counts(book_name: str) -> Dict[str, int]:
    path = _stats_path(book_name)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: Dict[str, int] = {}
    for key, value in data.items():
        try:
            result[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return result


def save_error_counts(book_name: str, counts: Dict[str, int]) -> None:
    path = _stats_path(book_name)
    path.write_text(
        json.dumps(counts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_error_count(book_name: str, en: str, zh: str) -> int:
    return load_error_counts(book_name).get(_word_key(en, zh), 0)


def record_wrong(book_name: str, en: str, zh: str) -> int:
    """记错一次，返回累计错误次数。"""
    counts = load_error_counts(book_name)
    key = _word_key(en, zh)
    counts[key] = counts.get(key, 0) + 1
    save_error_counts(book_name, counts)
    return counts[key]
