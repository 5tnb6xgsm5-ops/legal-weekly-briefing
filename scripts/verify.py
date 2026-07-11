#!/usr/bin/env python3
"""legal-weekly-briefing 评分引擎回归测试

用法：
    python3 scripts/verify.py

读取 assets/data/test-prompts.json 中的样例，逐一调用 scoring_engine.predict，
断言预测分落在期望区间。全部通过退出码 0，否则 1。

这是开源用户安装后的自检工具，也是维护者迭代评分维度时的回归门禁。
"""
import json, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from scoring_engine import predict

TEST_PATH = BASE / "assets" / "data" / "test-prompts.json"


def main():
    if not TEST_PATH.exists():
        print(f"✗ 测试样例缺失: {TEST_PATH}", file=sys.stderr)
        sys.exit(1)
    cases = json.loads(TEST_PATH.read_text())["cases"]

    passed = 0
    failed = 0
    print(f"运行 {len(cases)} 个验证样例...\n")
    for c in cases:
        cat = c["category"]
        feat = c["features"]
        score, conf = predict({"title": c.get("title", ""), "features": feat}, cat)
        lo, hi = c["expect_min"], c["expect_max"]
        ok = lo <= score <= hi
        mark = "✓" if ok else "✗"
        print(f"  {mark} {c['id']:12} | {cat:9} | score={score:4} (期望 {lo}-{hi}) | conf={conf} | {c.get('title','')[:24]}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n结果: {passed} 通过 / {failed} 失败 / 共 {len(cases)}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
