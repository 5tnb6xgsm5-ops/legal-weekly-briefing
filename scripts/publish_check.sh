#!/usr/bin/env bash
# publish_check.sh — 发布前安全检查（2026-08-01 对抗审查教训固化）
#
# 背景：2026-08-01 审查发现真实 KB_ID/folder_id 残留在 git 历史（tag v3.0.0、
# v1.0.1 及 4 个历史提交），运行产物被跟踪入库。HEAD 干净不代表历史干净。
#
# 用法：在仓库根目录运行  bash scripts/publish_check.sh
# 铁律：任何 push / Release / 打 tag 之前必须先跑本脚本，未通过禁止发布。

set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
FAIL=0

echo "🔍 发布前安全检查 — $(basename "$REPO")"
echo ""

# ── 1. HEAD taxonomy 占位符检查 ──
if [ -f assets/config/taxonomy.yaml ]; then
    if grep -q "YOUR_KNOWLEDGE_BASE_ID" assets/config/taxonomy.yaml; then
        echo "  ✓ HEAD taxonomy.yaml 为占位符"
    else
        echo "  ✗ HEAD taxonomy.yaml 含非占位符 KB_ID — 禁止发布！"
        FAIL=1
    fi
else
    echo "  ⚠️  未找到 assets/config/taxonomy.yaml（跳过检查）"
fi

# ── 2. git 历史敏感模式扫描（教训：HEAD 干净 ≠ 历史干净）──
echo ""
echo "  扫描 git 全历史敏感模式（耗时与仓库规模相关）..."
HITS=$(git log --all -p -- . ":(exclude)scripts/publish_check.sh" 2>/dev/null | grep -nE \
    'knowledge_base_id: [^Y"# ]|folder_[0-9]{10,}|ghp_[A-Za-z0-9]{20,}|ima-openapi-apikey[: =][^ "]{8,}' \
    | grep -v '^Binary' | head -20)
if [ -n "$HITS" ]; then
    echo "  ✗ git 历史发现敏感模式（发布前必须清除：filter-repo 重写或删除对应 tag）："
    echo "$HITS"
    FAIL=1
else
    echo "  ✓ git 历史无 KB_ID / folder_id / token / api-key 模式"
fi

# ── 3. 被跟踪的运行时产物 / 登录态 / 备份 ──
TRACKED=$(git ls-files | grep -E \
    '\.state\.json|\.bak-|^\.workbuddy/|mp_articles.*\.json|yuanbao_links|queued_cache|needs_llm|^周报_|run-report|candidates(_merged)?\.jsonl')
if [ -n "$TRACKED" ]; then
    echo ""
    echo "  ✗ 被跟踪的产物/敏感文件（git rm --cached 移除并补 .gitignore）："
    echo "$TRACKED"
    FAIL=1
else
    echo ""
    echo "  ✓ 无被跟踪的产物 / 登录态 / 备份文件"
fi

# ── 4. 未推送提交提醒 ──
echo ""
UNPUSHED=$(git log --oneline @{u}.. 2>/dev/null || git log --oneline origin/main.. 2>/dev/null)
if [ -n "$UNPUSHED" ]; then
    echo "  ⚠️  存在未推送提交（推送前确保已通过全部检查）："
    echo "$UNPUSHED" | sed 's/^/      /'
fi

echo ""
if [ $FAIL -eq 0 ]; then
    echo "✅ 发布前检查通过 — 可以 push / 打 tag / 发 Release"
    exit 0
else
    echo "❌ 发布前检查未通过 — 修复后再发布"
    exit 1
fi
