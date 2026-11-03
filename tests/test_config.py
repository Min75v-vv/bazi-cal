from pathlib import Path

import pytest
import yaml

from bazi_calendar.config import parse_config

ROOT = Path(__file__).resolve().parent.parent


def base():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def test_repo_config_is_valid():
    cfg = parse_config(base())
    assert cfg.shen == {"yong": ["水"], "xi": ["金"], "ji": ["土"], "chou": ["火"]}
    assert cfg.zi_hour_sect == 1 and cfg.equation_of_time is True


def test_shen_single_string_allowed():
    d = base()
    d["shen"] = {"yong": "印星"}
    assert parse_config(d).shen == {"yong": ["印星"], "xi": [], "ji": [], "chou": []}


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(shen={"xi": ["金"]}),                 # 缺用神
    lambda d: d.update(shen={"yong": ["水"], "xian": ["木"]}),  # 未知层级
    lambda d: d.update(shen={"yong": [1]}),
    lambda d: d.update(zi_hour_sect=3),
])
def test_invalid_config_rejected(mutate):
    d = base()
    mutate(d)
    with pytest.raises(ValueError):
        parse_config(d)
