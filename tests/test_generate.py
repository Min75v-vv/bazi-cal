from datetime import date
from pathlib import Path

from bazi_calendar.chart import day_info, natal_chart
from bazi_calendar.config import load_config
from bazi_calendar.generate import build_events, main

ROOT = Path(__file__).resolve().parent.parent


def test_day_info_known_date():
    # 2026-11-03 为辛巳日
    assert day_info(date(2026, 11, 3)).ganzhi == "辛巳"


def test_zi_hour_sect(tmp_path):
    cfg = load_config(ROOT / "config.yaml")
    cfg.birth.year, cfg.birth.month, cfg.birth.day = 2000, 3, 1
    cfg.birth.hour, cfg.birth.minute, cfg.birth.longitude = 23, 30, 120.0
    cfg.equation_of_time = False
    cfg.zi_hour_sect = 1
    d1 = natal_chart(cfg).day
    cfg.zi_hour_sect = 2
    d2 = natal_chart(cfg).day
    assert d1 != d2  # sect=1 已换到次日


def test_build_events_and_main(tmp_path):
    cfg = load_config(ROOT / "config.yaml")
    events = build_events(cfg, natal_chart(cfg), date(2026, 1, 1), 365)
    assert len(events) == 365
    assert len({e.uid for e in events}) == 365
    assert all(e.summary.split("｜")[0] in ("优", "良", "平", "注意", "慎行")
               and "日 · " in e.summary for e in events)

    out = tmp_path / "bazi.ics"
    assert main(["--config", str(ROOT / "config.yaml"), "--out", str(out),
                 "--start", "2026-01-01", "--days", "10"]) == 0
    data = out.read_bytes()
    assert data.count(b"BEGIN:VEVENT") == 10
    assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")


def test_main_does_not_print_chart_by_default(tmp_path, capsys):
    # 公开仓库的 CI 日志任何人可见：默认输出不得包含命盘或出生时间
    out = tmp_path / "bazi.ics"
    main(["--config", str(ROOT / "config.yaml"), "--out", str(out), "--days", "1"])
    printed = capsys.readouterr().out
    assert "命盘" not in printed and "真太阳时" not in printed
    main(["--config", str(ROOT / "config.yaml"), "--out", str(out), "--days", "1", "--show-chart"])
    assert "真太阳时" in capsys.readouterr().out
