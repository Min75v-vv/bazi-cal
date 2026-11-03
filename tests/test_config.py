from pathlib import Path

import pytest
import yaml

from bazi_calendar.config import RELATION_KEYS, parse_config

ROOT = Path(__file__).resolve().parent.parent


def base():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def test_repo_config_is_valid():
    cfg = parse_config(base())
    assert set(cfg.scoring.day_pillar) == set(RELATION_KEYS)
    assert cfg.zi_hour_sect == 1 and cfg.equation_of_time is True


def test_missing_relation_weight_defaults_to_zero():
    d = base()
    del d["scoring"]["day_pillar"]["伏吟"]
    assert parse_config(d).scoring.day_pillar["伏吟"] == 0


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(xiyong=["水", "风"]),
    lambda d: d.update(xiyong=["水"], jishen=["水"]),
    lambda d: d["scoring"]["day_pillar"].update({"三刑": -1}),
    lambda d: d["scoring"]["thresholds"].update(ji_min=-5),
    lambda d: d.update(zi_hour_sect=3),
])
def test_invalid_config_rejected(mutate):
    d = base()
    mutate(d)
    with pytest.raises(ValueError):
        parse_config(d)
