#!/usr/bin/env python3
"""legal-weekly-briefing 回归测试 + 交付门禁

用法：
    python3 scripts/verify.py

两层检查：
  1. 评分引擎回归（6 个 test-prompts 样例）
  2. HTML 交付门禁（P0: 模板风格 / 字段完整性 / 流水线集成）

全部通过 → 退出码 0；任一失败 → 退出码 1。
"""
import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

PASSED = 0
FAILED = 0

def check(ok, label, detail=""):
    global PASSED, FAILED
    mark = "✓" if ok else "✗"
    msg = f"  {mark} [{label}]"
    if detail:
        msg += f"  {detail}"
    print(msg)
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    return ok


# ============================================================
# Layer 1: 评分引擎回归（保持原有逻辑）
# ============================================================
def run_scoring_tests():
    global PASSED, FAILED
    perf = PASSED
    perf = FAILED
    P, F = 0, 0

    from scoring_engine import predict
    TEST_PATH = BASE / "assets" / "data" / "test-prompts.json"
    if not TEST_PATH.exists():
        print(f"✗ 测试样例缺失: {TEST_PATH}")
        return False

    cases = json.loads(TEST_PATH.read_text())["cases"]
    print(f"\n--- 评分引擎回归 ({len(cases)} 样例) ---")
    for c in cases:
        cat = c["category"]
        feat = c["features"]
        score, conf = predict({"title": c.get("title", ""), "features": feat}, cat)
        lo, hi = c["expect_min"], c["expect_max"]
        ok = lo <= score <= hi
        detail = f"score={score:.1f} (期望 {lo}-{hi}) | {c.get('title','')[:36]}"
        if check(ok, f"评分/{c['id']}", detail):
            P += 1
        else:
            F += 1
    return F == 0


# ============================================================
# Layer 2: HTML 交付门禁（P0 — 任一失败即阻塞交付）
# ============================================================
def run_html_gate():
    print(f"\n--- HTML 交付门禁 ---")
    all_ok = True

    # G1: render_html.py 存在且可导入
    render_path = BASE / "scripts" / "render_html.py"
    exists = render_path.exists()
    all_ok &= check(exists, "G1-render_html存在", f"路径: {render_path}")

    try:
        import render_html
        has_fn = hasattr(render_html, "render_html")
        all_ok &= check(has_fn, "G1-render_html可导入", "render_html.render_html() 函数可用")
    except Exception as e:
        all_ok &= check(False, "G1-render_html可导入", f"导入失败: {e}")

    # G2: 模板风格 = 浅色简报风（禁止深色翻页幻灯片）
    if render_path.exists():
        template_src = render_path.read_text()
        is_light_bg = "#f8f7f5" in template_src
        is_dark_header = "#1a1a2e" in template_src
        has_no_dark_slide = "var cur" not in template_src  # 翻页幻灯片的典型 JS 变量

        all_ok &= check(is_light_bg, "G2-浅色背景", "模板含 #f8f7f5（浅色简报风）")
        all_ok &= check(is_dark_header, "G2-深色页眉", "模板含 #1a1a2e（深色页眉）")
        all_ok &= check(has_no_dark_slide, "G2-禁止翻页幻灯片",
                        "模板不含翻页 JS（禁止自造深色翻页版）")

        # G3: HTML 模板必须含 abstract / recommend 渲染段
        has_abstract = "abstract" in template_src and "{abstract}" in template_src
        has_recommend = "推荐理由" in template_src and "{recommend}" in template_src
        has_fav = "fav-btn" in template_src
        all_ok &= check(has_abstract, "G3-abstract字段", "模板渲染 abstract 占位符")
        all_ok &= check(has_recommend, "G3-recommend字段", "模板渲染 推荐理由 占位符")
        all_ok &= check(has_fav, "G3-收藏按钮", "模板含 fav-btn 交互")

    # G4: demo.py 产出 JSON 必须含 abstract/recommend 字段
    demo_path = BASE / "scripts" / "demo.py"
    if demo_path.exists():
        demo_src = demo_path.read_text()
        has_abstract_in_demo = '"abstract"' in demo_src and '"recommend"' in demo_src
        all_ok &= check(has_abstract_in_demo, "G4-demo含abstract/recommend",
                        "demo.py 候选数据含完整渲染字段")

    # G5: run_pipeline.py 必须含 HTML 渲染步骤（Stage 4.5 或 render_html 调用）
    pipeline_path = BASE / "scripts" / "run_pipeline.py"
    if pipeline_path.exists():
        pl_src = pipeline_path.read_text()
        has_html_stage = "render_html" in pl_src or "Stage 4.5" in pl_src or "HTML" in pl_src
        all_ok &= check(has_html_stage, "G5-流水线含HTML渲染",
                        "run_pipeline.py 必须含 render_html 调用步骤")

    # G6: taxonomy.yaml 的 knowledge_base_id 不能是作者/他人 KB（占位符=尚未配置，警告不阻断）
    tax_path = BASE / "assets" / "config" / "taxonomy.yaml"
    if tax_path.exists():
        tax_src = tax_path.read_text()
        kb_line = [l for l in tax_src.split('\n') if 'knowledge_base_id' in l]
        kb_val = ""
        if kb_line:
            import re
            m = re.search(r'"([^"]*)"', kb_line[0])
            kb_val = m.group(1) if m else ""

        # 作者 KB 检测（P0 — 必须阻断）
        if kb_val.startswith("0P34_Uh7"):
            all_ok &= check(False, "G6-KB_ID非作者KB(P0)",
                            f"检测到作者知识库 ID，禁止导入！请替换为你自建的 KB_ID")
        # 占位符检测（警告 — 打包版合法，但提醒用户配置）
        elif kb_val in {"YOUR_KNOWLEDGE_BASE_ID", "YOUR_KB_ID", ""} or kb_val.startswith("YOUR_"):
            all_ok &= check(True, "G6-KB_ID待配置(警告)",
                            f"knowledge_base_id=占位符 — 打包版正常，用户部署时需替换为自建 KB_ID")
        elif kb_val:
            all_ok &= check(True, "G6-KB_ID已配置",
                            f"knowledge_base_id={kb_val[:20]}...（已替换为自建 KB）")

    return all_ok


def main():
    print("legal-weekly-briefing 回归测试 + 交付门禁\n")

    scoring_ok = run_scoring_tests()
    html_gate_ok = run_html_gate()

    total = PASSED + FAILED
    print(f"\n{'='*50}")
    print(f"评分引擎: {'✓ 通过' if scoring_ok else '✗ 失败'}")
    print(f"HTML门禁: {'✓ 通过' if html_gate_ok else '✗ 失败 (P0 — 阻塞交付)'}")
    print(f"总计: {PASSED} 通过 / {FAILED} 失败 / {total} 项")
    sys.exit(0 if (scoring_ok and html_gate_ok) else 1)


if __name__ == "__main__":
    main()
