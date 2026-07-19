#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧名归一化 + 聚合（方案B — 规则打底版）

用途：把 adex 计划名/项目名做"粗归一化"，把 ~758 条计划聚合到 ~137 部剧，
     秒级、免费。规则搞不定的边界情况（数字是剧名还是批次）由 AI 复核精修。

用法（二选一）：
  A. 直接喂两个 adex 输出文件（推荐，自动合并两平台）：
       python3 normalize_drama.py --ks /tmp/ks_camps.json --oe /tmp/oe_projs.json
  B. 喂已合并的 plans.json（格式 [{charge,name,platform},...]）：
       python3 normalize_drama.py /tmp/plans.json

输出 JSON：{total_charge, plan_count, drama_count, dramas:[{drama,charge,ks,oe,plans,samples}]}
之后由 AI 读 dramas + samples 做语义精修（见下"已知局限"）。

⚠️ 已知规则局限（AI 必须复核这几类）：
  - 剧名内含数字会被误切：示例剧名1998→示例剧名、示例剧名1990→示例剧名。AI 需还原。
  - 批次/集数数字会残留：示例剧名A1、2示例剧名B。AI 需去掉。
  - 同剧不同批次未合并：示例剧名C 与 示例剧名C…6。AI 需合并。
规则输出仅作草稿，最终榜单以 AI 复核后为准。
"""
import json
import re
import sys
from collections import defaultdict

SRC_PREFIX = ['自投', '自制', '代投', '百川', '云菜', '奇树', '阅友', '点众', '掌读', '奇迹']
STOP_TOKENS = set([
    '定投', '通投', '定投女', '定投男', '女频', '男频', '测试', '新测', '老素材新测',
    '复刻动漫', '默认卡点', '激励', '上下滑', '最大转化',
    'IAA', 'iaa', 'cbo', 'CBO', '通投男', '第二集', '第一集', '新测cbo',
])


def normalize(name):
    s = name.strip()
    for p in SRC_PREFIX:
        if s.startswith(p):
            s = s[len(p):]
            s = re.sub(r'^\d{0,6}[-_\s]*', '', s)
            break
    s = re.sub(r'IAA[-_\s]*', '', s, flags=re.I)
    s = re.sub(r'^[-_\s]*\d{6,}[-_\s]*', '', s)
    s = re.sub(r'^[-_\s]*\d{4}_\d{6}_?\d*[-_\s]*', '', s)
    s = re.sub(r'^[-_\s]*\d{4}[-_\s]+', '', s)
    s = re.sub(r'^\[日期\][-_\s]*', '', s)
    s = s.lstrip('-_ ')
    parts = re.split(r'[-_\s]+', s)
    drama = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if re.fullmatch(r'\d{2,}', p):
            break
        if re.fullmatch(r'\d{4}_\d{6}.*', p):
            break
        if re.fullmatch(r'[a-zA-Z]{1,6}\d*', p):
            break
        if p in STOP_TOKENS or p == '[日期]':
            break
        p2 = re.sub(r'\d{4,}.*$', '', p)
        if p2 != p and p2 == '':
            break
        drama.append(p2 if p2 else p)
    result = ''.join(drama).strip('，。！：, .!:')
    return result if result else s[:16]


def load_adex_items(path, platform):
    """读 adex summary 输出，返回 [{charge,name,platform}]。容错 API 错误。"""
    try:
        d = json.load(open(path))
    except Exception:
        return []
    if isinstance(d, dict) and d.get('ok') is False:
        return []
    items = d.get('items') or d.get('data') or []
    rows = []
    for i in items:
        name = i.get('groupName', '')
        if not name:
            continue
        rows.append({'charge': float(i.get('charge', 0) or 0), 'name': name, 'platform': platform})
    return rows


def main():
    args = sys.argv[1:]
    data = []
    if '--ks' in args or '--oe' in args:
        if '--ks' in args:
            data += load_adex_items(args[args.index('--ks') + 1], '快手')
        if '--oe' in args:
            data += load_adex_items(args[args.index('--oe') + 1], '巨量')
    else:
        path = args[0] if args else '/tmp/plans.json'
        data = json.load(open(path))

    agg = defaultdict(lambda: {'charge': 0.0, 'plans': 0, 'ks': 0.0, 'oe': 0.0, 'samples': []})
    for r in data:
        drama = normalize(r['name'])
        a = agg[drama]
        a['charge'] += r['charge']
        a['plans'] += 1
        if r.get('platform') == '快手':
            a['ks'] += r['charge']
        else:
            a['oe'] += r['charge']
        if len(a['samples']) < 3:
            a['samples'].append(r['name'])

    total = sum(v['charge'] for v in agg.values())
    out = {
        'total_charge': round(total, 2),
        'plan_count': len(data),
        'drama_count': len(agg),
        'dramas': [
            {'drama': k, 'charge': round(v['charge'], 2), 'ks': round(v['ks'], 2),
             'oe': round(v['oe'], 2), 'plans': v['plans'], 'samples': v['samples']}
            for k, v in sorted(agg.items(), key=lambda x: -x[1]['charge'])
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
