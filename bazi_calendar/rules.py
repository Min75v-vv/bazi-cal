"""每日评分规则 —— 移植自 oceanjustinlin/qimen 的 lib/calculateDailyScore.js 与
lib/normalizeShenProfile.js（commit ddb61cb，MIT License, Copyright (c) 2026 oceanjustinlin）。

全部是纯函数，便于单测。与原实现一致的部分：
- 基础分 70，最终分限定在 45–98；分五档：≥85 优、≥70 良、≥60 平、≥50 注意、<50 慎行。
- 维度 1：流日天干十神按四维用神分层：用神 +10、喜神 +6、闲神 0、仇神 −5、忌神 −8。
- 维度 2：流日地支与命局日/月/年支——
    三刑成立则熔断，维度 2 固定 −15，不再看其它关系；否则累加：
    冲日支 −10、冲月支 −8、冲年支 −4；流日地支与日支相同（伏吟）−2；
    害日支或年支 −4（只计一次）；
    与日支或年支六合（只计一次）、与日/月/年支任一组成三合（只计一次），
    按合化五行对日主的十神层级计分：用神 +6、喜神 +4、闲神 +1、仇神 −4、忌神 −5。
- 维度 3：建除十二神：成开 +10；定执除满 +4；平危收 0；建破闭 −10。
- 空亡：维度 1–3 合计 ×0.7 向下取整。

经使用者确认后与原实现不同的两处：
- 三刑：原实现只要「流日地支 + 命局地支」凑齐就触发，命局自带子卯等会天天触发；
  这里要求流日地支本身是组成该刑的字之一。
- 空亡：原实现判断「流日地支是否在当日旬空」，这在数学上永远为假；
  这里改为判断流日地支是否落在命主日柱的旬空内，且未被当日年支/月支填实。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .ganzhi import GAN, WUXING, ke, sheng, shishen, wuxing_of

# ---------- 四维用神 ----------
YONG, XI, XIAN, CHOU, JI = "yong", "xi", "xian", "chou", "ji"
TIER_LABELS = {YONG: "用神", XI: "喜神", XIAN: "闲神", CHOU: "仇神", JI: "忌神"}
TIER_INPUT_ORDER = (YONG, XI, JI, CHOU)  # 冲突时高层优先，与原实现相同

SHISHEN_ALIASES = {
    "印星": ("正印", "偏印"),
    "比劫": ("比肩", "劫财"),
    "官杀": ("正官", "七杀"),
    "食伤": ("食神", "伤官"),
    "财星": ("正财", "偏财"),
}
ALL_SHISHEN = {s for pair in SHISHEN_ALIASES.values() for s in pair}


def wuxing_to_category(elem: str, day_master: str) -> str:
    """五行相对日主属于哪一类十神，如 日主乙、水 → '印星'。"""
    me = wuxing_of(day_master)
    if elem == me:
        return "比劫"
    if sheng(elem, me):
        return "印星"
    if sheng(me, elem):
        return "食伤"
    if ke(elem, me):
        return "官杀"
    return "财星"


def _expand(item: str) -> tuple[str, ...]:
    return SHISHEN_ALIASES.get(item, (item,))


def _conflict(a: str, b: str) -> bool:
    return a == b or bool(set(_expand(a)) & set(_expand(b)))


def normalize_shen(raw: dict[str, list[str]], day_master: str) -> dict[str, list[str]]:
    """把 config 里的四维用神规范化。

    每项可以是十神（正印）、别名（印星）或五行（水，按日主换算成别名）。
    同一十神出现在多层时，只保留在最高层（用 > 喜 > 忌 > 仇），与原实现一致。
    """
    occupied: list[str] = []
    out: dict[str, list[str]] = {}
    for tier in TIER_INPUT_ORDER:
        kept: list[str] = []
        for item in raw.get(tier, []):
            if item in WUXING:
                item = wuxing_to_category(item, day_master)
            elif item not in SHISHEN_ALIASES and item not in ALL_SHISHEN:
                raise ValueError(f"无法识别的用神项: {item!r}（可写十神、印星/比劫/官杀/食伤/财星 或 五行）")
            if not any(_conflict(o, item) for o in occupied) and not any(_conflict(k, item) for k in kept):
                kept.append(item)
                occupied.append(item)
        out[tier] = kept
    return out


def shishen_tier(ss: str, shen: dict[str, list[str]]) -> str:
    for tier in (YONG, XI, JI, CHOU):
        if any(ss == item or ss in SHISHEN_ALIASES.get(item, ()) for item in shen.get(tier, [])):
            return tier
    return XIAN


def shishen_list_tier(ss_list: list[str], shen: dict[str, list[str]]) -> str:
    """一组十神取最高层级，优先级 用 > 喜 > 忌 > 仇 > 闲（与原实现一致）。"""
    tiers = {shishen_tier(s, shen) for s in ss_list}
    for tier in (YONG, XI, JI, CHOU):
        if tier in tiers:
            return tier
    return XIAN


def wuxing_shishen_pair(elem: str, day_master: str) -> list[str]:
    """五行对应的一对十神（阴阳各一），用于合化后的判断。"""
    return list(SHISHEN_ALIASES[wuxing_to_category(elem, day_master)])


# ---------- 原实现的分值表 ----------
BASE_SCORE = 70
SCORE_MIN, SCORE_MAX = 45, 98
DIM1_SCORES = {YONG: 10, XI: 6, XIAN: 0, CHOU: -5, JI: -8}
HEHUA_SCORES = {YONG: 6, XI: 4, XIAN: 1, CHOU: -4, JI: -5}
SANXING_SCORE = -15
CHONG_DAY, CHONG_MONTH, CHONG_YEAR = -10, -8, -4
FUYIN_SCORE = -2
HAI_SCORE = -4
ZHIXING_SCORES = {"成": 10, "开": 10, "定": 4, "执": 4, "除": 4, "满": 4,
                  "平": 0, "危": 0, "收": 0, "建": -10, "破": -10, "闭": -10}
KONGWANG_FACTOR = 0.7

_CHONG = {a: b for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥") for a, b in (p, p[::-1])}
_HAI = {a: b for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌") for a, b in (p, p[::-1])}
# 六合化神沿用原实现（午未合化土）
_LIUHE = {a: (b, wx) for p, wx in (("子丑", "土"), ("寅亥", "木"), ("卯戌", "火"),
                                   ("辰酉", "金"), ("巳申", "水"), ("午未", "土"))
          for a, b in (p, p[::-1])}
_SANHE = {z: (ju, wx) for ju, wx in (("申子辰", "水"), ("亥卯未", "木"),
                                     ("寅午戌", "火"), ("巳酉丑", "金")) for z in ju}
_SANXING_GROUPS = ("寅巳申", "丑戌未")


def has_sanxing(liu_zhi: str, natal_zhis: list[str]) -> bool:
    """三刑：流日地支须是组成该刑的字之一，其余字由命局日/月/年支补齐。"""
    pool = set(natal_zhis) | {liu_zhi}
    for group in _SANXING_GROUPS:
        if liu_zhi in group and set(group) <= pool:
            return True
    return (liu_zhi == "子" and "卯" in natal_zhis) or (liu_zhi == "卯" and "子" in natal_zhis)


def is_kongwang(liu_zhi: str, natal_day_xunkong: str, day_year_zhi: str, day_month_zhi: str) -> bool:
    """流日地支落在命主日柱旬空内，且未被当日年支/月支填实。"""
    return liu_zhi in natal_day_xunkong and liu_zhi not in (day_year_zhi, day_month_zhi)


def level(score: int) -> str:
    if score >= 85:
        return "优"
    if score >= 70:
        return "良"
    if score >= 60:
        return "平"
    if score >= 50:
        return "注意"
    return "慎行"


@dataclass(frozen=True)
class ScoreItem:
    dim: int
    reason: str
    points: int


@dataclass
class DailyScore:
    final: int
    level: str
    items: list[ScoreItem] = field(default_factory=list)
    has_sanxing: bool = False
    is_kongwang: bool = False
    raw_total: int = 0  # 空亡折算与区间限定之前


def score_day(day_gz: str, zhixing: str, day_year_zhi: str, day_month_zhi: str,
              day_master: str, natal_day_zhi: str, natal_month_zhi: str, natal_year_zhi: str,
              natal_day_xunkong: str, shen: dict[str, list[str]]) -> DailyScore:
    if day_master not in GAN:
        raise ValueError(f"日主必须是天干: {day_master!r}")
    gan, zhi = day_gz[0], day_gz[1]
    items: list[ScoreItem] = []

    # 维度 1：流日天干十神
    ss = shishen(day_master, gan)
    tier = shishen_tier(ss, shen)
    items.append(ScoreItem(1, f"天干{gan}为{ss}（{TIER_LABELS[tier]}）", DIM1_SCORES[tier]))

    # 维度 2：地支刑冲合害
    natal_zhis = [natal_day_zhi, natal_month_zhi, natal_year_zhi]
    sanxing = has_sanxing(zhi, natal_zhis)
    if sanxing:
        items.append(ScoreItem(2, f"地支{zhi}与命局成三刑（熔断）", SANXING_SCORE))
    else:
        for natal_zhi, name, pts in ((natal_day_zhi, "日支", CHONG_DAY),
                                     (natal_month_zhi, "月支", CHONG_MONTH),
                                     (natal_year_zhi, "年支", CHONG_YEAR)):
            if _CHONG[zhi] == natal_zhi:
                items.append(ScoreItem(2, f"{zhi}冲{name}{natal_zhi}", pts))
        if zhi == natal_day_zhi:
            items.append(ScoreItem(2, f"{zhi}与日支伏吟", FUYIN_SCORE))
        if _HAI[zhi] in (natal_day_zhi, natal_year_zhi):
            items.append(ScoreItem(2, f"{zhi}害{_HAI[zhi]}（日支或年支）", HAI_SCORE))
        partner, he_wx = _LIUHE[zhi]
        if partner in (natal_day_zhi, natal_year_zhi):
            t = shishen_list_tier(wuxing_shishen_pair(he_wx, day_master), shen)
            items.append(ScoreItem(2, f"{zhi}{partner}六合化{he_wx}（{TIER_LABELS[t]}）", HEHUA_SCORES[t]))
        ju, ju_wx = _SANHE[zhi]
        if any(z != zhi and z in natal_zhis for z in ju):
            t = shishen_list_tier(wuxing_shishen_pair(ju_wx, day_master), shen)
            items.append(ScoreItem(2, f"{zhi}入{ju}三合{ju_wx}局（{TIER_LABELS[t]}）", HEHUA_SCORES[t]))

    # 维度 3：建除十二神
    items.append(ScoreItem(3, f"建除「{zhixing}」日", ZHIXING_SCORES.get(zhixing, 0)))

    dims = sum(i.points for i in items)
    raw = BASE_SCORE + dims
    kong = is_kongwang(zhi, natal_day_xunkong, day_year_zhi, day_month_zhi)
    total = BASE_SCORE + math.floor(dims * KONGWANG_FACTOR) if kong else raw
    final = min(SCORE_MAX, max(SCORE_MIN, total))
    return DailyScore(final, level(final), items, sanxing, kong, raw)


# ---------- 标题 / 宜忌 ----------
def shishen_day(day_master: str, day_gz: str) -> str:
    """十神日：流日天干对日主。"""
    return shishen(day_master, day_gz[0])


def yiji_sentence(yi: list[str], ji: list[str], n: int) -> str:
    """黄历宜忌前 n 项拼成一句：'宜祭祀、出行，忌动土、安葬'。"""
    parts = []
    yi_s = "、".join([x for x in yi if x and x != "无"][:n])
    ji_s = "、".join([x for x in ji if x and x != "无"][:n])
    if yi_s:
        parts.append(f"宜{yi_s}")
    if ji_s:
        parts.append(f"忌{ji_s}")
    return "，".join(parts) if parts else "无特别宜忌"


def title(lv: str, shishen_name: str, yiji: str) -> str:
    return f"{lv}｜{shishen_name}日 · {yiji}"
