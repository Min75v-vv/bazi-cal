import pytest

from bazi_calendar import rules

# 日主乙木：水=印星 金=官杀 土=财星 火=食伤 木=比劫
SHEN = rules.normalize_shen({"yong": ["水"], "xi": ["金"], "ji": ["土"], "chou": ["火"]}, "乙")


def score(day_gz, zhixing="平", day_year_zhi="午", day_month_zhi="戌",
          natal=("酉", "巳", "午"), xunkong="午未", shen=SHEN, dm="乙"):
    d, m, y = natal
    return rules.score_day(day_gz, zhixing, day_year_zhi, day_month_zhi, dm, d, m, y, xunkong, shen)


def points(sc):
    return {i.reason: i.points for i in sc.items}


# ---------- 用神规范化 ----------
def test_wuxing_to_category():
    assert [rules.wuxing_to_category(e, "乙") for e in "木火土金水"] == ["比劫", "食伤", "财星", "官杀", "印星"]


def test_normalize_shen_converts_wuxing():
    assert SHEN == {"yong": ["印星"], "xi": ["官杀"], "ji": ["财星"], "chou": ["食伤"]}


def test_normalize_shen_higher_tier_wins():
    shen = rules.normalize_shen({"yong": ["正印"], "xi": ["印星", "比劫"], "ji": ["比肩"]}, "甲")
    # 印星与用神正印冲突 → 喜神里丢弃；比肩与喜神比劫冲突 → 忌神里丢弃
    assert shen == {"yong": ["正印"], "xi": ["比劫"], "ji": [], "chou": []}


def test_normalize_shen_rejects_unknown():
    with pytest.raises(ValueError):
        rules.normalize_shen({"yong": ["贵人"]}, "甲")


def test_shishen_tier_and_list_tier():
    shen = {"yong": ["正印"], "xi": [], "ji": ["偏印"], "chou": []}
    assert rules.shishen_tier("正印", shen) == rules.YONG
    assert rules.shishen_tier("偏印", shen) == rules.JI
    assert rules.shishen_tier("七杀", shen) == rules.XIAN
    assert rules.shishen_list_tier(["偏印", "正印"], shen) == rules.YONG
    # 优先级 用 > 喜 > 忌 > 仇
    assert rules.shishen_list_tier(["a", "b"], {"yong": [], "xi": [], "ji": ["a"], "chou": ["b"]}) == rules.JI


# ---------- 维度 1 ----------
@pytest.mark.parametrize("gan,expected", [
    ("壬", 10),  # 正印 用神
    ("庚", 6),   # 正官 喜神
    ("甲", 0),   # 劫财 闲神
    ("丙", -5),  # 伤官 仇神
    ("戊", -8),  # 正财 忌神
])
def test_dim1(gan, expected):
    # 命局地支全为丑，寅与丑无任何关系，只剩维度 1
    sc = score(gan + "寅", natal=("丑", "丑", "丑"), xunkong="子丑")
    assert [i.points for i in sc.items if i.dim == 1] == [expected]


# ---------- 维度 2 ----------
def test_chong_day_month_year_accumulate():
    # 子冲午：日/月/年支都是午 → −10 −8 −4
    sc = score("甲子", natal=("午", "午", "午"), xunkong="戌亥")
    d2 = [i.points for i in sc.items if i.dim == 2]
    assert sorted(d2) == [-10, -8, -4]


def test_fuyin_day_zhi():
    sc = score("丁酉", natal=("酉", "寅", "寅"), xunkong="子丑")
    assert -2 in [i.points for i in sc.items if i.dim == 2]


def test_hai_counted_once():
    # 子害未：日支、年支都是未，只计一次 −4
    sc = score("甲子", natal=("未", "寅", "未"), xunkong="戌亥")
    assert [i.points for i in sc.items if "害" in i.reason] == [-4]


def test_liuhe_uses_hua_wuxing_tier():
    # 辰酉合化金 → 日主乙 官杀 = 喜神 → +4
    sc = score("甲辰", natal=("酉", "寅", "寅"), xunkong="子丑")
    assert points(sc)["辰酉六合化金（喜神）"] == 4


def test_liuhe_xian_gives_plus_one():
    # 寅亥合化木 → 比劫 闲神 → +1
    sc = score("甲寅", natal=("亥", "子", "子"), xunkong="戌亥")
    assert points(sc)["寅亥六合化木（闲神）"] == 1


def test_liuhe_only_day_or_year_zhi():
    # 月支合不算六合
    sc = score("甲辰", natal=("寅", "酉", "寅"), xunkong="子丑")
    assert not any("六合" in r for r in points(sc))


def test_sanhe_any_pillar():
    # 子 与 月支申 同属申子辰水局 → 印星 用神 +6
    sc = score("甲子", natal=("寅", "申", "寅"), xunkong="戌亥")
    assert points(sc)["子入申子辰三合水局（用神）"] == 6


def test_sanxing_fuses_dim2():
    # 寅 + 命局巳申 → 三刑；本来还会 寅冲申 −8，被熔断
    sc = score("甲寅", natal=("巳", "申", "子"), xunkong="子丑")
    d2 = [i.points for i in sc.items if i.dim == 2]
    assert d2 == [-15] and sc.has_sanxing


def test_sanxing_requires_day_zhi_to_participate():
    # 命局自带子卯：流日地支不是子或卯，不应触发（与原实现不同，已确认修正）
    sc = score("甲午", natal=("子", "卯", "寅"), xunkong="戌亥")
    assert not sc.has_sanxing
    assert rules.has_sanxing("卯", ["子", "寅", "寅"])
    assert rules.has_sanxing("子", ["卯", "寅", "寅"])
    assert not rules.has_sanxing("午", ["寅", "巳", "申"])
    assert rules.has_sanxing("申", ["寅", "巳", "午"])
    assert not rules.has_sanxing("申", ["寅", "午", "午"])


# ---------- 维度 3 ----------
@pytest.mark.parametrize("zx,pts", [("成", 10), ("开", 10), ("定", 4), ("满", 4),
                                    ("危", 0), ("建", -10), ("破", -10), ("闭", -10)])
def test_zhixing(zx, pts):
    assert rules.ZHIXING_SCORES[zx] == pts


# ---------- 空亡 / 汇总 ----------
def test_kongwang_uses_natal_day_xunkong():
    assert rules.is_kongwang("午", "午未", "子", "戌")
    assert not rules.is_kongwang("午", "午未", "午", "戌")  # 年支填实
    assert not rules.is_kongwang("午", "午未", "子", "午")  # 月支填实
    assert not rules.is_kongwang("申", "午未", "子", "戌")


def test_kongwang_floor_times_07():
    # 癸未：癸=偏印 用神 +10；未冲日/月/年支丑 −22；建除开 +10 → 合计 −2
    sc = score("癸未", zhixing="开", day_year_zhi="子", day_month_zhi="子",
               natal=("丑", "丑", "丑"), xunkong="午未")
    dims = sum(i.points for i in sc.items)
    assert dims == 10 - 10 - 8 - 4 + 10
    assert sc.is_kongwang
    assert sc.final == 68  # 70 + floor(−2 × 0.7) = 70 − 2


def test_base_and_clamp():
    # 壬申：正印用神 +10；申巳六合化水 用神 +6；申子三合水局 用神 +6；建除开 +10 → 102
    sc = score("壬申", zhixing="开", natal=("巳", "子", "巳"), xunkong="戌亥")
    assert sc.raw_total == 102
    assert sc.final == 98  # 限定上限
    low = score("戊子", zhixing="破", natal=("午", "午", "午"), xunkong="戌亥")
    assert low.raw_total == 70 - 8 - 22 - 10
    assert low.final == 45  # 限定下限


@pytest.mark.parametrize("s,lv", [(98, "优"), (85, "优"), (84, "良"), (70, "良"), (69, "平"),
                                  (60, "平"), (59, "注意"), (50, "注意"), (49, "慎行"), (45, "慎行")])
def test_level(s, lv):
    assert rules.level(s) == lv


def test_shishen_day_uses_day_gan():
    assert rules.shishen_day("乙", "辛巳") == "七杀"


def test_yiji_sentence():
    assert rules.yiji_sentence(["祭祀", "出行", "嫁娶"], ["动土", "安葬"], 2) == "宜祭祀、出行，忌动土、安葬"
    assert rules.yiji_sentence(["无"], ["诸事不宜"], 2) == "忌诸事不宜"
    assert rules.yiji_sentence([], [], 2) == "无特别宜忌"


def test_title():
    assert rules.title("良", "正财", "宜祭祀，忌动土") == "良｜正财日 · 宜祭祀，忌动土"
