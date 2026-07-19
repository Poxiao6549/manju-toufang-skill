# 指标口径与字段对照

管理层看的核心指标，及其在 adex 返回 JSON 里的字段名。dashboard 的 `summary`/`accountRankings[]` 下有 `metrics`（原子值）和 `ratios`（已算好的比率）两个对象。

---

## 一、管理层核心指标（对齐数据看板）

| 中文指标 | 快手字段 | 位置 | 单位/处理 |
|---------|---------|------|----------|
| 消耗 | `charge` | metrics | 元，保留2位 |
| IAA变现金额 | `minigame_iaa_purchase_amount` | metrics | 元 |
| ROI | `minigame_iaa_purchase_roi` | ratios | 小数，保留3位（如0.318） |
| 曝光量 | `ad_show` | metrics | 整数，千分位 |
| 广告点击量 | `aclick` | metrics | 整数 |
| CTR（点击率） | `action_ratio` / `material_click_ratio` | ratios | ×100 加% |
| 激活数 | `activation` | metrics | 整数 |
| 激活成本 | `action_cost` | ratios | 元 |
| 转化数 | `conversion_num` | metrics | 整数 |
| CVR（转化率） | `conversion_ratio` | ratios | ×100 加% |
| 3秒播放率 | `play_3s_ratio` | ratios | ×100 加%（可信✓） |
| 5秒播放率 | `play_5s_ratio` | ratios | ×100 加%（可信✓） |
| 完播率 | ⚠️`played_end`/`ad_show` **自己算** | metrics | 见下方警告 |
| 播放数 | `played_num` | metrics | 整数 |
| 千次曝光成本 | `impression_1k_cost` | ratios | 元 |
| App调起数 | `event_app_invoked` | metrics | 整数 |

> **比率字段一律是小数**：`conversion_ratio: 0.179` → 显示 `17.9%`；`play_3s_ratio: 0.686` → `68.6%`。ROI 习惯保留小数原样（0.318）不转百分比。

> **⚠️ 完播率坑（重要）**：不要用 adex 的 `play_end_ratio`——它分母错误（用了 `played_num` 而非曝光），实测会给出 228% 这种荒谬值。**完播率必须自己算 = `played_end / ad_show`**（完整播放数/曝光量），实测约16.9%才合理。同理 75%播放率 = `ad_photo_played_75percent / ad_show`。播放漏斗统一以 `ad_show`（曝光）为分母。`play_3s_ratio`/`play_5s_ratio` 分母正确可直接用。

---

## 二、巨量字段说明

巨量 `oe` 的字段命名与快手**不完全相同**。因巨量 dashboard 当前有 bug（见 SKILL.md 已知问题），主要通过 `oe project-reports summary` 取数：
- summary 返回的分组行含 `charge`（消耗）、`groupName`（项目名=剧名来源）、`rowCount`
- 需要更多巨量指标时，用 `adex oe report-metric-meta --level project` 查字段名，或 `adex oe project-reports summary` 的完整 JSON 里看有哪些字段
- 巨量常见字段：`stat_cost`/`charge`（消耗）、`show_cnt`（展示）、`click_cnt`（点击）、`convert_cnt`（转化）、`active`（激活）等——**实际字段以 API 返回为准，取数前先看一条 JSON 确认**

> 快手↔巨量做平台对比时，只对比两边都有的可比指标（消耗、变现、ROI、激活、转化），字段名不同但业务含义对齐即可。

---

## 三、AI 派生指标（图2批注"可让AI裂变"）

基于原子指标派生，供管理层视角。**本期只算这些明确的，不主观编造达标判断**（无阈值标准）：

| 派生指标 | 算法 | 用途 |
|---------|------|------|
| 平台消耗占比 | 各平台charge / 总charge ×100% | 看快手vs巨量投放结构 |
| 跑量集中度 | Top3剧集消耗 / 总消耗 ×100% | 看消耗是否集中在少数剧 |
| 剧集平均ROI | 各剧ROI，或 总变现/总消耗 | 整体变现效率 |
| 环比变化 | (当期 - 上期) / 上期 ×100% | **仅当用户问及趋势/环比时算**，需额外拉上一周期数据 |
| 单剧计划数 | 该剧下计划/项目条数 | 看测试铺量程度 |

**环比说明**：adex 报表不直接返回环比。要环比时，拉两段时间（当期 + 等长上期）分别聚合后手工相减。用户没问趋势就不主动算，避免多余拉数。

---

## 四、金额/数字格式规范

- 金额：`¥12,345.67`（千分位 + 2位小数）
- 大整数：`27,146`（千分位）
- 百分比：`92.5%`（1位小数）
- ROI：`0.318`（3位小数，不转百分比）
- 空值/0消耗：显示"—"或"无消耗"，不显示 `¥0.00` 误导

---

## 五、指标元数据查询（需要更多字段时）

```bash
# 快手计划级所有可用指标（580+字段）
adex ks report-metric-meta --level campaign --page-size 300 --format table

# 巨量项目级指标
adex oe report-metric-meta --level project --page-size 200 --format table
```
`--level` 可选 account / campaign(ks) / project(oe) / unit / creative(ks)。
enabled=true 的才是当前启用的指标。
