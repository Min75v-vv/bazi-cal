"""命盘与流日数据的获取（全部委托 lunar_python）。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from lunar_python import Solar
from lunar_python.util import LunarUtil

from .config import Config
from .solar_time import true_solar_time


@dataclass(frozen=True)
class Natal:
    year: str   # 年柱干支
    month: str
    day: str    # 日柱干支，day[0] 即日主
    time: str
    solar_time: datetime  # 校正后的出生时间

    @property
    def day_master(self) -> str:
        return self.day[0]

    @property
    def day_xunkong(self) -> str:
        """日柱旬空，如 乙酉 → 午未。"""
        return LunarUtil.getXunKong(self.day)


def natal_chart(cfg: Config) -> Natal:
    b = cfg.birth
    clock = datetime(b.year, b.month, b.day, b.hour, b.minute)
    t = true_solar_time(clock, b.timezone, b.longitude, cfg.equation_of_time)
    ec = Solar.fromYmdHms(t.year, t.month, t.day, t.hour, t.minute, t.second).getLunar().getEightChar()
    ec.setSect(cfg.zi_hour_sect)
    return Natal(ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime(), t)


@dataclass(frozen=True)
class DayInfo:
    day: date
    ganzhi: str        # 流日干支
    month_ganzhi: str  # 流月（按节气）
    year_ganzhi: str   # 流年（按立春）
    zhixing: str       # 建除十二神
    yi: list[str]      # 黄历宜
    ji: list[str]      # 黄历忌


def day_info(d: date) -> DayInfo:
    # 取当天正午，避开子时换日问题；流月流年按节气精确交接
    lunar = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0).getLunar()
    return DayInfo(d, lunar.getDayInGanZhi(), lunar.getMonthInGanZhiExact(),
                   lunar.getYearInGanZhiExact(), lunar.getZhiXing(),
                   list(lunar.getDayYi()), list(lunar.getDayJi()))
