"""真太阳时校正。

钟表时间（含该地当时的夏令时，靠 zoneinfo 的历史数据处理，例如中国 1986–1991 年夏令时）
→ UTC → 加上经度时差（每度 4 分钟）得到地方平太阳时 → 可选再加均时差得到真太阳时。
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def equation_of_time_minutes(dt: datetime) -> float:
    """均时差（分钟，真太阳时 − 平太阳时），NOAA 常用近似式，误差约 ±30 秒。"""
    n = dt.timetuple().tm_yday
    b = 2 * math.pi * (n - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(clock: datetime, tz: str, longitude: float,
                    use_equation_of_time: bool) -> datetime:
    """返回出生地的地方太阳时（naive datetime）。

    clock: 出生证/家人记录的钟表时间（naive）
    tz: IANA 时区名，如 'Asia/Shanghai'
    longitude: 东经为正
    """
    utc = clock.replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)
    local_mean = utc.replace(tzinfo=None) + timedelta(minutes=longitude * 4)
    if use_equation_of_time:
        local_mean += timedelta(minutes=equation_of_time_minutes(local_mean))
    return local_mean
