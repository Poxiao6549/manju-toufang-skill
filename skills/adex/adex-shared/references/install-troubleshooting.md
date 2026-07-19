# adex CLI 安装排错

npm 包 `@<SCOPE>/adex-cli` 只是一个包装器：真正的可执行文件是一个 ~3MB 的 Go 静态二进制，
在 **首次运行时** 从 GitHub Releases 自动下载并放到 `<pkg>/bin/adex`。这个下载步骤是安装失败的主要来源。

## 已知坑 1：`install` 自带的全局安装步骤失败

`npx @<SCOPE>/adex-cli install` 末尾会尝试 `npm install -g`，可能失败并提示：

```
◇ Failed to install globally. Run manually: npm install -g @<SCOPE>/adex-cli
```

**解法**：直接手动全局安装即可（可能耗时 1-2 分钟）：

```bash
npm install -g @<SCOPE>/adex-cli
```

安装后 `which adex` 应指向 `<npm-global-bin>/adex`（如 `~/.local/bin/adex`）。

## 已知坑 2：GitHub 二进制下载被限速卡死（最常见）

首次运行 `adex <任意命令>` 时触发下载，若网络访问 GitHub `release-assets` 被限速，会看到：

```
Failed to install adex binary: All download sources failed:
  https://github.com/<ORG>/adex-cli/releases/download/v<VER>/adex-<VER>-linux-amd64.tar.gz
    → curl: (28) Operation timed out ... X out of 3202823 bytes received
  https://registry.npmmirror.com/-/binary/adex/v<VER>/... → curl: (22) 404
```

根因：包内 `scripts/install.js` 的 curl 有 `--max-time 120` 硬上限；GitHub 直连能建连但吞吐极低
（实测 3 分钟只下 ~470KB），120 秒内下不完 3MB 就超时。npmmirror 镜像对该 bucket 返回 404，无用。

**解法：用 GitHub 加速镜像前缀手动下载 + 校验 + 放到位。** 通用模式（适用于任何被 GitHub 限速的
release 资源，不限 adex）：给原始 GitHub URL 加一个可用的镜像前缀。

```bash
# 1. 目标信息（版本号见 <pkg>/package.json；校验和见 <pkg>/checksums.txt）
VER=0.2.8
URL="https://github.com/<ORG>/adex-cli/releases/download/v${VER}/adex-${VER}-linux-amd64.tar.gz"
EXPECT=$(grep "linux-amd64" "$(npm root -g)/@<SCOPE>/adex-cli/checksums.txt" | cut -d' ' -f1)

# 2. 依次尝试镜像前缀，成功即停（ghfast.top 实测 5 秒下完 3MB）
for M in https://ghfast.top https://gh-proxy.com https://ghproxy.net; do
  curl --fail -L --connect-timeout 10 --max-time 120 -o /tmp/adex-dl.tar.gz "$M/$URL" && break
done

# 3. 校验 SHA256（必须与 checksums.txt 一致）
echo "$EXPECT  /tmp/adex-dl.tar.gz" | sha256sum -c -

# 4. 解压并放到包期望的位置
BINDIR="$(npm root -g)/@<SCOPE>/adex-cli/bin"
mkdir -p "$BINDIR"
tar -xzf /tmp/adex-dl.tar.gz -C /tmp
cp /tmp/adex "$BINDIR/adex" && chmod 755 "$BINDIR/adex"

# 5. 验证（注意：没有 --version 这个 flag，用 --help）
adex --help
```

**要点**：
- **不要用 `adex --version`** —— 该二进制没有此 flag，会返回 `{"ok":false,...,"unknown flag: --version"}`。用 `adex --help`。
- 直连 GitHub 的 `curl -C -`（断点续传）+ `--retry` 也救不了限速——速度会掉到 0。必须换镜像前缀。
- 镜像可用性会变；`ghfast.top` / `gh-proxy.com` / `ghproxy.net` 循环兜底。先 `curl -sI` 探 HTTP 200 再下。

## 已知坑 3：`npx skills add <OSS 地址>` 无必要且会 AccessDenied

vendor 文档里的 `npx skills add https://adex-skills.oss-cn-hangzhou.aliyuncs.com -y` 这一步：
- 该阿里云 OSS bucket 直接返回 `<Code>AccessDenied</Code>`。
- **而且没必要**——adex 二进制**已内嵌** `adex-ks` / `adex-oe` / `adex-shared` 三个 skill。

**把内嵌 skill 装进本地 skill 目录的正确做法**（让投放 skill 能加载并调 adex 拉数）：

```bash
# 逐个导出内嵌 skill 到本地技能目录
for S in adex-shared adex-ks adex-oe; do
  mkdir -p ~/.workbuddy/skills/$S
  adex skills read "$S" > ~/.workbuddy/skills/$S/SKILL.md
done
```

`adex skills list` 查看有哪些内嵌 skill；`adex skills read <name>` 输出完整 SKILL.md（含 frontmatter）。
