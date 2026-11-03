"""吉 / 平 / 凶 判定规则 —— 全部是纯函数，便于单测。

口径（已与使用者确认）：
- 评分制：流日天干、地支（只取本气）五行对照喜用神/忌神加减分；
  流日与命局日柱、年柱的冲合刑害等关系按 config 中的权重加减分；总分按阈值分档。
- 忌神在 config 中单独列出，不在喜用、忌神里的五行为闲神，不计分。
- 十神日以流日天干对日主为准。
- 一句话宜忌取黄历（lunar_python 通书宜忌）前 N 项。
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import Scoring
from .ganzhi import pillar_relations, shishen, wuxing_effect, wuxing_of

XIYONG, JISHEN, XIANSHEN = "喜用", "忌神", "闲神"
JI, PING, XIONG = "吉", "平", "凶"


def wuxing_role(elem: str, xiyong: list[str], jishen: list[str]) -> str:
    if elem in xiyong:
        return XIYONG
    if elem in jishen:
        return JISHEN
    return XIANSHEN


def relation_key(label: str) -> str:
    """把 pillar_relations 的标签归一成 config 权重键，如 '地支半合水局' → '地支半合'。"""
    if label in ("伏吟", "天克地冲"):
        return label
    return label[:4]


@dataclass(frozen=True)
class ScoreItem:
    reason: str
    points: float


def score_day(day_gz: str, natal_day: str, natal_year: str,
              xiyong: list[str], jishen: list[str], s: Scoring) -> list[ScoreItem]:
    """返回所有非零计分项。"""
    items: list[ScoreItem] = []
    gan, zhi = day_gz[0], day_gz[1]

    for pos, char, w_xi, w_ji in (("天干", gan, s.gan_xiyong, s.gan_jishen),
                                  ("地支", zhi, s.zhi_xiyong, s.zhi_jishen)):
        elem = wuxing_of(char)
        role = wuxing_role(elem, xiyong, jishen)
        if role == XIYONG:
            items.append(ScoreItem(f"{pos}{char}{elem}为喜用", w_xi))
        elif role == JISHEN:
            items.append(ScoreItem(f"{pos}{char}{elem}为忌神", w_ji))

    for pillar_name, natal_gz, weights in (("日柱", natal_day, s.day_pillar),
                                           ("年柱", natal_year, s.year_pillar)):
        for label in pillar_relations(day_gz, natal_gz):
            items.append(ScoreItem(f"{label}{pillar_name}", weights[relation_key(label)]))

    return [i for i in items if i.points != 0]


def total(items: list[ScoreItem]) -> float:
    return sum(i.points for i in items)


def level(score: float, ji_min: float, xiong_max: float) -> str:
    if score >= ji_min:
        return JI
    if score <= xiong_max:
        return XIONG
    return PING


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


def wuxing_effects(elem: str, xiyong: list[str], jishen: list[str]) -> list[str]:
    """五行 elem 对每个喜用神、忌神的作用，如 ['生喜用水', '克忌神火']。"""
    out = [f"{wuxing_effect(elem, y)}喜用{y}" for y in xiyong]
    out += [f"{wuxing_effect(elem, j)}忌神{j}" for j in jishen]
    return out


def title(lv: str, shishen_name: str, yiji: str) -> str:
    return f"{lv}｜{shishen_name}日 · {yiji}"
