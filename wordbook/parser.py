"""录入纯文本：区分英文 / 中文片段并配对。"""

from __future__ import annotations

import re
from typing import List, Tuple

WordPair = Tuple[str, str]

EN_TOKEN = re.compile(
    r"[A-Za-z0-9]+(?:[\s'\-./]*[A-Za-z0-9]+)*"
)
ZH_TOKEN = re.compile(
    r"[\u4e00-\u9fff]+(?:[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]*)*"
)


def extract_segments(text: str) -> List[Tuple[str, str]]:
    """返回 [(kind, value), ...]，kind 为 en 或 zh，按出现顺序。"""
    segments: List[Tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        en = EN_TOKEN.match(text, i)
        zh = ZH_TOKEN.match(text, i)
        candidates = []
        if en:
            candidates.append(("en", en))
        if zh:
            candidates.append(("zh", zh))
        if not candidates:
            i += 1
            continue
        kind, match = max(candidates, key=lambda item: item[1].end() - item[1].start())
        value = match.group(0).strip()
        if value:
            segments.append((kind, value))
        i = match.end()
    return segments


def parse_input_text(text: str) -> Tuple[List[WordPair], int]:
    """
    按出现顺序将英中片段两两配对。
    返回 (词条列表, 落单忽略数量)。
    """
    segments = extract_segments(text)
    pairs: List[WordPair] = []
    pending_en: str | None = None
    ignored = 0

    for kind, value in segments:
        if kind == "en":
            if pending_en is not None:
                ignored += 1
            pending_en = value
        else:
            if pending_en is not None:
                pairs.append((pending_en, value))
                pending_en = None
            else:
                ignored += 1

    if pending_en is not None:
        ignored += 1

    return pairs, ignored


def normalize_english(s: str) -> str:
    return s.strip().casefold()


def normalize_chinese(s: str) -> str:
    return s.strip()


def match_english(answer: str, expected: str) -> bool:
    return normalize_english(answer) == normalize_english(expected)


def match_chinese(answer: str, expected: str) -> bool:
    return normalize_chinese(answer) == normalize_chinese(expected)
