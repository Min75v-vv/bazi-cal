"""每日格言：从 quotes.txt 里按日期固定地挑一句，作为日历事件的标题。"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

QUOTES_FILE = Path(__file__).with_name("quotes.txt")
# 打乱顺序用的固定种子：保证每月重新生成时同一天仍是同一句
SHUFFLE_SEED = "bazi-cal-quotes"


@dataclass(frozen=True)
class Quote:
    text: str      # 标题里显示的句子；非英文的外国名句这里是中文译文
    source: str
    original: str = ""  # 外文原文（有译文时才有），放在事件详情里

    def __str__(self) -> str:
        return f"{self.text} ——{self.source}" if self.source else self.text


def parse_quotes(content: str) -> list[Quote]:
    quotes = []
    for n, raw in enumerate(content.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        if not 2 <= len(parts) <= 3 or not parts[0] or (len(parts) == 3 and not parts[2]):
            raise ValueError(f"格言第 {n} 行格式应为「句子|出处」或「中文译文|出处|原文」：{raw!r}")
        quotes.append(Quote(*parts))
    if not quotes:
        raise ValueError("格言文件里没有句子")
    return quotes


@lru_cache(maxsize=None)
def load_quotes(path: Path = QUOTES_FILE) -> tuple[Quote, ...]:
    quotes = parse_quotes(path.read_text(encoding="utf-8"))
    # 原文件按出处分组，打乱后相邻几天不会都是同一本书
    random.Random(SHUFFLE_SEED).shuffle(quotes)
    return tuple(quotes)


def quote_for(day: date, quotes: tuple[Quote, ...] | None = None) -> Quote:
    """按日期轮转：句子数为 N 时，任意连续 N 天内不重复。"""
    quotes = quotes or load_quotes()
    return quotes[day.toordinal() % len(quotes)]
