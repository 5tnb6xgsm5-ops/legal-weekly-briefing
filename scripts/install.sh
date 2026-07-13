#!/usr/bin/env bash
# legal-weekly-briefing 一行安装脚本
# 用法: curl -fsSL <raw-url> | bash
# 或:   bash scripts/install.sh

set -e

SKILL_NAME="legal-weekly-briefing"
SKILL_DIR="${SKILL_DIR:-$HOME/.workbuddy/skills/$SKILL_NAME}"
REPO_URL="${REPO_URL:-https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing.git}"

echo "📦 安装 $SKILL_NAME ..."

# 如果已经是 git 仓库，直接拉取
if [ -d "$SKILL_DIR/.git" ]; then
    echo "  已存在，更新..."
    cd "$SKILL_DIR" && git pull --ff-only
else
    # 首次安装：克隆仓库
    if [ -f "SKILL.md" ]; then
        # 本地目录模式：已经在 skill 目录中
        SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
        echo "  本地安装: $SKILL_DIR"
    else
        git clone "$REPO_URL" "$SKILL_DIR"
    fi
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Python $PYTHON_VERSION ✓"

# 可选依赖
python3 -c 'import yaml' 2>/dev/null || {
    echo "   ⚠️  pyyaml 未安装（非必需，缺失时自动降级）"
    echo "   安装: pip3 install pyyaml"
}

# 验证安装
echo ""
echo "🧪 验证安装..."
cd "$SKILL_DIR"
PYTHONPATH=scripts python3 scripts/verify.py

echo ""
echo "🚀 快速体验:"
echo "   cd $SKILL_DIR && python3 scripts/demo.py"
echo ""
echo "✅ $SKILL_NAME 安装完成！"
