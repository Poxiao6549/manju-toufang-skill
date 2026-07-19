---
name: adex-ks
version: 0.4.0
description: "快手广告数据查询：账户、计划、组、创意的列表/详情/Top-N 排名，日/汇总报表，指标元数据，租户级概览。当用户需要查询快手广告投放数据、消耗、报表或排名时使用。"
metadata:
  requires:
    bins: ["adex"]
  cliHelp: "adex ks --help"
---

# ks — 快手广告数据

**CRITICAL — 开始前 MUST 先用 Read 工具读取 `../adex-shared/SKILL.md`，其中包含安装、认证、共享 flags（分页、日期范围、jq、输出格式、错误处理）。**

> **所有命令支持 `--tenant`（可选）。** 通过 `adex init --tenant <ID>` 或 `adex tenant use <ID>` 设定默认租户后，后续命令无需再传 `--tenant`。`report-metric-meta` 不需要租户。

**CRITICAL — 未设定默认租户时，禁止 AI 自动选择租户。** 必须先回到 `adex-shared` 执行 `adex tenant --page-all --format table`，**展示租户列表让用户选择**，再 `adex tenant use <用户选择的ID>`。

## 快速决策

- 用户要**看整体投放概览 / 大盘数据** → `adex ks dashboard --tenant <ID> --range 30d`，详见 [`dashboard`](references/adex-ks-dashboard.md)
- 用户要**查账户列表**或按名称/状态筛选账户 → `adex ks accounts --tenant <ID>`，详见 [`accounts`](references/adex-ks-accounts.md)
- 用户要**查计划/组/创意列表** → `adex ks campaigns|units|creatives --tenant <ID>`，详见对应 reference 文档
- 用户要**看消耗排名 Top-N** → `adex ks campaigns|units|creatives top --tenant <ID> --range 30d --metric charge --limit 10`，详见 [Top-N 分析工作流](references/adex-ks-workflow-top-analysis.md)
- 用户要**看日报表**（按天看趋势） → `adex ks <resource>-reports daily --tenant <ID> --range 30d`，详见 [`reports`](references/adex-ks-reports.md)
- 用户要**看汇总报表**（按维度分组汇总） → `adex ks <resource>-reports summary --tenant <ID> --range 30d --group-by <dimension>`，详见 [`reports`](references/adex-ks-reports.md)
- 用户要**查某个计划/组/创意的详情** → `adex ks campaigns|units|creatives get <ID> --tenant <ID>`
- 用户要**查报表有哪些指标字段** → `adex ks report-metric-meta --level <account|campaign|unit|creative>`，详见 [`metric-meta`](references/adex-ks-metric-meta.md)
- 用户说**"最近 7 天消耗怎么样"** → 先 `dashboard` 看大盘，再 `account-reports daily --range 7d` 看日趋势
- 用户说**"哪个计划消耗最多"** → `campaigns top --tenant <ID> --range 30d --metric charge --limit 10`
- 用户说**"导出数据"** → 用 `--format json` 或 `--jq` 提取需要的字段，CLI 本身不提供导出文件功能

## 命令总览

| 命令 | 说明 | API | 参考 |
|------|------|-----|------|
| `ks accounts` | 广告账户列表 | `GET /v1/ks/ad-accounts` | [`accounts`](references/adex-ks-accounts.md) |
| `ks campaigns` | 广告计划列表 | `GET /v1/ks/campaigns` | [`campaigns`](references/adex-ks-campaigns.md) |
| `ks campaigns top` | 计划 Top-N 排名 | `GET /v1/ks/campaigns/top` | [`campaigns`](references/adex-ks-campaigns.md) |
| `ks campaigns get <id>` | 计划详情 | `GET /v1/ks/campaigns/{id}` | [`campaigns`](references/adex-ks-campaigns.md) |
| `ks units` | 广告组列表 | `GET /v1/ks/units` | [`units`](references/adex-ks-units.md) |
| `ks units top` | 组 Top-N 排名 | `GET /v1/ks/units/top` | [`units`](references/adex-ks-units.md) |
| `ks units get <id>` | 组详情 | `GET /v1/ks/units/{id}` | [`units`](references/adex-ks-units.md) |
| `ks creatives` | 创意列表 | `GET /v1/ks/creatives` | [`creatives`](references/adex-ks-creatives.md) |
| `ks creatives top` | 创意 Top-N 排名 | `GET /v1/ks/creatives/top` | [`creatives`](references/adex-ks-creatives.md) |
| `ks creatives get <biz_key>` | 创意详情 | `GET /v1/ks/creatives/{biz_key}` | [`creatives`](references/adex-ks-creatives.md) |
| `ks account-reports daily` | 账户日报表 | `GET /v1/ks/account-reports/daily` | [`reports`](references/adex-ks-reports.md) |
| `ks account-reports summary` | 账户汇总报表 | `GET /v1/ks/account-reports/summary` | [`reports`](references/adex-ks-reports.md) |
| `ks campaign-reports daily` | 计划日报表 | `GET /v1/ks/campaign-reports/daily` | [`reports`](references/adex-ks-reports.md) |
| `ks campaign-reports summary` | 计划汇总报表 | `GET /v1/ks/campaign-reports/summary` | [`reports`](references/adex-ks-reports.md) |
| `ks unit-reports daily` | 组日报表 | `GET /v1/ks/unit-reports/daily` | [`reports`](references/adex-ks-reports.md) |
| `ks unit-reports summary` | 组汇总报表 | `GET /v1/ks/unit-reports/summary` | [`reports`](references/adex-ks-reports.md) |
| `ks creative-reports daily` | 创意日报表 | `GET /v1/ks/creative-reports/daily` | [`reports`](references/adex-ks-reports.md) |
| `ks creative-reports summary` | 创意汇总报表 | `GET /v1/ks/creative-reports/summary` | [`reports`](references/adex-ks-reports.md) |
| `ks report-metric-meta` | 报表指标元数据 | `GET /v1/ks/report-metric-meta` | [`metric-meta`](references/adex-ks-metric-meta.md) |
| `ks dashboard` | 租户级概览 | `GET /v1/ks/dashboard` | [`dashboard`](references/adex-ks-dashboard.md) |

## 常见工作流

### 工作流 1：投放概览 → 下钻分析

用户想了解近期投放情况，从大盘到明细逐层下钻：

```bash
# 1. 看大盘概览（账户统计 + 消耗汇总 + 账户排名）
adex ks dashboard --range 30d

# 2. 看账户日报表趋势
adex ks account-reports daily --range 30d --format table

# 3. 看消耗 Top-N 计划
adex ks campaigns top --range 30d --metric charge --limit 10

# 4. 对 Top 计划下钻看日报表
adex ks campaign-reports daily --range 30d --campaign <CAMPAIGN_ID> --format table
```

详见 [Top-N 分析工作流](references/adex-ks-workflow-top-analysis.md)。

### 工作流 2：查看报表可用指标

用户不确定报表有哪些指标字段时，先查指标元数据：

```bash
# 1. 查询 campaign 层级可用指标
adex ks report-metric-meta --level campaign --enabled 1 --page-size 50

# 2. 用返回的 field 名称作为 --order-by 或 --metric 参数
adex ks campaign-reports summary --range 30d --group-by campaign_id --order-by charge --order-desc
```

### 工作流 3：按层级筛选下钻

从计划 → 组 → 创意逐层筛选：

```bash
# 1. 查计划列表
adex ks campaigns --put-status 1 --format table

# 2. 用计划 ID 筛选组列表
adex ks units --campaign <CAMPAIGN_ID> --format table

# 3. 用组 ID 筛选创意列表
adex ks creatives --unit <UNIT_ID> --format table
```

## 资源层级关系

快手广告使用三级结构：**计划 (campaign) → 组 (unit) → 创意 (creative)**，所有资源都归属于**广告账户 (account)**。

```
账户 (account)
└── 计划 (campaign)
    └── 组 (unit)
        └── 创意 (creative)
```

- 列表命令支持按上级 ID 过滤：`--campaign`、`--unit`、`--advertiser`
- 报表命令同样支持按上级 ID 过滤
- `get` 命令使用各自的路径参数：campaign_id、unit_id、creative 的 biz_key（如 `p:29637782154`）

## 共享 Flags

以下 flags 在所有命令中通用（详见 `../adex-shared/SKILL.md`）：

| Flag | 说明 | 默认值 |
|------|------|--------|
| `--tenant` | 租户 ID（可选；缺省使用 `adex tenant use` 设定的默认租户） | — |
| `--page-size` | 每页条数 | 20 |
| `--page-token` | 指定页游标 | — |
| `--page-all` | 聚合所有页 | false |
| `--order-by` | 排序字段 | 因命令而异 |
| `--order-desc` | 降序排序 | true |
| `--range` | 相对日期范围（如 7d/4w/1m） | — |
| `--begin` | 起始日期（YYYY-MM-DD） | — |
| `--end` | 结束日期（YYYY-MM-DD） | — |
| `--jq` | jq 表达式过滤 JSON 输出 | — |
| `--format` | 输出格式：json / pretty / table | json |
| `--dry-run` | 打印请求但不执行 | false |

## Table 列定义

`--format table` 时各命令显示的列：

| 命令 | 列 |
|------|----|
| `accounts` | id, advertiserId, accountName, accountType, authStatus, deliveryStatus, activeStatus, balance |
| `campaigns` | id, campaignId, campaignName, advertiserId, putStatus, status, campaignType |
| `units` | id, unitId, unitName, campaignId, advertiserId, putStatus, status |
| `creatives` | id, creativeId, creativeName, unitId, campaignId, advertiserId, putStatus, status |
| `account-reports daily` | id, advertiserId, accountName, statDate, statHour, charge |
| `campaign-reports daily` | id, advertiserId, campaignId, campaignName, statDate, charge |
| `unit-reports daily` | id, advertiserId, unitId, unitName, statDate, charge |
| `creative-reports daily` | id, advertiserId, creativeId, creativeName, statDate, charge |
| `summary / top` | groupKey, groupName, charge, rowCount |
| `report-metric-meta` | id, level, field, label, groupName, agg, valueType, sortOrder, enabled, sortable |

## 不在本 skill 范围

- 巨量引擎广告数据查询 → `../adex-oe/SKILL.md`
- 安装、配置、认证、共享 flags 参考 → `../adex-shared/SKILL.md`
- 租户管理、用户信息查询 → `../adex-shared/SKILL.md`
- 创建 / 修改 / 删除广告投放对象 → 本 CLI 仅提供查询功能，不支持写入操作