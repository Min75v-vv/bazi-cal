from datetime import datetime

import pytest

from bazi_calendar.solar_time import equation_of_time_minutes, true_solar_time


def test_longitude_only_shanghai_meridian_120():
    # 东经 120° 正好是东八区中央经线，不加均时差时不变
    t = true_solar_time(datetime(2000, 1, 1, 12, 0), "Asia/Shanghai", 120.0, False)
    assert t == datetime(2000, 1, 1, 12, 0)


def test_longitude_offset_beijing():
    # 116.4° → (116.4-120)*4 = -14.4 分钟
    t = true_solar_time(datetime(2000, 3, 1, 12, 0), "Asia/Shanghai", 116.4, False)
    assert t == datetime(2000, 3, 1, 11, 45, 36)


def test_china_dst_1990_handled():
    # 1990-05-20 中国实行夏令时，钟表 14:30 = 标准时 13:30
    t = true_solar_time(datetime(1990, 5, 20, 14, 30), "Asia/Shanghai", 120.0, False)
    assert t == datetime(1990, 5, 20, 13, 30)


@pytest.mark.parametrize("month,day,expected,tol", [
    (2, 11, -14.2, 0.6),   # 全年最小值附近
    (11, 3, 16.4, 0.6),    # 全年最大值附近
    (4, 15, 0.0, 0.6),
])
def test_equation_of_time(month, day, expected, tol):
    assert equation_of_time_minutes(datetime(2021, month, day)) == pytest.approx(expected, abs=tol)


def test_equation_of_time_applied():
    a = true_solar_time(datetime(2021, 11, 3, 12, 0), "Asia/Shanghai", 120.0, False)
    b = true_solar_time(datetime(2021, 11, 3, 12, 0), "Asia/Shanghai", 120.0, True)
    assert 16 <= (b - a).total_seconds() / 60 <= 17
