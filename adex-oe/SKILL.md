---
name: adex-oe
version: 0.4.0
description: "巨量引擎广告数据查询：账户、项目、单元的列表/详情/Top-N 排名，日/汇总报表，指标元数据，租户级概览，预算 vs 实际消耗对比。当用户需要查询巨量/Oceanengine 广告投放数据、消耗、报表或排名时使用。"
metadata:
  requires:
    bins: ["adex"]
  cliHelp: "adex oe --help"
---

# oe — 巨量引擎广告数据

**CRITICAL — 开始前 MUST 先用 Read 工具读取 `../adex-shared/SKILL.md`，其中包含安装、认证、共享 flags（分页、日期范围、jq、输出格式、错误处理）。**

> **所有命令支持 `--tenant`（可选）。** 通过 `adex init --tenant <ID>` 或 `adex tenant use <ID>` 设定默认租户后，后续命令无需再传 `--tenant`。`report-metric-meta` 不需要租户。

**CRITICAL — 未设定默认租户时，禁止 AI 自动选择租户。** 必须先回到 `adex-shared` 执行 `adex tenant --page-all --format table`，**展示租户列表让用户选择**，再 `adex tenant use <用户选择的ID>`。

## 快速决策

- 用户要**看整体投放概览 / 大盘数据** → `adex oe dashboard --tenant <ID> --range 30d`，详见 [`dashboard`](references/adex-oe-dashboard.md)
- 用户要**查账户列表**或按名称/状态筛选账户 → `adex oe accounts --tenant <ID>`，详见 [`accounts`](references/adex-oe-accounts.md)
- 用户要**查项目/单元列表** → `adex oe projects|units --tenant <ID>`，详见对应 reference 文档
- 用户要**看消耗排名 Top-N** → `adex oe projects|units top --tenant <ID> --range 30d --metric charge --limit 10`，详见 [Top-N 分析工作流](references/adex-oe-workflow-top-analysis.md)
- 用户要**看日报表**（按天看趋势） → `adex oe <resource>-reports daily --tenant <ID> --range 30d`，详见 [`reports`](references/adex-oe-reports.md)
- 用户要**看汇总报表**（按维度分组汇总） → `adex oe <resource>-reports summary --tenant <ID> --range 30d --group-by <dimension>`，详见 [`reports`](references/adex-oe-reports.md)
- 用户要**查某个项目/单元的详情** → `adex oe projects|units get <ID> --tenant <ID>`
- 用户要**查报表有哪些指标字段** → `adex oe report-metric-meta --level <account|project|unit>`，详见 [`metric-meta`](references/adex-oe-metric-meta.md)
- 用户要**对比预算与实际消耗** → `adex oe account-budget-vs-actual --tenant <ID> --range 30d`，详见 [`budget-vs-actual`](references/adex-oe-budget-vs-actual.md)
- 用户说**"最近 7 天消耗怎么样"** → 先 `dashboard` 看大盘，再 `account-reports daily --range 7d` 看日趋势
- 用户说**"哪个项目消耗最多"** → `projects top --tenant <ID> --range 30d --metric charge --limit 10`
- 用户说**"导出数据"** → 用 `--format json` 或 `--jq` 提取需要的字段，CLI 本身不提供导出文件功能

## 命令总览

| 命令 | 说明 | API | 参考 |
|------|------|-----|------|
| `oe accounts` | 广告账户列表 | `GET /v1/oe/ad-accounts` | [`accounts`](references/adex-oe-accounts.md) |
| `oe projects` | 项目列表 | `GET /v1/oe/projects` | [`projects`](references/adex-oe-projects.md) |
| `oe projects top` | 项目 Top-N 排名 | `GET /v1/oe/projects/top` | [`projects`](references/adex-oe-projects.md) |
| `oe projects get <id>` | 项目详情 | `GET /v1/oe/projects/{id}` | [`projects`](references/adex-oe-projects.md) |
| `oe units` | 单元列表 | `GET /v1/oe/units` | [`units`](references/adex-oe-units.md) |
| `oe units top` | 单元 Top-N 排名 | `GET /v1/oe/units/top` | [`units`](references/adex-oe-units.md) |
| `oe units get <id>` | 单元详情 | `GET /v1/oe/units/{id}` | [`units`](references/adex-oe-units.md) |
| `oe account-reports daily` | 账户日报表 | `GET /v1/oe/account-reports/daily` | [`reports`](references/adex-oe-reports.md) |
| `oe account-reports summary` | 账户汇总报表 | `GET /v1/oe/account-reports/summary` | [`reports`](references/adex-oe-reports.md) |
| `oe project-reports daily` | 项目日报表 | `GET /v1/oe/project-reports/daily` | [`reports`](references/adex-oe-reports.md) |
| `oe project-reports summary` | 项目汇总报表 | `GET /v1/oe/project-reports/summary` | [`reports`](references/adex-oe-reports.md) |
| `oe unit-reports daily` | 单元日报表 | `GET /v1/oe/unit-reports/daily` | [`reports`](references/adex-oe-reports.md) |
| `oe unit-reports summary` | 单元汇总报表 | `GET /v1/oe/unit-reports/summary` | [`reports`](references/adex-oe-reports.md) |
| `oe report-metric-meta` | 报表指标元数据 | `GET /v1/oe/report-metric-meta` | [`metric-meta`](references/adex-oe-metric-meta.md) |
| `oe dashboard` | 租户级概览 | `GET /v1/oe/dashboard` | [`dashboard`](references/adex-oe-dashboard.md) |
| `oe account-budget-vs-actual` | 预算 vs 实际消耗 | `GET /v1/oe/account-budget-vs-actual` | [`budget-vs-actual`](references/adex-oe-budget-vs-actual.md) |

## 常见工作流

### 工作流 1：投放概览 → 下钻分析

用户想了解近期投放情况，从大盘到明细逐层下钻：

```bash
# 1. 看大盘概览（账户统计 + 消耗汇总 + 账户排名）
adex oe dashboard --range 30d

# 2. 看账户日报表趋势
adex oe account-reports daily --range 30d --format table

# 3. 看消耗 Top-N 项目
adex oe projects top --range 30d --metric charge --limit 10

# 4. 对 Top 项目下钻看日报表
adex oe project-reports daily --range 30d --project <PROJECT_ID> --format table
```

详见 [Top-N 分析工作流](references/adex-oe-workflow-top-analysis.md)。

### 工作流 2：查看报表可用指标

用户不确定报表有哪些指标字段时，先查指标元数据：

```bash
# 1. 查询 project 层级可用指标
adex oe report-metric-meta --level project --enabled 1 --page-size 50

# 2. 用返回的 field 名称作为 --order-by 或 --metric 参数
adex oe project-reports summary --range 30d --group-by project_id --order-by charge --order-desc
```

### 工作流 3：按层级筛选下钻

从项目 → 单元逐层筛选：

```bash
# 1. 查项目列表
adex oe projects --opt-status ENABLE --format table

# 2. 用项目 ID 筛选单元列表
adex oe units --project <PROJECT_ID> --format table
```

### 工作流 4：预算 vs 实际消耗对比

用户想了解预算使用情况，对比日预算与实际日均消耗：

```bash
# 全部账户的预算使用情况
adex oe account-budget-vs-actual --range 30d --format table

# 单个账户的预算使用情况
adex oe account-budget-vs-actual --advertiser <ADVERTISER_ID> --range 30d
```

## 资源层级关系

巨量引擎广告使用两级结构：**项目 (project) → 单元 (unit/promotion)**，所有资源都归属于**广告账户 (account)**。

```
账户 (account)
└── 项目 (project)
    └── 单元 (unit / promotion)
```

- 列表命令支持按上级 ID 过滤：`--project`、`--advertiser`
- 报表命令同样支持按上级 ID 过滤
- `get` 命令使用各自的路径参数：project_id、promotion_id

> **与快手的区别：** 快手广告为三级结构（计划 → 组 → 创意），巨量引擎为两级结构（项目 → 单元），没有创意层级。

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
| `accounts` | id, advertiserId, accountName, accountType, authStatus, deliveryStatus, activeStatus, balance, budget |
| `projects` | id, projectId, name, advertiserId, optStatus, statusFirst, deliveryMode, landingType |
| `units` | id, promotionId, name, projectId, advertiserId, optStatus, statusFirst, learningPhase |
| `account-reports daily` | id, advertiserId, statDate, statHour, charge |
| `project-reports daily` | id, advertiserId, projectId, projectName, statDate, charge |
| `unit-reports daily` | id, advertiserId, promotionId, promotionName, statDate, charge |
| `summary / top` | groupKey, groupName, charge, rowCount |
| `report-metric-meta` | id, level, field, label, groupName, agg, valueType, sortOrder, enabled |
| `account-budget-vs-actual` | advertiserId, accountName, budgetMode, budget, totalCharge, days, avgDailyCharge, budgetUsageRate, balance |

## 不在本 skill 范围

- 快手广告数据查询 → `../adex-ks/SKILL.md`
- 安装、配置、认证、共享 flags 参考 → `../adex-shared/SKILL.md`
- 租户管理、用户信息查询 → `../adex-shared/SKILL.md`
- 创建 / 修改 / 删除广告投放对象 → 本 CLI 仅提供查询功能，不支持写入操作