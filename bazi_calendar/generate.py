"""生成 bazi.ics：python -m bazi_calendar --config config.yaml --out public/bazi.ics"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import rules
from .chart import DayInfo, Natal, day_info, natal_chart
from .config import Config, load_config
from .ganzhi import WUXING, ZHI_HIDE_GAN, pillar_relations, shishen, wuxing_effect, wuxing_of
from .ics import AllDayEvent, build_calendar

# 事件 UID 的域名部分；固定值，保证每月重新生成时同一天的 UID 不变
UID_DOMAIN = "bazi-cal"


def tier_wuxing(shen: dict[str, list[str]], day_master: str) -> dict[str, list[str]]:
    """把规范化后的四维用神换算回五行，用于描述「五行对用神的作用」。"""
    out: dict[str, list[str]] = {}
    for tier in (rules.YONG, rules.XI, rules.JI, rules.CHOU):
        elems = []
        for e in WUXING:
            pair = rules.wuxing_shishen_pair(e, day_master)
            if any(rules.shishen_tier(s, shen) == tier for s in pair):
                elems.append(e)
        out[tier] = elems
    return out


def describe(info: DayInfo, natal: Natal, shen: dict[str, list[str]], sc: rules.DailyScore) -> str:
    gz = info.ganzhi
    gan, zhi = gz[0], gz[1]
    dm = natal.day_master
    hide = "、".join(f"{g}{shishen(dm, g)}" for g in ZHI_HIDE_GAN[zhi])
    tw = tier_wuxing(shen, dm)

    def rel(natal_gz: str) -> str:
        return "、".join(pillar_relations(gz, natal_gz)) or "无"

    def effects(elem: str) -> str:
        parts = [f"{wuxing_effect(elem, t)}{rules.TIER_LABELS[tier]}{t}"
                 for tier, elems in tw.items() for t in elems]
        return "、".join(parts) or "未设用神"

    lines = [
        f"当日干支：{gz}日（{info.month_ganzhi}月 {info.year_ganzhi}年），建除「{info.zhixing}」",
        f"十神：天干{gan}为{shishen(dm, gan)}；地支{zhi}藏干 {hide}",
        f"与日柱{natal.day}：{rel(natal.day)}",
        f"与月柱{natal.month}：{rel(natal.month)}",
        f"与年柱{natal.year}：{rel(natal.year)}",
        "五行对用神的作用：",
        f"  天干{gan}{wuxing_of(gan)}：{effects(wuxing_of(gan))}",
        f"  地支{zhi}{wuxing_of(zhi)}：{effects(wuxing_of(zhi))}",
        # 等级字（优/良/平/注意/慎行）只出现在标题和下面的搜索词里，
        # 避免日历 App 搜索时误命中其它日子
        f"评分：{sc.final} ＝ 基础 {rules.BASE_SCORE}",
    ]
    lines += [f"  {i.points:+d} {i.reason}" for i in sc.items]
    if sc.is_kongwang:
        lines.append(f"  空亡：{zhi}落日柱旬空{natal.day_xunkong}，各项合计 ×{rules.KONGWANG_FACTOR}")
    if sc.final != sc.raw_total and not sc.is_kongwang:
        lines.append(f"  原始分 {sc.raw_total}，限定在 {rules.SCORE_MIN}–{rules.SCORE_MAX}")
    lines += [
        f"黄历宜：{'、'.join(info.yi) or '无'}",
        f"黄历忌：{'、'.join(info.ji) or '无'}",
        f"命盘：{natal.year} {natal.month} {natal.day} {natal.time}（日主{dm}，日柱旬空{natal.day_xunkong}）",
        "用神：" + "；".join(f"{rules.TIER_LABELS[t]} {'、'.join(shen[t]) or '无'}"
                          for t in (rules.YONG, rules.XI, rules.JI, rules.CHOU)),
        f"搜索词：{search_tag(sc.level)}",
    ]
    return "\n".join(lines)


def search_tag(level: str) -> str:
    """日历 App 里按等级搜索用的关键词，如「优日」。单字「平」会撞上建除「平」与黄历「平治道涂」，
    所以统一加「日」字。"""
    return f"{level}日"


def score_for(info: DayInfo, natal: Natal, shen: dict[str, list[str]]) -> rules.DailyScore:
    return rules.score_day(
        info.ganzhi, info.zhixing, info.year_ganzhi[1], info.month_ganzhi[1],
        natal.day_master, natal.day[1], natal.month[1], natal.year[1],
        natal.day_xunkong, shen)


def build_events(cfg: Config, natal: Natal, start: date, days: int) -> list[AllDayEvent]:
    shen = rules.normalize_shen(cfg.shen, natal.day_master)
    events = []
    for k in range(days):
        info = day_info(start + timedelta(days=k))
        sc = score_for(info, natal, shen)
        summary = rules.title(sc.level, rules.shishen_day(natal.day_master, info.ganzhi),
                              rules.yiji_sentence(info.yi, info.ji, cfg.yiji_count))
        events.append(AllDayEvent(
            day=info.day, summary=summary,
            description=describe(info, natal, shen, sc),
            uid=f"{info.day:%Y%m%d}@{UID_DOMAIN}",
        ))
    return events


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成个人八字趋吉避凶日历 (.ics)")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="public/bazi.ics")
    ap.add_argument("--start", help="起始日期 YYYY-MM-DD，默认为日历时区的今天")
    ap.add_argument("--days", type=int, help="天数，默认取 config 中 calendar.days")
    ap.add_argument("--show-chart", action="store_true",
                    help="打印命盘与真太阳时（仅本地使用；公开仓库的 CI 日志任何人可见，切勿开启）")
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

    if args.show_chart:
        print(f"命盘 {natal.year} {natal.month} {natal.day} {natal.time}，"
              f"真太阳时 {natal.solar_time:%Y-%m-%d %H:%M}")
    print(f"已生成 {len(events)} 天 → {out}")
    return 0
