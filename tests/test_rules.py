import pytest

from bazi_calendar import rules
from bazi_calendar.config import RELATION_KEYS, Scoring


def make_scoring(**over):
    base = dict(gan_xiyong=2, gan_jishen=-2, zhi_xiyong=2, zhi_jishen=-2,
                day_pillar={k: 0.0 for k in RELATION_KEYS},
                year_pillar={k: 0.0 for k in RELATION_KEYS},
                ji_min=3, xiong_max=-3)
    base.update(over)
    return Scoring(**base)


def test_wuxing_role():
    assert rules.wuxing_role("水", ["水", "金"], ["火"]) == rules.XIYONG
    assert rules.wuxing_role("火", ["水", "金"], ["火"]) == rules.JISHEN
    assert rules.wuxing_role("木", ["水", "金"], ["火"]) == rules.XIANSHEN


@pytest.mark.parametrize("label,key", [
    ("伏吟", "伏吟"), ("天克地冲", "天克地冲"), ("天干五合", "天干五合"),
    ("地支半合水局", "地支半合"), ("地支拱合火局", "地支拱合"), ("地支六冲", "地支六冲"),
])
def test_relation_key(label, key):
    assert rules.relation_key(label) == key
    assert key in RELATION_KEYS


def test_score_wuxing_only():
    s = make_scoring()
    # 壬子：天干壬水、地支子水 均喜用
    items = rules.score_day("壬子", "乙酉", "庚午", ["水", "金"], ["火", "土"], s)
    assert rules.total(items) == 4
    # 丙午：均忌神
    items = rules.score_day("丙午", "乙卯", "庚寅", ["水", "金"], ["火", "土"], s)
    assert rules.total(items) == -4


def test_score_xianshen_not_counted():
    s = make_scoring()
    items = rules.score_day("甲寅", "乙酉", "庚午", ["水", "金"], ["火", "土"], s)
    assert items == []


def test_score_relations_use_pillar_weights():
    dp = {k: 0.0 for k in RELATION_KEYS} | {"地支六冲": -3}
    yp = {k: 0.0 for k in RELATION_KEYS} | {"地支六冲": -2}
    s = make_scoring(gan_xiyong=0, gan_jishen=0, zhi_xiyong=0, zhi_jishen=0,
                     day_pillar=dp, year_pillar=yp)
    # 辛卯：卯冲日支酉(-3)；其余关系（天干相冲、天克地冲、卯午破）权重为 0 不计
    items = rules.score_day("辛卯", "乙酉", "庚午", ["水"], ["火"], s)
    assert [(i.reason, i.points) for i in items] == [("地支六冲日柱", -3)]
    # 甲子：子冲年支午(-2)；子酉六破、甲庚相冲权重为 0
    items = rules.score_day("甲子", "乙酉", "庚午", ["水"], ["火"], s)
    assert rules.total(items) == -2
    assert ("地支六冲年柱", -2) in [(i.reason, i.points) for i in items]


def test_score_stacks_tian_ke_di_chong():
    # 辛卯 对 乙酉：天克地冲、天干相冲、地支六冲 三项叠加
    dp = {k: 0.0 for k in RELATION_KEYS} | {"天克地冲": -2, "地支六冲": -3, "天干相冲": -1}
    s = make_scoring(gan_xiyong=0, gan_jishen=0, zhi_xiyong=0, zhi_jishen=0, day_pillar=dp)
    items = rules.score_day("辛卯", "乙酉", "壬辰", [], [], s)
    assert rules.total(items) == -6


@pytest.mark.parametrize("score,expected", [
    (3, "吉"), (5, "吉"), (2.9, "平"), (0, "平"), (-2.5, "平"), (-3, "凶"), (-9, "凶"),
])
def test_level(score, expected):
    assert rules.level(score, 3, -3) == expected


def test_shishen_day_uses_day_gan():
    assert rules.shishen_day("乙", "辛巳") == "七杀"
    assert rules.shishen_day("乙", "壬午") == "正印"


def test_yiji_sentence():
    assert rules.yiji_sentence(["祭祀", "出行", "嫁娶"], ["动土", "安葬"], 2) == "宜祭祀、出行，忌动土、安葬"
    assert rules.yiji_sentence(["无"], ["诸事不宜"], 2) == "忌诸事不宜"
    assert rules.yiji_sentence([], [], 2) == "无特别宜忌"
    assert rules.yiji_sentence(["祭祀"], [], 3) == "宜祭祀"


def test_wuxing_effects():
    assert rules.wuxing_effects("金", ["水"], ["火"]) == ["生喜用水", "耗忌神火"]


def test_title():
    assert rules.title("吉", "正财", "宜祭祀，忌动土") == "吉｜正财日 · 宜祭祀，忌动土"
