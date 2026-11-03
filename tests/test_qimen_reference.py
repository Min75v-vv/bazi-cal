"""与 qimen 原版 JS 的差分回归：固定数据由原版代码生成，移植版必须逐条一致。"""
import json
from pathlib import Path

from lunar_python.util import LunarUtil

from bazi_calendar import rules

DATA = json.loads((Path(__file__).parent / "fixtures" / "qimen_reference.json").read_text(encoding="utf-8"))


def test_matches_original_implementation():
    assert len(DATA["rows"]) > 900
    mismatches = []
    for day_gz, zx, yz, mz, ri_zhu, n_mz, n_yz, shen, expected in DATA["rows"]:
        sc = rules.score_day(day_gz, zx, yz, mz, ri_zhu[0], ri_zhu[1], n_mz, n_yz,
                             LunarUtil.getXunKong(ri_zhu), rules.normalize_shen(shen, ri_zhu[0]))
        if sc.final != expected:
            mismatches.append((day_gz, ri_zhu, n_mz, n_yz, shen, expected, sc.final))
    assert mismatches == []
