# Rili-haoge

自己用的八字趋吉避凶日历：每天一条全天事件，标题形如

```
吉｜正财日 · 宜祭祀、出行，忌动土、安葬
```

描述里列出当日干支、与我日柱/年柱的冲合刑害、十神、五行对喜用神/忌神的作用、评分明细和黄历宜忌。

## 用法

```bash
pip install -r requirements-dev.txt
python -m pytest -q                       # 单元测试
python -m bazi_calendar                   # 生成 public/bazi.ics（今天起 365 天）
python -m bazi_calendar --start 2027-01-01 --days 30 --out /tmp/test.ics
```

所有个人信息和规则参数都在 `config.yaml`：

| 配置 | 说明 |
| --- | --- |
| `birth` | 钟表出生时间（公历）、出生地 IANA 时区、经度 |
| `true_solar_time.equation_of_time` | `true` = 经度时差 + 均时差 |
| `zi_hour_sect` | `1` = 23 点即换日柱；`2` = 晚子时不换 |
| `xiyong` / `jishen` | 喜用神 / 忌神，其余五行为闲神 |
| `scoring` | 五行喜忌分、与日柱/年柱各种关系的分值、吉凶阈值（**当前是示例值**） |

## 判定口径

代码在 `bazi_calendar/rules.py`（纯函数）和 `bazi_calendar/ganzhi.py`（干支关系表）。

1. **命盘**：钟表时间 → 按出生地时区（含历史夏令时）转 UTC → 加经度时差和均时差得真太阳时 → lunar_python 排四柱，年柱按立春、月柱按节气。
2. **流日**：取当天正午的日干支；流月/流年按节气精确交接。
3. **十神日**：流日天干对日主。
4. **评分**：流日天干、地支（本气）五行是喜用加分、是忌神减分、闲神不计；流日与日柱、年柱之间的伏吟、天克地冲、天干五合/相冲、地支六冲/六合/半合/拱合/相刑/自刑/六害/六破分别按 config 中的分值计入。多项会叠加。
5. **分档**：总分 ≥ `ji_min` 为吉，≤ `xiong_max` 为凶，其余为平。
6. **一句话宜忌**：lunar_python 的黄历宜、忌各取前 `yiji_count` 项（这是通书宜忌，与个人八字无关）。

## 自动发布

`.github/workflows/build.yml`：每月 1 日 08:37（北京时间）、推送到 `main` 时、或手动触发，跑测试 → 生成 → 发布到 GitHub Pages。

首次使用：仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。订阅地址为
`https://<用户名>.github.io/<仓库名>/bazi.ics`（日历 App 里用「订阅日历 / 从 URL 添加」）。

不想把出生信息提交进仓库：把完整的 config.yaml 内容存成仓库 Secret `BAZI_CONFIG`，工作流会用它覆盖仓库里的 config.yaml。注意 Pages 上的 bazi.ics 本身是公开可访问的，里面带有命盘四柱。
