"""读取并校验 config.yaml。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .ganzhi import WUXING

RELATION_KEYS = (
    "伏吟", "天克地冲", "天干五合", "天干相冲",
    "地支六冲", "地支六合", "地支半合", "地支拱合",
    "地支相刑", "地支自刑", "地支六害", "地支六破",
)


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
class Scoring:
    gan_xiyong: float
    gan_jishen: float
    zhi_xiyong: float
    zhi_jishen: float
    day_pillar: dict[str, float]
    year_pillar: dict[str, float]
    ji_min: float      # 总分 >= ji_min 为「吉」
    xiong_max: float   # 总分 <= xiong_max 为「凶」


@dataclass
class Config:
    birth: Birth
    xiyong: list[str]
    jishen: list[str]
    scoring: Scoring
    equation_of_time: bool = True
    zi_hour_sect: int = 1
    calendar_name: str = "八字趋吉避凶"
    calendar_timezone: str = "Asia/Shanghai"
    days: int = 365
    yiji_count: int = 2
    uid_domain: str = "rili-haoge.bazi"


def _check_wuxing(name: str, items: list[str]) -> list[str]:
    bad = [x for x in items if x not in WUXING]
    if bad:
        raise ValueError(f"{name} 只能是 木火土金水，发现: {bad}")
    return list(items)


def _relation_weights(name: str, raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    unknown = set(raw) - set(RELATION_KEYS)
    if unknown:
        raise ValueError(f"scoring.{name} 有未知关系: {sorted(unknown)}；可用: {RELATION_KEYS}")
    return {k: float(raw.get(k, 0)) for k in RELATION_KEYS}


def load_config(path: str | Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return parse_config(data)


def parse_config(data: dict) -> Config:
    b = data["birth"]
    birth = Birth(int(b["year"]), int(b["month"]), int(b["day"]), int(b["hour"]),
                  int(b.get("minute", 0)), float(b["longitude"]), b.get("timezone", "Asia/Shanghai"))
    xiyong = _check_wuxing("xiyong", data["xiyong"])
    jishen = _check_wuxing("jishen", data.get("jishen", []))
    if set(xiyong) & set(jishen):
        raise ValueError(f"喜用神与忌神重叠: {set(xiyong) & set(jishen)}")

    s = data["scoring"]
    w = s.get("wuxing", {})
    th = s["thresholds"]
    scoring = Scoring(
        gan_xiyong=float(w.get("gan_xiyong", 0)), gan_jishen=float(w.get("gan_jishen", 0)),
        zhi_xiyong=float(w.get("zhi_xiyong", 0)), zhi_jishen=float(w.get("zhi_jishen", 0)),
        day_pillar=_relation_weights("day_pillar", s.get("day_pillar")),
        year_pillar=_relation_weights("year_pillar", s.get("year_pillar")),
        ji_min=float(th["ji_min"]), xiong_max=float(th["xiong_max"]),
    )
    if scoring.xiong_max >= scoring.ji_min:
        raise ValueError("thresholds.xiong_max 必须小于 thresholds.ji_min")

    sect = int(data.get("zi_hour_sect", 1))
    if sect not in (1, 2):
        raise ValueError("zi_hour_sect 只能是 1 或 2")

    cal = data.get("calendar", {})
    return Config(
        birth=birth, xiyong=xiyong, jishen=jishen, scoring=scoring,
        equation_of_time=bool(data.get("true_solar_time", {}).get("equation_of_time", True)),
        zi_hour_sect=sect,
        calendar_name=cal.get("name", "八字趋吉避凶"),
        calendar_timezone=cal.get("timezone", "Asia/Shanghai"),
        days=int(cal.get("days", 365)),
        yiji_count=int(cal.get("yiji_count", 2)),
        uid_domain=cal.get("uid_domain", "rili-haoge.bazi"),
    )
