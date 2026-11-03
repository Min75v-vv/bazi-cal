"""最小但符合 RFC 5545 的 iCalendar 写出器（只用到全天 VEVENT）。

要点：CRLF 换行；每行不超过 75 个八位字节，超出用 CRLF+空格折行且不切断 UTF-8 字符；
TEXT 值转义 \\ ; , 和换行；全天事件用 VALUE=DATE，DTEND 为次日（不含）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

CRLF = "\r\n"


def escape_text(value: str) -> str:
    return (value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def fold(line: str, limit: int = 75) -> str:
    """按八位字节折行（RFC 5545 §3.1）。续行以一个空格开头，空格计入该行长度。"""
    out, cur, cur_len = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        max_len = limit if not out else limit - 1
        if cur_len + n > max_len:
            out.append(cur)
            cur, cur_len = "", 0
        cur += ch
        cur_len += n
    out.append(cur)
    return (CRLF + " ").join(out)


@dataclass
class AllDayEvent:
    day: date
    summary: str
    description: str
    uid: str


def build_calendar(events: list[AllDayEvent], cal_name: str,
                   now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//bazi-cal//bazi-calendar//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text(cal_name)}",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    for ev in events:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ev.uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{ev.day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{ev.day + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{escape_text(ev.summary)}",
            f"DESCRIPTION:{escape_text(ev.description)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "".join(fold(line) + CRLF for line in lines)
