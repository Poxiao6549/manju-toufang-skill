# 漫剧投放 — management report design

Requirements gathered from business-side (WeChat group) +
management dashboard screenshots. Status: **design confirmed with user, not yet
built.** Text Q&A prioritized over docx.

## Confirmed decisions

| # | Item | Decision |
|---|------|----------|
| 1 | Audience / channel | Management, via **WeChat** |
| 2 | Output forms | **Text Q&A (priority)** + **docx** full report |
| 3 | Tenant | Lock **tenant 1** (`adex tenant use 1`). Tenant ≠ account. |
| 4 | Platforms | 快手 (adex-ks) + 巨量 (adex-oe), side-by-side |
| 5 | 投手/investor dimension | **OUT this version** — not in adex. plan-name suffix = director/other, strip it |
| 6 | 项目 = 剧集 (drama) | Yes |
| 7 | Drama granularity | **Dual, switch by question:** drama-name rollup (方案B) for "which drama performs best"; native full plan name (方案A) for plan-level detail |
| 8 | Drama-name normalization | **AI/LLM, not regex** — regex mangles Chinese punctuation, `IAA-` prefix, embedded dates |
| 9 | Time口径 | Parse from natural language → adex `--range` or `--begin/--end` |
| 10 | Thresholds (达标/异常) | Env-var placeholders; confirm values with user, don't hardcode |

## Why drama-name normalization must be AI, not regex

Real plan names (快手, tenant 1):
```
自投-示例剧名A-_0708_103529- dir_1
自投-IAA-示例剧名C，带逗号-1-复刻动漫-0619001
自投-示例剧名E：带冒号-0711_134316-定投女- dir_45
自投-100200300-示例剧名D-1-[日期]-ops-002
自投-0705_104549_001示例剧名F：带冒号-1
```
Regex splitting on `-`/`_` produced garbage: `IAA-示例剧名C，带逗` (Chinese comma
truncation), `0705_104549_` (date mistaken for name), and split the same drama
across `IAA-` vs non-`IAA-` prefixes. adex `summary --group-by` only supports
`campaign_id`, so drama rollup is a **second aggregation** over plan names — hand
the raw name list to the LLM to identify + merge true titles. ~60 plans → ~24
dramas in testing.

## docx report skeleton

```
标题: 漫剧投放报告 | 周期: YYYY-MM-DD ~ YYYY-MM-DD | 数据源: adex(租户1)
一、投放大盘概览      —— 核心指标卡片 + AI 一句话总结
二、平台对比(快手 vs 巨量) —— 并列表 + 消耗占比
三、剧集维度 Top 排行  —— 剧名│消耗│变现│ROI│激活│完播率 + AI 点评
四、异常/关注提示      —— ROI过低/消耗骤降等 AI 信号
附: 口径说明(租户/时间/剧名为AI归一化)
```

## Metrics

Mirror the management dashboard: 消耗, 变现金额, ROI, 曝光量, 广告点击量, CTR,
激活数, 激活成本, CVR, 3秒完播率, 完播率. AI-derived: 跑量集中度(Top3剧消耗占比),
平台消耗结构, ROI达标率, 环比(当期 vs 上期 — only compute when asked; adex reports
don't return 环比 natively, pull two windows and diff).

## Time-parsing map

| 用户说 | 参数 |
|--------|------|
| 上周 | last Mon–Sun explicit `--begin/--end` |
| 过去一个月 | `--range 30d` |
| 上个月 | prior calendar month `--begin/--end` |
| 今天 / 实时 | `dashboard` |

## Proposed skill layout (when built)

```
skills/漫剧投放报告/  (or extend adex-reporting)
  SKILL.md                  意图路由, 时间解析, 维度决策树
  references/metrics-glossary.md
  references/drama-name-rules.md
  templates/report-weekly.md
  scripts/gen_docx.py        python-docx 生成器 (verify python-docx installed)
```

## Open items to confirm before/during build

- 巨量(oe) field structure — verify project/unit naming & where drama name lives
- python-docx availability in env
- Threshold values for 达标/异常
