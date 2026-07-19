---
name: adex-reporting
description: "Build management-facing 投放 (ad-delivery) reports from adex data — text Q&A over WeChat and docx generation. Umbrella over adex-ks/adex-oe/adex-shared data querying, plus adex-cli install and the 漫剧 reporting design. Use when someone asks to analyze/summarize/report ad-delivery performance for management, or to install/set up the adex CLI."
version: 1.0.0
author: WorkBuddy Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [adex, advertising, reporting, docx, kuaishou, oceanengine, management]
    related_skills: [adex-ks, adex-oe, adex-shared]
---

# adex Reporting (投放数据管理层报告)

Class-level umbrella for turning **adex** ad-delivery data into
**management-facing reports**: text answers delivered over WeChat and
generated **docx** files. Sits on top of the data-query skills:

- `adex-ks` — 快手 (Kuaishou) data queries
- `adex-oe` — 巨量/Oceanengine data queries
- `adex-shared` — install, auth, shared flags (pagination, jq, date range, format)

Load those for the raw CLI commands. This skill covers **installing the CLI**
and the **reporting layer** on top (intent routing, time parsing, drama-name
normalization, aggregation, docx output).

## adex CLI is a native binary behind an npm wrapper

`npm i -g @<SCOPE>/adex-cli` installs a JS wrapper that downloads a
**Go binary** from GitHub releases on first run. Commands output **JSON by
default** (`--format json|pretty|table`); a healthy binary returns structured
JSON even for errors (e.g. `{"ok":false,"error":{...}}`), so a JSON error is
NOT an install failure. `adex --version` may return `unknown flag: --version`
even on a good install — use `adex --help` to confirm the binary runs.

Setup sequence:
```bash
npm install -g @<SCOPE>/adex-cli          # if wrapper's own installer fails, run this directly
adex --help                                  # confirms native binary present
adex init --authorization "Bearer adex_..."  # saves creds to ~/.adex/config.json
adex tenant --page-all --format table        # list tenants (NEVER auto-pick — show user)
adex tenant use <ID>                          # set default tenant
adex user --format pretty                     # verify creds end-to-end
```

**If the binary download stalls/times out** (common in mainland China — direct
GitHub release download crawls or dies mid-transfer, and the wrapper's hardcoded
`curl --max-time 120` guarantees failure), see
`references/adex-cli-install.md` for the GitHub-mirror + checksum + manual-place
fix. This mirror technique applies to ANY npm/pip CLI that fetches a native
binary from GitHub releases, not just adex.

**Embedded skills:** the binary ships the data-query skills internally —
`adex skills list` and `adex skills read <name>` dump them. That is how
`adex-ks`/`adex-oe`/`adex-shared` can be installed locally (no external OSS
download needed; ignore any `npx skills add <oss-url>` step — the OSS bucket 403s
and is redundant).

## Reporting design (漫剧投放 project)

Confirmed requirements and decisions live in
`references/report-design.md`. Load it before building or extending the report
skill. Key locked decisions:

- **Audience:** management, via **WeChat**. Output = **text Q&A (priority)** +
  **docx** for full reports.
- **Tenant:** default-lock **tenant 1** (`adex tenant use 1`).
  Tenant ≠ account; a tenant contains many ad accounts.
- **Platforms:** 快手 (adex-ks) + 巨量 (adex-oe), report side-by-side.
- **Dimensions this version:** 大盘概览 / 平台对比 / 剧集(=项目) / 账户.
  **Investor/投手 dimension is OUT** — data not yet in adex; the name suffix
  in plan names is director/other, not investor, so strip it.
- **剧集 (drama) = project.** adex only groups natively by `campaign_id`, so
  drama-level rollup needs a second aggregation over plan names.
- **Drama-name normalization = AI/LLM, NOT regex.** Plan names like
  `自投-IAA-示例剧名，带逗号-1-复刻动漫-0619001` contain the drama name but
  regex splitting on `-`/`_` fails badly (Chinese commas/colons inside names,
  `IAA-` prefix, embedded dates, account-number segments). Feed the raw plan-name
  list to the LLM to identify+merge true drama titles. Regex only as a fast path
  for obviously-clean names.
- **Dual granularity, switch by question:** drama-name rollup for
  "哪部剧最能跑"; native full plan name for "某部剧的计划明细".
- **Time = parse from natural language** → adex `--range 7d/30d` or explicit
  `--begin/--end`. "上周"→last Mon–Sun explicit dates; "过去一个月"→`--range 30d`;
  "上个月"→prior calendar month; "今天/实时"→`dashboard`.
- **Metrics:** mirror the management dashboard — 消耗, 变现金额, ROI, 曝光量,
  点击量, CTR, 激活数, 激活成本, CVR, 3秒完播率, 完播率 — plus AI-derived
  ratios (跑量集中度, 平台消耗结构, ROI达标率, 环比). Env-var thresholds for
  "达标/异常" — confirm values with the user, don't hardcode.

## Pitfalls

- **Never auto-select a tenant.** If no default is set, list tenants and let the
  user choose. adex-ks/adex-oe enforce this too.
- adex is **read-only** — query only, no create/modify/delete.
- The `adex-ks`/`adex-oe` SKILL.md files reference `references/*.md` sub-docs
  that are NOT exported by `adex skills read` (only the main SKILL.md is). If a
  future session needs that depth, re-dump or reconstruct from `adex <cmd> --help`.
- Verify 巨量(oe) field names independently before building oe reports — 快手
  uses campaign/unit/creative; 巨量 uses project/unit, and the drama name may
  live in the project name, not the campaign name.
