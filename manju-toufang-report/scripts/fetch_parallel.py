#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行拉取快手+巨量投放数据（A方案：实时拉取+并行加速）。
两平台查询用线程并行，总耗时 = max(各查询) 而非累加。

实测耗时（租户1，上周范围）：
  dashboard 模式: ~0.6秒（大盘/平台对比，秒回）
  drama 模式:     ~13.5秒（剧集 page-all，需给用户进度提示）

用法:
  python3 fetch_parallel.py <begin> <end> [mode]
  mode: dashboard | drama | both  (默认 both)

输出到 /tmp/：
  ks_dash.json   快手大盘（summary.metrics/ratios + accountRankings）
  oe_total.json  巨量总计（project summary 不分组，含 metrics）—— 因 oe dashboard 有bug走此降级
  ks_camps.json  快手计划汇总 page-all（剧集用，groupName=计划名）
  oe_projs.json  巨量项目汇总 page-all（剧集用，groupName=项目名）

注意：
  - 数据实时拉取，不缓存，保证与后台看板一致（投放数据滚动更新，缓存会导致数字对不上）
  - 每个查询有 120s 超时；返回状态含 OK/API_ERROR/BAD_JSON/TIMEOUT
  - 巨量 dashboard/account-reports 有后端 bug(is_final)，本脚本已避开，用 project summary 降级
"""
import subprocess
import sys
import time
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

TMP = tempfile.gettempdir()


def run(cmd, out):
    t0 = time.time()
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        open(out, 'w').write(r.stdout)
        try:
            d = json.loads(r.stdout)
            if isinstance(d, dict) and d.get('ok') is False:
                return (out, 'API_ERROR', d.get('error', {}).get('message', '')[:80], time.time() - t0)
        except Exception:
            return (out, 'BAD_JSON', (r.stderr or r.stdout)[:80], time.time() - t0)
        return (out, 'OK', f'{len(r.stdout)}B', time.time() - t0)
    except subprocess.TimeoutExpired:
        return (out, 'TIMEOUT', '', time.time() - t0)


def main():
    if len(sys.argv) < 3:
        print('用法: python3 fetch_parallel.py <begin> <end> [dashboard|drama|both]')
        sys.exit(1)
    begin, end = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'both'
    dr = f'--begin {begin} --end {end}'

    jobs = []
    if mode in ('dashboard', 'both'):
        jobs += [
            (f'adex ks dashboard {dr} --format json', os.path.join(TMP, 'ks_dash.json')),
            (f'adex oe project-reports summary {dr} --format json', os.path.join(TMP, 'oe_total.json')),
        ]
    if mode in ('drama', 'both'):
        jobs += [
            (f'adex ks campaign-reports summary {dr} --group-by campaign_id --order-by charge --order-desc --page-all --format json', os.path.join(TMP, 'ks_camps.json')),
            (f'adex oe project-reports summary {dr} --group-by project_id --order-by charge --order-desc --page-all --format json', os.path.join(TMP, 'oe_projs.json')),
        ]

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda j: run(j[0], j[1]), jobs))
    wall = time.time() - t0

    print(f'并行总耗时: {wall:.2f}秒')
    for out, status, info, dt in results:
        print(f'  [{status}] {out}  {info}  ({dt:.2f}s)')
    bad = [r for r in results if r[1] != 'OK']
    if bad:
        print('⚠️ 部分数据源异常，报告需注明或走降级:', [b[0] for b in bad])


if __name__ == '__main__':
    main()
