"""读取并校验 config.yaml。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

SHEN_KEYS = ("yong", "xi", "ji", "chou")


@dataclass
class Birth:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    longitude: float
    timezone: str = "Asia/Shanghai"


@dataclass
class Config:
    birth: Birth
    # 四维用神原始输入：{'yong': [...], 'xi': [...], 'ji': [...], 'chou': [...]}
    # 由 rules.normalize_shen 结合日主规范化
    shen: dict[str, list[str]] = field(default_factory=dict)
    equation_of_time: bool = True
    zi_hour_sect: int = 1
    calendar_name: str = "八字趋吉避凶"
    calendar_timezone: str = "Asia/Shanghai"
    days: int = 365
    yiji_count: int = 2
    uid_domain: str = "rili-haoge.bazi"


def _str_list(name: str, val) -> list[str]:
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
        raise ValueError(f"shen.{name} 必须是字符串列表")
    return list(val)


def load_config(path: str | Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return parse_config(data)


def parse_config(data: dict) -> Config:
    b = data["birth"]
    birth = Birth(int(b["year"]), int(b["month"]), int(b["day"]), int(b["hour"]),
                  int(b.get("minute", 0)), float(b["longitude"]), b.get("timezone", "Asia/Shanghai"))

    raw_shen = data.get("shen") or {}
    unknown = set(raw_shen) - set(SHEN_KEYS)
    if unknown:
        raise ValueError(f"shen 只能包含 {SHEN_KEYS}，发现: {sorted(unknown)}")
    shen = {k: _str_list(k, raw_shen.get(k)) for k in SHEN_KEYS}
    if not shen["yong"]:
        raise ValueError("shen.yong（用神）至少要写一项")

    sect = int(data.get("zi_hour_sect", 1))
    if sect not in (1, 2):
        raise ValueError("zi_hour_sect 只能是 1 或 2")

    cal = data.get("calendar", {})
    return Config(
        birth=birth, shen=shen,
        equation_of_time=bool(data.get("true_solar_time", {}).get("equation_of_time", True)),
        zi_hour_sect=sect,
        calendar_name=cal.get("name", "八字趋吉避凶"),
        calendar_timezone=cal.get("timezone", "Asia/Shanghai"),
        days=int(cal.get("days", 365)),
        yiji_count=int(cal.get("yiji_count", 2)),
        uid_domain=cal.get("uid_domain", "rili-haoge.bazi"),
    )
