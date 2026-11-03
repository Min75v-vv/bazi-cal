from datetime import date, datetime, timezone

from bazi_calendar.ics import AllDayEvent, build_calendar, escape_text, fold


def test_escape_text():
    assert escape_text("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"


def test_fold_respects_octets_and_utf8():
    line = "DESCRIPTION:" + "八字" * 60
    folded = fold(line)
    for part in folded.split("\r\n"):
        assert len(part.encode("utf-8")) <= 75
        part.encode("utf-8").decode("utf-8")  # 没有切断多字节字符
    # 去掉折行后还原
    assert folded.replace("\r\n ", "") == line


def test_fold_short_line_untouched():
    assert fold("VERSION:2.0") == "VERSION:2.0"


def test_calendar_structure():
    ev = AllDayEvent(date(2026, 12, 31), "吉｜正财日 · 宜祭祀", "第一行\n第二行", "20261231@x")
    ics = build_calendar([ev], "测试", now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert ics.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:")
    assert ics.endswith("END:VCALENDAR\r\n")
    assert "\n" not in ics.replace("\r\n", "")  # 只有 CRLF
    unfolded = ics.replace("\r\n ", "")
    assert "DTSTART;VALUE=DATE:20261231\r\n" in unfolded
    assert "DTEND;VALUE=DATE:20270101\r\n" in unfolded  # 跨年
    assert "DTSTAMP:20260101T000000Z\r\n" in unfolded
    assert "UID:20261231@x\r\n" in unfolded
    assert "DESCRIPTION:第一行\\n第二行\r\n" in unfolded
