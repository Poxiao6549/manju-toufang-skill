# adex CLI install — GitHub-release mirror fix

`@<SCOPE>/adex-cli` is an npm wrapper around a **Go binary** downloaded from
GitHub releases on first run. On slow/blocked networks (mainland China) the
direct download to `release-assets.githubusercontent.com` **connects but
crawls or stalls mid-transfer**; the wrapper's hardcoded
`curl --connect-timeout 10 --max-time 120` then fails with
`curl: (28) Operation timed out` and the tool prints
`Failed to install adex binary: All download sources failed`. The bundled
`registry.npmmirror.com` fallback 404s.

This fix generalizes to **any npm/pip CLI that fetches a native binary from
GitHub releases**.

## Fix: mirror-download + verify + place manually

1. **Read the wrapper's install script** to find three things
   (for adex: `node_modules/@<SCOPE>/adex-cli/scripts/install.js`):
   - the release URL it builds (`GITHUB_URL` = `github.com/OWNER/REPO/releases/download/vX/<archive>`)
   - the **destination path** for the binary (`bin/<name>`, chmod 755)
   - the `checksums.txt` it verifies the archive against

2. **Download via a GitHub proxy mirror** (seconds instead of 20+ min):
   ```bash
   URL="https://github.com/<ORG>/adex-cli/releases/download/v0.2.8/adex-0.2.8-linux-amd64.tar.gz"
   EXPECT="<sha256 from checksums.txt for this archive>"
   for M in "https://ghfast.top" "https://gh-proxy.com" "https://ghproxy.net"; do
     curl --fail -L --show-error --connect-timeout 10 -o /tmp/asset.tar.gz "$M/$URL" && break
   done
   echo "$EXPECT  /tmp/asset.tar.gz" | sha256sum -c -   # MUST pass — mirrors are 3rd-party
   ```

3. **Extract and place** the binary where the wrapper expects it:
   ```bash
   tar -xzf /tmp/asset.tar.gz -C /tmp
   BINDIR="$(npm root -g)/@<SCOPE>/adex-cli/bin"   # or the path from install.js
   cp /tmp/adex "$BINDIR/adex" && chmod 755 "$BINDIR/adex"
   adex --help    # confirm the native binary runs
   ```
   The wrapper finds the binary on next run and skips its own broken download.

## Gotchas

- **Always `sha256sum -c`** — proxy mirrors are third-party infrastructure.
- Mirror `HEAD` returns `200 speed=0` (no body) — test with a real GET before
  concluding a mirror is dead.
- Mirror availability rotates; keep 2-3 in the fallback list.
- `adex --version` → `unknown flag: --version` is the binary running FINE, not a
  broken install. Use `adex --help`.
- Extracted Go binary is a `statically linked ELF x86-64` (~7 MB) even though the
  archive is ~3 MB.
- Don't try to raise the wrapper's `--max-time` — placing the binary manually
  bypasses the wrapper's downloader entirely, which is cleaner.
