import pytest

from bazi_calendar.ganzhi import (gan_relations, pillar_relations, shishen,
                                  wuxing_effect, wuxing_of, zhi_relations)


@pytest.mark.parametrize("dm,gan,expected", [
    ("甲", "甲", "比肩"), ("甲", "乙", "劫财"), ("甲", "丙", "食神"), ("甲", "丁", "伤官"),
    ("甲", "戊", "偏财"), ("甲", "己", "正财"), ("甲", "庚", "七杀"), ("甲", "辛", "正官"),
    ("甲", "壬", "偏印"), ("甲", "癸", "正印"), ("乙", "辛", "七杀"), ("癸", "戊", "正官"),
])
def test_shishen(dm, gan, expected):
    assert shishen(dm, gan) == expected


def test_shishen_rejects_zhi():
    with pytest.raises(ValueError):
        shishen("甲", "子")


def test_wuxing_of():
    assert wuxing_of("庚") == "金"
    assert wuxing_of("戌") == "土"
    assert wuxing_of("亥") == "水"


@pytest.mark.parametrize("elem,target,expected", [
    ("水", "水", "助"), ("金", "水", "生"), ("土", "水", "克"),
    ("木", "水", "泄"), ("火", "水", "耗"),
])
def test_wuxing_effect(elem, target, expected):
    assert wuxing_effect(elem, target) == expected


def test_gan_relations():
    assert gan_relations("甲", "己") == ["五合"]
    assert gan_relations("庚", "甲") == ["相冲"]
    assert gan_relations("戊", "己") == []
    assert gan_relations("戊", "甲") == []  # 戊甲相克但不算相冲


@pytest.mark.parametrize("a,b,expected", [
    ("子", "午", ["六冲"]),
    ("子", "丑", ["六合"]),
    ("申", "子", ["半合水局"]),
    ("申", "辰", ["拱合水局"]),
    ("子", "卯", ["相刑"]),
    ("午", "午", ["自刑"]),
    ("子", "子", []),
    ("丑", "未", ["六冲", "相刑"]),
    ("寅", "申", ["六冲", "相刑"]),
    ("寅", "巳", ["相刑", "六害"]),
    ("巳", "申", ["六合", "相刑", "六破"]),
    ("寅", "亥", ["六合", "六破"]),
    ("卯", "午", ["六破"]),
    ("酉", "戌", ["六害"]),
    ("戌", "未", ["相刑", "六破"]),
    ("子", "寅", []),
])
def test_zhi_relations(a, b, expected):
    assert zhi_relations(a, b) == expected
    assert zhi_relations(b, a) == expected  # 对称


def test_pillar_relations_fuyin():
    assert pillar_relations("甲子", "甲子") == ["伏吟"]


def test_pillar_relations_tian_ke_di_chong():
    # 庚克甲，申冲寅
    assert pillar_relations("庚申", "甲寅") == ["天克地冲", "天干相冲", "地支六冲", "地支相刑"]
    # 甲克戊（我克）也算天克
    assert "天克地冲" in pillar_relations("甲辰", "戊戌")


def test_pillar_relations_chong_without_ke():
    # 天干相同（不相克），只有地支冲，不算天克地冲
    assert pillar_relations("甲子", "甲午") == ["地支六冲"]
