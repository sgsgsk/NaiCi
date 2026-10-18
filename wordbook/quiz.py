"""选择题：从当前词库随机抽取干扰项。"""

from __future__ import annotations

import random
from typing import List, Sequence, Tuple

WordPair = Tuple[str, str]


def build_zh_choices(
    pairs: Sequence[WordPair],
    index: int,
    count: int = 4,
) -> List[str] | None:
    """
    生成 count 个中文选项，包含 pairs[index] 的正确答案，其余从词库随机抽取。
    词库可用中文释义不足时返回 None。
    """
    if not pairs or index < 0 or index >= len(pairs):
        return None

    correct_zh = pairs[index][1].strip()
    if not correct_zh:
        return None

    # 其他词条的中文（去重，排除正确答案）
    others: List[str] = []
    seen = {correct_zh}
    for i, (_en, zh) in enumerate(pairs):
        if i == index:
            continue
        text = zh.strip()
        if text and text not in seen:
            seen.add(text)
            others.append(text)

    need = count - 1
    if len(others) < need:
        return None

    distractors = random.sample(others, need)
    choices = distractors + [correct_zh]
    random.shuffle(choices)
    return choices
