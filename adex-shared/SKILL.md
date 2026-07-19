---
name: adex-shared
version: 0.4.0
description: "Use when first setting up adex CLI, configuring API credentials, or needing shared flags reference (pagination, jq, date range, output format, error handling). Also covers tenant listing with filters and current user info query."
metadata:
  requires:
    bins: ["adex"]
  cliHelp: "adex --help"
---

# adex CLI 共享规则

**CRITICAL — 本 Skill 是 adex-ks 和 adex-oe 的前置必读。** 安装、认证、共享 flags（分页、日期范围、jq、输出格式、错误处理）全部在此文档中。ks/oe Skill 不重复这些内容。

> **大多数命令支持 `--tenant`（可选）。** 通过 `adex init --tenant <ID>` 或 `adex tenant use <ID>` 设定默认租户后，后续命令无需再传 `--tenant`。仅在需要切换到其他租户时临时传入。

**CRITICAL — 租户选择规则：** 当用户未设定默认租户且未明确指定租户时，必须先执行 `adex tenant --page-all --format table` 列出租户，**将结果展示给用户并由用户选择**，再执行 `adex tenant use <用户选择的ID>`。**禁止 AI 自动选择租户。**

## 快速决策

- 用户要**安装 / 更新 adex CLI** → 见 [安装](#安装) 或 [更新检查](#更新检查)
- 用户要**绑定 API Key / 初始化配置** → `adex init --authorization "Bearer adex_xxx"`，然后 `adex tenant --page-all --format table` 列出租户**展示给用户选择**，再 `adex tenant use <用户选择的ID>`，见 [初始化配置](#初始化配置)
- 用户要**验证 API Key 是否有效** → `adex user`，见 [`user`](references/adex-shared-user.md)
- 用户要**切换默认租户** → `adex tenant use <ID>`，见 [`tenant use`](references/adex-shared-tenant.md)
- 用户要**查看当前租户 ID** → `adex user --jq '.currentTenantId'`，见 [`user`](references/adex-shared-user.md)
- 用户要**列出 / 搜索租户** → `adex tenant --name "关键词" --format table`，见 [`tenant`](references/adex-shared-tenant.md)
- 用户要**查看所有可用命令** → `adex --help` 或见 [命令树总览](#命令树总览)
- 用户要**了解某个命令的 flags** → `adex <command> --help` 或见 [共享 Flags](#共享-flags)
- 用户要**调试请求** → 加 `--dry-run` 打印请求路径和参数，见 [Dry-Run](#dry-run)
- 用户遇到**报错** → 见 [错误处理](#错误处理)，根据 `type` / `subtype` 判断原因
- 用户要**查快手广告数据** → 路由到 [`adex-ks`](../adex-ks/SKILL.md)
- 用户要**查巨量引擎广告数据** → 路由到 [`adex-oe`](../adex-oe/SKILL.md)

## 安装

### 通过 npm 安装（推荐）

```bash
# 安装 CLI
npm install -g @<SCOPE>/adex-cli
```

> **CRITICAL 安装坑（务必先读 [安装排错](references/install-troubleshooting.md)）：**
> 1. **二进制首次运行时从 GitHub 下载，常被限速卡死**（`curl: (28) Operation timed out ... out of 3202823 bytes`）。
>    因为包内 `install.js` 有 `--max-time 120` 硬上限。解法：用 GitHub 加速镜像前缀手动下载 + SHA256 校验 + 放到 `<npm-root-g>/@<SCOPE>/adex-cli/bin/adex`。见排错文档「已知坑 2」。
> 2. **不要跑 `npx skills add https://adex-skills.oss-cn-hangzhou.aliyuncs.com`** —— 该 OSS bucket 返回 `AccessDenied`，
>    而且没必要：adex 二进制已内嵌 `adex-ks`/`adex-oe`/`adex-shared`，用 `adex skills read <name>` 导出即可。见排错文档「已知坑 3」。
> 3. **验证用 `adex --help`，不是 `adex --version`**（该二进制没有 `--version` flag）。

### 从源码安装

```bash
git clone https://github.com/<ORG>/adex-cli.git
cd adex-cli
make install
```

### 验证安装

```bash
adex --help                  # 验证二进制可运行（不要用 --version，无此 flag）
adex user                    # 验证 API Key 是否有效
```

> 若 `adex --help` 卡住或报 "Failed to install adex binary" → 二进制下载被限速，见 [安装排错](references/install-troubleshooting.md)。

## 更新检查

adex 命令执行后，如果检测到新版本，JSON 输出中会包含 `_notice.update` 字段（含 `message`、`command` 等）。
如果 Skills 与当前二进制版本不一致，JSON 输出中会包含 `_notice.skills` 字段。

**当你在输出中看到 `_notice.update` 或 `_notice.skills` 时，完成用户当前请求后，主动提议帮用户更新**：

1. 告知用户当前版本和最新版本号
2. 提议执行更新（同时更新 CLI 和 Skills）：
   ```bash
   adex update
   ```
3. 更新完成后提醒用户：**退出并重新打开 AI Agent** 以加载最新 Skills

**重要**：始终使用 `adex update` 更新，它会同时更新 CLI 和 AI Skills。

**规则**：不要静默忽略更新提示。即使当前任务与更新无关，也应在完成用户请求后补充告知。

### 更新通知抑制

在非 CI 脚本中可通过环境变量抑制通知：

| 环境变量 | 效果 |
|---------|--------|
| `ADEX_NO_UPDATE_NOTIFIER=1` | 抑制 `_notice.update` |
| `ADEX_NO_SKILLS_NOTIFIER=1` | 抑制 `_notice.skills` |

CI 环境自动跳过通知。

## 初始化配置

首次使用前，必须完成以下 3 步：

```bash
# 步骤 1：绑定 API Key
adex init --authorization "Bearer adex_你的token"

# 步骤 2：列出可用租户
adex tenant --page-all --format table

# 步骤 3：由用户选择租户后设定（禁止 AI 自动选择）
adex tenant use <用户选择的ID>
```

**CRITICAL — 步骤 2 和 3 之间，必须将租户列表展示给用户，由用户决定使用哪个租户。禁止 AI 自动选择租户。**

完成后，后续所有命令自动使用该租户，无需再传 `--tenant`。

> 如果用户已知租户 ID，步骤 1 可直接带上 `--tenant`：
> `adex init --authorization "Bearer adex_xxx" --tenant <ID>`，跳过步骤 2 和 3。

也可以传入裸 key（自动补 Bearer 前缀）：

```bash
adex init --authorization adex_你的token --base-url http://你的adex服务地址:端口
```

配置写入 `~/.adex/config.json`（0600 权限）。

### 切换默认租户

```bash
# 设定或切换默认租户
adex tenant use 8
```

切换后所有命令自动使用该租户，无需再传 `--tenant`。

### 环境变量覆盖

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ADEX_API_BASE_URL` | `http://你的adex服务地址:端口` | API base URL |
| `ADEX_AUTHORIZATION` | — | API key（自动去 Bearer 前缀） |
| `ADEX_TENANT_ID` | — | 默认租户 ID（覆盖配置文件中的值） |
| `ADEX_CONFIG_DIR` | `~/.adex` | 配置目录（测试用） |

优先级：`--tenant` 标志 > `ADEX_TENANT_ID` 环境变量 > 配置文件中的 `tenant_id` > 报错。

优先级（base-url）：`--base-url` 标志 > 环境变量 > 配置文件 > 默认值。

## 命令树总览

```
adex
├── init                      # 绑定 API Key（一次性）
├── ks                        # 快手广告数据 → adex-ks Skill
│   ├── accounts              # 广告账户列表
│   ├── campaigns             # 广告计划列表 / top / get
│   ├── units                 # 广告组列表 / top / get
│   ├── creatives             # 创意列表 / top / get
│   ├── account-reports       # 账户报表 daily / summary
│   ├── campaign-reports      # 计划报表 daily / summary
│   ├── unit-reports          # 组报表 daily / summary
│   ├── creative-reports      # 创意报表 daily / summary
│   ├── report-metric-meta    # 报表指标元数据
│   └── dashboard             # 租户级概览
├── oe                        # 巨量引擎广告数据 → adex-oe Skill
│   ├── accounts              # 广告账户列表
│   ├── projects              # 项目列表 / top / get
│   ├── units                 # 单元列表 / top / get
│   ├── account-reports       # 账户报表 daily / summary
│   ├── project-reports       # 项目报表 daily / summary
│   ├── unit-reports          # 单元报表 daily / summary
│   ├── report-metric-meta    # 报表指标元数据
│   ├── dashboard             # 租户级概览
│   └── account-budget-vs-actual # 预算 vs 实际消耗
├── tenant                    # 租户列表 / tenant use → 本 Skill
├── user                      # 当前用户信息 → 本 Skill
├── update                    # 更新 CLI 和 Skill
└── skills                    # 嵌入式 Skill 内容
    ├── list                  # 列出所有 Skill
    └── read                  # 读取 Skill 内容
```

## 共享 Flags

以下 flags 在大多数命令中通用：

| Flag | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--tenant` | int | — | 租户 ID（可选；缺省使用 `adex tenant use` 设定的默认租户，`report-metric-meta` / `tenant` / `user` 不需要） |
| `--page-size` | int | 20 | 每页条数 |
| `--page-token` | string | — | 指定页的游标 token |
| `--page-all` | bool | false | 聚合所有页（自动翻页直到 `hasMore=false`） |
| `--order-by` | string | 因命令而异 | 排序字段 |
| `--order-desc` | bool | true | 降序排序 |
| `--range` | string | — | 相对日期范围（如 `7d` / `4w` / `1m`），优先于 `--begin` / `--end` |
| `--begin` | string | — | 起始日期（YYYY-MM-DD） |
| `--end` | string | — | 结束日期（YYYY-MM-DD） |
| `--jq` | string | — | jq 表达式过滤 JSON 输出 |
| `--format` | enum | `json` | 输出格式：`json` / `pretty` / `table` |
| `--dry-run` | bool | false | 打印请求路径和参数到 stderr，不实际调用 API |
| `--base-url` | string | — | 覆盖 API base URL |

## 分页

列表接口统一使用 `page_token` 游标分页：

```bash
# 单页查询
adex ks accounts --page-size 20

# 翻页（透传上一次响应的 nextPageToken）
adex ks accounts --page-token "abc123"

# 聚合所有页（自动翻页直到 hasMore=false）
adex ks accounts --page-all
```

响应结构（列表接口统一）：

```json
{
  "hasMore": true,
  "nextPageToken": "abc123",
  "items": [...]
}
```

- `hasMore` 为 `true` 时，用 `nextPageToken` 的值传给 `--page-token` 获取下一页
- `--page-all` 会自动翻页并合并所有 `items`，大量数据时注意耗时

## 日期范围

报表、Top-N 和 dashboard 命令支持灵活的日期范围指定：

```bash
# 相对范围（7d=7天, 4w=4周, 1m=1月）
adex ks dashboard --range 30d

# 显式日期
adex ks dashboard --begin 2026-06-01 --end 2026-06-30

# --range 优先于 --begin/--end
```

### 支持的相对范围格式

| 格式 | 含义 | 示例 |
|------|------|------|
| `<N>d` | 最近 N 天（含今天） | `7d` = 最近 7 天 |
| `<N>w` | 最近 N 周（含今天） | `4w` = 最近 4 周（28 天） |
| `<N>m` | 最近 N 个月（含今天） | `1m` = 最近 1 个月 |

> 范围以**今天**为结束日期，向前推算。例如 `7d` 表示 `[今天-6, 今天]` 共 7 天。
> `--range` 优先于 `--begin` / `--end`；两者都不传时，行为因命令而异（daily 可选，summary / top / dashboard 必需）。

## jq 过滤

所有命令支持 `--jq` 对 JSON 输出进行过滤：

```bash
# 提取所有 advertiserId
adex ks accounts --page-all --jq '.items[].advertiserId'

# 提取单个字段
adex user --jq '.username'

# 提取前 5 条的项目名
adex oe projects --page-size 5 --jq '.items[].name'
```

## 输出格式

通过 `--format` 标志控制：

| 格式 | 说明 |
|------|------|
| `json`（默认） | 紧凑 JSON，适合管道处理 |
| `pretty` | 格式化 JSON，适合人工阅读 |
| `table` | 表格输出，适合快速浏览 |

```bash
adex ks accounts --format table
adex ks dashboard --range 30d --format pretty
```

> `--format table` 的列定义因命令而异，详见各 Skill 的 Table 列定义部分。

## Dry-Run

`--dry-run` 打印请求路径和参数到 stderr，不实际调用 API：

```bash
adex ks accounts --dry-run
```

用于调试请求结构、验证参数是否正确。

## 错误处理

错误以 JSON 信封格式输出到 stderr，包含 `type`、`subtype`、`message` 字段，部分错误还包含 `param`（出错的参数名）和 `hint`（修复建议）：

```json
{
  "ok": false,
  "error": {
    "type": "validation",
    "subtype": "invalid_argument",
    "message": "--tenant must be a positive integer",
    "param": "--tenant"
  }
}
```

### 错误分类

| Exit Code | type | subtype | 说明 | 常见原因 |
|-----------|------|---------|------|----------|
| 0 | — | — | 成功 | — |
| 2 | `validation` | `invalid_argument` | 参数校验失败 | `--tenant` 缺失或非正整数、日期格式错误 |
| 2 | `validation` | `missing_config` | 配置缺失 | 未执行 `adex init` 绑定 API Key |
| 3 | `unauthorized` | `auth_required` | 认证失败 | API Key 无效或过期 |
| 4 | `network` | `network_transport` | 网络错误 | 无法连接 API 服务器、DNS 解析失败 |
| 5 | `api` | `api_error` | API 返回非 2xx | 服务端错误、权限不足、资源不存在 |
| 1 | `internal` | `unknown` | 内部错误 | 意外异常，通常是 bug |

### 错误处理建议

- `validation` → 检查 `param` 字段指向的 flag，按 `hint` 修正
- `missing_config` → 执行 `adex init --authorization "Bearer <key>"`
- `unauthorized` → API Key 可能过期，重新执行 `adex init`
- `network` → 检查网络连接和 `--base-url` 是否正确
- `api` → 查看返回的 HTTP `code` 和 `message`，可能是权限不足或资源不存在

## tenant — 租户列表 / 切换默认租户

不需要 `--tenant` flag。支持名称模糊匹配和状态精确过滤。详见 [`tenant`](references/adex-shared-tenant.md)。

```bash
# 列出所有租户
adex tenant --page-size 20

# 按名称模糊过滤
adex tenant --name acme --format table

# 按状态过滤
adex tenant --status active --page-size 50

# 聚合所有页
adex tenant --page-all --jq '.items[].id'

# 设定默认租户（后续命令无需 --tenant）
adex tenant use <ID>
```

### Table 列

| 列 | 字段 |
|----|------|
| ID | `id` |
| Name | `name` |
| Status | `status` |
| Created By | `createdBy` |
| Created At | `createdAt` |
| Updated At | `updatedAt` |

## user — 当前用户信息

不需要 `--tenant` flag。通过 Bearer API Key 自动解析当前用户。详见 [`user`](references/adex-shared-user.md)。

```bash
# JSON 输出（默认）
adex user

# 表格输出
adex user --format table

# 提取当前租户 ID（用于其他命令的 --tenant 参数）
adex user --jq '.currentTenantId'
```

### Table 列

| 列 | 字段 |
|----|------|
| ID | `id` |
| Username | `username` |
| Name | `name` |
| Status | `status` |
| Current Tenant | `currentTenantId` |
| Created At | `createdAt` |
| Updated At | `updatedAt` |

## 常见工作流

### 工作流 1：首次使用（3 步初始化）

```bash
# 1. 安装 CLI
npm install -g @<SCOPE>/adex-cli

# 2. 绑定 API Key
adex init --authorization "Bearer adex_你的token"

# 3. 列出租户，找到目标租户 ID
adex tenant --page-all --format table

# 4. 设定默认租户（由用户选择，禁止 AI 自动选择）
adex tenant use <ID>

# 后续命令无需 --tenant
adex ks accounts
adex oe dashboard --range 30d
```

### 工作流 2：切换默认租户

```bash
# 查看可用租户
adex tenant --format table

# 切换默认租户
adex tenant use <ID>

# 后续命令自动使用新租户
adex ks accounts
```

### 工作流 3：调试请求

```bash
# 用 --dry-run 查看请求路径和参数
adex ks accounts --dry-run

# 用 --format pretty 查看完整响应
adex ks dashboard --range 30d --format pretty

# 用 --jq 提取特定字段
adex ks accounts --page-size 3 --jq '.items[0]'
```

## Skill 路由

| 用户意图 | 路由到 Skill |
|----------|-------------|
| 快手广告数据查询 | [`adex-ks`](../adex-ks/SKILL.md) |
| 巨量引擎广告数据查询 | [`adex-oe`](../adex-oe/SKILL.md) |
| 安装、配置、认证、共享 flags、租户管理、用户信息 | 本 Skill |

## 不在本 skill 范围

- 快手广告数据查询（账户、计划、组、创意、报表、排名） → [`../adex-ks/SKILL.md`](../adex-ks/SKILL.md)
- 巨量引擎广告数据查询（账户、项目、单元、报表、排名、预算对比） → [`../adex-oe/SKILL.md`](../adex-oe/SKILL.md)
- 创建 / 修改 / 删除广告投放对象 → 本 CLI 仅提供查询功能，不支持写入操作