# adex 命令速查

租户已锁定租户1，所有命令**无需** `--tenant`。若报"未设默认租户"→ `adex tenant use 1`。

## 通用 flags

| flag | 作用 |
|------|------|
| `--range 7d/30d/4w/1m` | 滚动相对范围 |
| `--begin YYYY-MM-DD --end YYYY-MM-DD` | 绝对日期范围（自然周/月用这个） |
| `--group-by <dim>` | 汇总分组维度；留空=单条总计 |
| `--order-by charge --order-desc` | 按消耗降序 |
| `--page-all` | 拉全部页（账户多时慢，剧集聚合需要它） |
| `--page-size N` | 每页条数（默认20） |
| `--format json/table/pretty` | 输出格式；程序处理用 json，人看用 table |
| `--jq '<expr>'` | jq 过滤 JSON |
| `--dry-run` | 只打印请求，验证日期/参数用 |

---

## 快手 ks（全部正常）

```bash
# 大盘概览（含 accountTotal / summary.metrics|ratios / accountRankings[10]）
adex ks dashboard --range 7d

# 计划汇总（剧集维度取数：groupName=计划名→AI提剧名）
adex ks campaign-reports summary --range 30d --group-by campaign_id --order-by charge --order-desc --page-all

# 计划 Top-N 排名
adex ks campaigns top --range 30d --metric charge --limit 10

# 账户汇总
adex ks account-reports summary --range 7d

# 计划/组/创意列表（下钻明细、按剧名关键词筛选）
adex ks campaigns --page-all
adex ks units --campaign <ID>
adex ks creatives --unit <ID>

# 日报表（看趋势）
adex ks account-reports daily --range 30d
adex ks campaign-reports daily --range 30d --campaign <ID>
```

层级：账户 → 计划campaign → 组unit → 创意creative

---

## 巨量 oe（账户级/dashboard 有bug，见下）

```bash
# ❌ 有 bug（500 is_final）——不要用：
#   adex oe dashboard
#   adex oe account-reports summary

# ✅ 巨量大盘降级方案：项目汇总不分组=总计
adex oe project-reports summary --range 7d

# ✅ 项目汇总（剧集维度取数：groupName=项目名→AI提剧名）
adex oe project-reports summary --range 30d --group-by project_id --order-by charge --order-desc --page-all

# ✅ 项目列表 / 单元
adex oe projects --page-all
adex oe units --range 30d

# ✅ 项目 Top-N
adex oe units top --range 30d --metric convert_cnt --limit 20

# ✅ 预算vs实际（图1"前后端配比"雏形，可选）
adex oe account-budget-vs-actual --range 30d
```

层级：账户 → 项目project → 单元unit

---

## 时间范围计算（自然周/月）

`--range 7d` 是**滚动7天**，≠"上周"自然周。自然周期先用 `date` 算精确边界。
**⚠️ 用 `DOW` 方案，不要用 `date -d 'monday-1week'`（实测会算反，给出上周一>上周日）：**

```bash
# 上周（周一~周日）—— 已验证正确
DOW=$(date +%u)                                   # 1=周一..7=周日
THIS_MON=$(date -d "-$((DOW-1)) days" +%F)         # 本周一
LAST_MON=$(date -d "$THIS_MON -7 days" +%F)        # 上周一
LAST_SUN=$(date -d "$THIS_MON -1 day" +%F)         # 上周日
# 例：今天2026-07-18(周六) → 本周一07-13, 上周 07-06~07-12 ✓

# 上月（1号~月末）
THIS_M1=$(date +%Y-%m-01)
LAST_MEND=$(date -d "$THIS_M1 -1 day" +%F)          # 上月最后一天
LAST_M1=$(date -d "$LAST_MEND" +%Y-%m-01)          # 上月第一天

# 本月至今
THIS_M1=$(date +%Y-%m-01); TODAY=$(date +%F)

# 昨天
Y=$(date -d yesterday +%F)
```
不确定时把算出的 begin/end 报给用户核对，或 `--dry-run` 打印请求确认。

---

## 常用取数脚本模式

```bash
# 一次性拉全数据到临时文件再本地处理（避免管道被安全拦截）
adex ks dashboard --range 7d --format json > /tmp/ks_dash.json
adex ks campaign-reports summary --range 7d --group-by campaign_id --order-by charge --order-desc --page-all --format json > /tmp/ks_camps.json
adex oe project-reports summary --range 7d --group-by project_id --order-by charge --order-desc --page-all --format json > /tmp/oe_projs.json
adex oe project-reports summary --range 7d --format json > /tmp/oe_total.json   # 巨量总计降级
```
再用 read_file / execute_code 读取 /tmp/*.json 做聚合。
