"""生成 bazi.ics：python -m bazi_calendar --config config.yaml --out public/bazi.ics"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import rules
from .chart import DayInfo, Natal, day_info, natal_chart
from .config import Config, load_config
from .ganzhi import ZHI_HIDE_GAN, pillar_relations, shishen, wuxing_of
from .ics import AllDayEvent, build_calendar


def _fmt(x: float) -> str:
    return f"{x:+g}"


def describe(info: DayInfo, natal: Natal, cfg: Config,
             items: list[rules.ScoreItem], score: float, lv: str) -> str:
    gz = info.ganzhi
    gan, zhi = gz[0], gz[1]
    gwx, zwx = wuxing_of(gan), wuxing_of(zhi)
    dm = natal.day_master
    hide = "、".join(f"{g}{shishen(dm, g)}" for g in ZHI_HIDE_GAN[zhi])

    def rel(natal_gz: str) -> str:
        return "、".join(pillar_relations(gz, natal_gz)) or "无"

    def roles(elem: str) -> str:
        return rules.wuxing_role(elem, cfg.xiyong, cfg.jishen)

    lines = [
        f"当日干支：{gz}日（{info.month_ganzhi}月 {info.year_ganzhi}年）",
        f"十神：天干{gan}为{shishen(dm, gan)}；地支{zhi}藏干 {hide}",
        f"与日柱{natal.day}：{rel(natal.day)}",
        f"与年柱{natal.year}：{rel(natal.year)}",
        "五行对喜用神的作用：",
        f"  天干{gan}{gwx}（{roles(gwx)}）：{'、'.join(rules.wuxing_effects(gwx, cfg.xiyong, cfg.jishen))}",
        f"  地支{zhi}{zwx}（{roles(zwx)}）：{'、'.join(rules.wuxing_effects(zwx, cfg.xiyong, cfg.jishen))}",
        f"评分：{score:g} → {lv}（≥{cfg.scoring.ji_min:g} 吉，≤{cfg.scoring.xiong_max:g} 凶）",
    ]
    lines += [f"  {_fmt(i.points)} {i.reason}" for i in items] or ["  无计分项"]
    lines += [
        f"黄历宜：{'、'.join(info.yi) or '无'}",
        f"黄历忌：{'、'.join(info.ji) or '无'}",
        f"命盘：{natal.year} {natal.month} {natal.day} {natal.time}"
        f"（日主{dm}，喜用{''.join(cfg.xiyong)}，忌{''.join(cfg.jishen) or '未设'}）",
    ]
    return "\n".join(lines)


def build_events(cfg: Config, natal: Natal, start: date, days: int) -> list[AllDayEvent]:
    events = []
    for k in range(days):
        info = day_info(start + timedelta(days=k))
        items = rules.score_day(info.ganzhi, natal.day, natal.year,
                                cfg.xiyong, cfg.jishen, cfg.scoring)
        score = rules.total(items)
        lv = rules.level(score, cfg.scoring.ji_min, cfg.scoring.xiong_max)
        summary = rules.title(lv, rules.shishen_day(natal.day_master, info.ganzhi),
                              rules.yiji_sentence(info.yi, info.ji, cfg.yiji_count))
        events.append(AllDayEvent(
            day=info.day, summary=summary,
            description=describe(info, natal, cfg, items, score, lv),
            uid=f"{info.day:%Y%m%d}@{cfg.uid_domain}",
        ))
    return events


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成个人八字趋吉避凶日历 (.ics)")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="public/bazi.ics")
    ap.add_argument("--start", help="起始日期 YYYY-MM-DD，默认为日历时区的今天")
    ap.add_argument("--days", type=int, help="天数，默认取 config 中 calendar.days")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    start = (date.fromisoformat(args.start) if args.start
             else datetime.now(ZoneInfo(cfg.calendar_timezone)).date())
    days = args.days or cfg.days
    natal = natal_chart(cfg)
    events = build_events(cfg, natal, start, days)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # newline="" 保证写出的是 CRLF 原样，不被平台换行转换
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write(build_calendar(events, cfg.calendar_name))

    print(f"命盘 {natal.year} {natal.month} {natal.day} {natal.time}，"
          f"真太阳时 {natal.solar_time:%Y-%m-%d %H:%M}")
    print(f"已生成 {len(events)} 天（{start} 起）→ {out}")
    return 0
