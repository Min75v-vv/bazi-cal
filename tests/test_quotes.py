from datetime import date, timedelta

import pytest

from bazi_calendar.quotes import Quote, load_quotes, parse_quotes, quote_for


def test_enough_quotes_for_a_year_without_repeats():
    quotes = load_quotes()
    assert len(quotes) >= 366
    assert len({q.text for q in quotes}) == len(quotes), "格言有重复"
    start = date(2027, 3, 1)
    year = [quote_for(start + timedelta(days=k)) for k in range(366)]
    assert len(set(year)) == 366


def test_same_day_same_quote():
    assert quote_for(date(2027, 1, 1)) == quote_for(date(2027, 1, 1))
    assert quote_for(date(2027, 1, 1)) != quote_for(date(2027, 1, 2))


def test_quotes_do_not_break_level_search():
    # 日历 App 按「优日」「注意日」等搜索时，格言不能误命中
    banned = ("优", "良", "注意", "慎行", "平日", "｜")
    for q in load_quotes():
        assert not any(b in str(q) + q.original for b in banned), q


def test_non_english_quotes_have_chinese_title():
    # 标题只允许中文或英文：其他外语必须写成「中文译文|出处|原文」
    import re
    for q in load_quotes():
        if re.search(r"[A-Za-z]", q.text):
            assert q.text.isascii() or all(c in "’—" for c in q.text if not c.isascii()), q
            assert not q.original, q
        if q.original:
            assert re.search(r"[\u4e00-\u9fff]", q.text), q


def test_quote_str():
    assert str(Quote("吾日三省吾身", "《论语》")) == "吾日三省吾身 ——《论语》"
    assert str(Quote("吃一堑，长一智", "")) == "吃一堑，长一智"


def test_parse_quotes():
    assert parse_quotes("# 注释\n\n甲|乙\n丙|\n译文|出处|Original\n") == [
        Quote("甲", "乙"), Quote("丙", ""), Quote("译文", "出处", "Original")]
    with pytest.raises(ValueError):
        parse_quotes("译文|出处|")
    with pytest.raises(ValueError):
        parse_quotes("a|b|c|d")
    with pytest.raises(ValueError):
        parse_quotes("没有分隔符")
    with pytest.raises(ValueError):
        parse_quotes("# 只有注释\n")
