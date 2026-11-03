# bazi-cal

自己用的八字趋吉避凶日历：每天一条全天事件，标题形如

```
良｜正印日 · 宜祭祀、出行，忌动土、安葬
```

等级分五档：优 / 良 / 平 / 注意 / 慎行。描述里列出当日干支与建除、与我日柱/月柱/年柱的冲合刑害、十神、五行对四维用神的作用、评分明细和黄历宜忌。

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
| `shen` | 四维用神：用神 `yong` / 喜神 `xi` / 忌神 `ji` / 仇神 `chou`，可写十神、类别（印星等）或五行；其余为闲神 |

## 判定口径

评分规则移植自 [oceanjustinlin/qimen](https://github.com/oceanjustinlin/qimen)（MIT，见 `THIRD_PARTY_NOTICES.md`），代码在 `bazi_calendar/rules.py`（纯函数），干支关系表在 `bazi_calendar/ganzhi.py`。

1. **命盘**：钟表时间 → 按出生地时区（含历史夏令时）转 UTC → 加经度时差和均时差得真太阳时 → lunar_python 排四柱，年柱按立春、月柱按节气。
2. **流日**：取当天正午的日干支与建除十二神；流月/流年按节气精确交接。
3. **十神日**：流日天干对日主。
4. **评分**（基础 70，限定 45–98）：
   - 流日天干十神：用神 +10、喜神 +6、闲神 0、仇神 −5、忌神 −8；
   - 流日地支：与命局成三刑则 −15 且不再看其它；否则冲日支 −10、冲月支 −8、冲年支 −4，与日支相同 −2，害日支或年支 −4，与日支或年支六合、与任一柱三合时按合化五行的层级计分（用 +6 / 喜 +4 / 闲 +1 / 仇 −4 / 忌 −5）；
   - 建除：成开 +10，定执除满 +4，平危收 0，建破闭 −10；
   - 空亡：流日地支落在命主日柱旬空且未被当日年/月支填实，以上合计 ×0.7。
5. **分档**：≥85 优，≥70 良，≥60 平，≥50 注意，<50 慎行。
6. **与原版不同的两处**（已确认）：三刑要求流日地支参与（原版命局自带子卯等会天天触发）；空亡改看命主日柱旬空（原版判断条件永远不成立）。`tests/test_qimen_reference.py` 用原版代码生成的 992 条数据做逐条回归。
7. **一句话宜忌**：lunar_python 的黄历宜、忌各取前 `yiji_count` 项（通书宜忌，与个人八字无关）。

## 自动发布

`.github/workflows/build.yml`：每月 1 日 08:37（北京时间）、推送到 `main` 时、或手动触发，跑测试 → 生成 → 发布到 GitHub Pages。

首次使用：仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。订阅地址为
`https://<用户名>.github.io/<仓库名>/bazi.ics`（日历 App 里用「订阅日历 / 从 URL 添加」）。

不想把出生信息提交进仓库：把完整的 config.yaml 内容存成仓库 Secret `BAZI_CONFIG`，工作流会用它覆盖仓库里的 config.yaml。注意 Pages 上的 bazi.ics 本身是公开可访问的，里面带有命盘四柱。
