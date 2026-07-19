#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布前安全扫描：把 skill 打包分享给别人（GitHub / tar 包）之前，
先跑这个，确认没有把真实凭据 / 内网地址 / token 泄漏出去。

⚠️ 血泪教训：adex-shared / adex-reporting 的 SKILL.md 里嵌了真实
   adex token（adex_c93...）和内网 API 地址（47.99.131.x）。差点连同
   本 skill 一起推到 GitHub。search_files/grep 有时匹配不到（编码/正则差异），
   必须用这个独立脚本扫，且**在 commit/push 之前**跑。

用法：
  python3 prepublish_scan.py <要发布的目录>
  exit 0 = 干净可发布；exit 1 = 有泄漏，禁止发布

命中后处理：把真实值替换成占位符（adex_你的token / http://你的服务地址:端口），
然后**重建 git 历史**（rm -rf .git 重新 init + commit），因为 token 一旦进过
commit，即使后续修改，旧 commit 里仍留着 —— 私有仓库也算安全事故。
"""
import os
import re
import sys
import glob

# 泄漏特征（按需补充你们环境的真实前缀/网段）
LEAK_PATTERNS = [
    (r"adex_c9[0-9a-f]{6,}", "adex 真实 token"),
    (r"adex_[0-9a-f]{20,}", "adex 长 token"),
    (r"github_pat_\w{20,}", "GitHub fine-grained PAT"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub classic PAT"),
    (r"Bearer\s+adex_[0-9a-f]{8,}", "Bearer + 真实 adex token"),
    (r"47\.99\.131\.\d+", "内网/私有 API 地址"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b", "IP:端口（疑似内网服务）"),
]
# 白名单占位符（这些不算泄漏）
SAFE = ["adex_你的token", "adex_xxx", "adex_...", "你的服务地址", "你的adex", "<你的"]


def scan(root):
    problems = []
    files = (glob.glob(f"{root}/**/*.md", recursive=True)
             + glob.glob(f"{root}/**/*.py", recursive=True)
             + glob.glob(f"{root}/**/*.json", recursive=True)
             + glob.glob(f"{root}/**/*.sh", recursive=True))
    for f in files:
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for pat, label in LEAK_PATTERNS:
            for m in re.finditer(pat, txt):
                hit = m.group(0)
                if any(s in hit for s in SAFE):
                    continue
                # 定位行号
                line_no = txt[:m.start()].count("\n") + 1
                problems.append(f"  {os.path.relpath(f, root)}:L{line_no}  [{label}]  {hit[:40]}")
    return problems


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    problems = scan(root)
    if problems:
        print(f"❌ 发现 {len(problems)} 处疑似泄漏，禁止发布：\n" + "\n".join(problems))
        print("\n处理：替换成占位符 → rm -rf .git 重建历史 → 重新扫描确认 → 再 push")
        sys.exit(1)
    print(f"✅ 扫描通过（{root}）：无真实凭据/内网地址泄漏，可发布")
    sys.exit(0)


if __name__ == "__main__":
    main()
