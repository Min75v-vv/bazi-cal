"""干支基础表与客观关系判定（不含任何吉凶判断）。

这里只放命理里没有争议的「事实性」关系：五行、生克、十神、
天干五合/相冲、地支六冲/六合/三合/相刑/六害/六破、伏吟、天克地冲。
吉凶怎么算放在 rules.py。
"""
from __future__ import annotations

from lunar_python.util import LunarUtil

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WUXING = "木火土金水"

WUXING_GAN: dict[str, str] = dict(LunarUtil.WU_XING_GAN)
WUXING_ZHI: dict[str, str] = dict(LunarUtil.WU_XING_ZHI)
ZHI_HIDE_GAN: dict[str, list[str]] = {k: list(v) for k, v in LunarUtil.ZHI_HIDE_GAN.items()}

# 相生：木→火→土→金→水→木
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 相克：木→土→水→火→金→木
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def wuxing_of(char: str) -> str:
    """单个天干或地支的五行（地支取本气五行）。"""
    if char in WUXING_GAN:
        return WUXING_GAN[char]
    if char in WUXING_ZHI:
        return WUXING_ZHI[char]
    raise ValueError(f"不是天干或地支: {char!r}")


def sheng(a: str, b: str) -> bool:
    """五行 a 生 b。"""
    return _SHENG[a] == b


def ke(a: str, b: str) -> bool:
    """五行 a 克 b。"""
    return _KE[a] == b


def shishen(day_master: str, gan: str) -> str:
    """以日主天干为我，求另一天干的十神（比肩/劫财/食神/…）。"""
    if day_master not in GAN or gan not in GAN:
        raise ValueError(f"十神需要两个天干: {day_master!r}, {gan!r}")
    return LunarUtil.SHI_SHEN[day_master + gan]


# ---------- 天干 ----------
_GAN_HE = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水",
           frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
_GAN_CHONG = {frozenset("甲庚"), frozenset("乙辛"), frozenset("丙壬"), frozenset("丁癸")}


def gan_relations(a: str, b: str) -> list[str]:
    """两个天干之间的关系：['五合'] / ['相冲'] / []。"""
    pair = frozenset((a, b))
    rel = []
    if pair in _GAN_HE:
        rel.append("五合")
    if pair in _GAN_CHONG:
        rel.append("相冲")
    return rel


# ---------- 地支 ----------
_LIU_CHONG = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
_LIU_HE = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
_SAN_HE = ("申子辰", "亥卯未", "寅午戌", "巳酉丑")  # 生、旺(中神)、墓
_SAN_HE_WX = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}
_XING = {frozenset(p) for p in ("寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未", "子卯")}
_ZI_XING = set("辰午酉亥")
_LIU_HAI = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
_LIU_PO = {frozenset(p) for p in ("子酉", "卯午", "巳申", "寅亥", "丑辰", "戌未")}


def zhi_relations(a: str, b: str) -> list[str]:
    """两个地支之间的全部关系，按 六冲/六合/半合/拱合/相刑/自刑/六害/六破 顺序。

    三合局两两相遇：含中神（子午卯酉）为「半合」，生地与墓地相遇为「拱合」。
    """
    if a not in ZHI or b not in ZHI:
        raise ValueError(f"不是地支: {a!r}, {b!r}")
    pair = frozenset((a, b))
    rel = []
    if pair in _LIU_CHONG:
        rel.append("六冲")
    if pair in _LIU_HE:
        rel.append("六合")
    if a != b:
        for ju in _SAN_HE:
            if a in ju and b in ju:
                wx = _SAN_HE_WX[ju]
                rel.append(f"半合{wx}局" if ju[1] in (a, b) else f"拱合{wx}局")
    if pair in _XING:
        rel.append("相刑")
    if a == b and a in _ZI_XING:
        rel.append("自刑")
    if pair in _LIU_HAI:
        rel.append("六害")
    if pair in _LIU_PO:
        rel.append("六破")
    return rel


def pillar_relations(day_gz: str, natal_gz: str) -> list[str]:
    """流日干支与命局某一柱之间的关系，天干关系加「天干」前缀，地支加「地支」前缀，
    另判伏吟（干支完全相同）与天克地冲（天干相克且地支六冲，任一方向）。"""
    dg, dz = day_gz[0], day_gz[1]
    ng, nz = natal_gz[0], natal_gz[1]
    rel = []
    if day_gz == natal_gz:
        rel.append("伏吟")
    gwx, nwx = wuxing_of(dg), wuxing_of(ng)
    if (ke(gwx, nwx) or ke(nwx, gwx)) and frozenset((dz, nz)) in _LIU_CHONG:
        rel.append("天克地冲")
    rel += [f"天干{r}" for r in gan_relations(dg, ng)]
    rel += [f"地支{r}" for r in zhi_relations(dz, nz)]
    return rel


def wuxing_effect(elem: str, target: str) -> str:
    """五行 elem 对 target 的作用：助(同类)/生/克/泄(target 生 elem)/耗(target 克 elem)。"""
    if elem == target:
        return "助"
    if sheng(elem, target):
        return "生"
    if ke(elem, target):
        return "克"
    if sheng(target, elem):
        return "泄"
    return "耗"  # 只剩 target 克 elem
