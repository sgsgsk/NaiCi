"""选择题选项生成自测。"""

from wordbook.quiz import build_zh_choices


def test_four_choices_include_correct():
    pairs = [
        ("apple", "苹果"),
        ("banana", "香蕉"),
        ("cat", "猫"),
        ("dog", "狗"),
        ("egg", "鸡蛋"),
    ]
    for i in range(len(pairs)):
        choices = build_zh_choices(pairs, i, count=4)
        assert choices is not None
        assert len(choices) == 4
        assert len(set(choices)) == 4
        assert pairs[i][1] in choices


def test_too_few_returns_none():
    pairs = [("a", "甲"), ("b", "乙"), ("c", "丙")]
    assert build_zh_choices(pairs, 0, count=4) is None


if __name__ == "__main__":
    test_four_choices_include_correct()
    test_too_few_returns_none()
    print("ok")
