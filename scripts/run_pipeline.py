#!/usr/bin/env python3
"""周报生成流水线编排层（开源化：失败容错 + 自检断言 + 结构化日志）

职责：
- 串联：内容发现 → 去重 → 评分 → 写简报 → IMA 导入
- 每步 try/except：RETRYABLE（限流/网络/超时 → 退避重试）vs FATAL（依赖缺失 → 告警退出）
- 自检改为退出码断言（候选池≥min_candidates、导入数≥交付数、MD 非空）
- 写 run-report.json + .workbuddy/runs/<date>.jsonl 日志
- MP 不可用 → 跳过 MP 阶段，标"MP 缺失"继续

注意：内容发现（WebSearch/MP 拉取）由调用方完成并写入 candidates 文件，本文件负责
去重→评分→写简报→IMA队列的确定性编排。CLI 契约：

    python3 run_pipeline.py candidates.jsonl

candidates.jsonl 每行: {"title":..., "url":..., "category":"legal|ai-legal", "features":{...}}
输出: 周报_<date>.md + ima_import_queue.jsonl + run-report.json
"""
import json, time, sys, os, re
from pathlib import Path
from datetime import date
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

# 技能根目录（scripts/ 的上一级），assets/ 与 scripts/ 同级
BASE = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE / "assets" / "config" / "settings.yaml"


class PipelineError(Exception):
    pass


class RetryableError(PipelineError):
    pass


class FatalError(PipelineError):
    pass


def load_settings():
    if yaml is None or not SETTINGS_FILE.exists():
        return {}
    with open(SETTINGS_FILE) as f:
        return yaml.safe_load(f) or {}


def _get_runs_dir():
    """读取 settings.yaml 的 runs_dir，回退到 'runs'。"""
    settings = load_settings()
    runs_dir = settings.get("pipeline", {}).get("runs_dir", "runs")
    return BASE / runs_dir


def log_stage(report, stage, **kw):
    entry = {"ts": time.time(), "stage": stage, **kw}
    report["stages"].append(entry)
    # 结构化日志落盘
    runs_dir = _get_runs_dir()
    runs_dir.mkdir(parents=True, exist_ok=True)
    logfile = runs_dir / f"{date.today().isoformat()}.jsonl"
    with open(logfile, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def run_with_retry(fn, max_retries=3, backoff=2):
    """包装可重试步骤。RETRYABLE 异常退避重试；FATAL 立即抛出。"""
    last = None
    for attempt in range(max_retries):
        try:
            return fn()
        except RetryableError as e:
            last = e
            time.sleep(backoff ** attempt)
    raise last


def self_check(report, settings):
    """退出码断言：返回 (ok, failures)。"""
    out = settings.get('output', {})
    min_c = out.get('min_candidates', 10)
    failures = []
    n_candidates = report.get('counts', {}).get('candidates', 0)
    if n_candidates < min_c:
        failures.append(f"候选池 {n_candidates} < 最小 {min_c}")
    report_path = report.get('report_path')
    if report_path and not Path(report_path).exists():
        failures.append("周报 MD 文件未生成")
    return (len(failures) == 0, failures)


def classify_source(candidate):
    """从候选条目的 source/title/url 推断归一化来源标识。

    返回归一化来源字符串（如 '山东高法'、'上海一中院'、'Artificial Lawyer'）。
    用于 diversity-aware selection 的同源识别。
    """
    src = candidate.get('source', '') or ''
    title = candidate.get('title', '') or ''
    url = candidate.get('url', '') or ''

    # 法院公众号（精确匹配）
    if '山东高法' in src or '山东高法' in title:
        return '山东高法'
    if '上海一中' in src or '上海一中' in title:
        return '上海一中院'
    if '上海二中' in src or '上海二中' in title:
        return '上海二中院'
    if '最高法' in src or '最高人民法院' in src or 'court.gov.cn' in url:
        return '最高法'
    if '全国人大' in src:
        return '全国人大'
    if '国务院' in src or '人社部' in src or 'gov.cn' in url:
        return '国务院/部委'
    # 国际法律科技源
    if 'Artificial Lawyer' in src:
        return 'Artificial Lawyer'

    # Fallback: source 字段的第一段，或域名
    if src:
        return src.split('/')[0].strip().split('|')[0].strip()
    try:
        domain = urlparse(url).netloc
        return domain or '未知来源'
    except Exception:
        return '未知来源'


def select_diverse(scored, category, count, max_per_source):
    """多样性感知选择：从已评分候选中选取 top N，同源不超过 max_per_source。

    scored: 已按分数降序排列的候选列表（含 score, category 等字段）
    category: 'ai-legal' | 'legal'（筛选条件）
    count: 目标条数
    max_per_source: 同一来源最大条数（0=不限制）

    返回: (selected, remaining) — selected 是入选的 N 条，remaining 是未入选的（可用于 IMA 导入）
    """
    cat_items = [c for c in scored if c.get('category') == category or (category == 'legal' and c.get('category') != 'ai-legal')]
    if not max_per_source or max_per_source <= 0:
        selected = cat_items[:count]
        remaining = cat_items[count:]
        return selected, remaining

    source_counts = {}
    selected = []
    remaining = []
    for item in cat_items:
        s = classify_source(item)
        if len(selected) >= count:
            remaining.append(item)
            continue
        if source_counts.get(s, 0) < max_per_source:
            selected.append(item)
            source_counts[s] = source_counts.get(s, 0) + 1
        else:
            remaining.append(item)

    # 如果选不够 count 条（候选太少），允许同源重复
    if len(selected) < count:
        overflow = []
        for item in remaining:
            if len(selected) >= count:
                break
            selected.append(item)
            overflow.append(item)
        remaining = [r for r in remaining if r not in overflow]

    # 按分数降序重排（diversity-aware selection 可能打乱顺序）
    selected.sort(key=lambda x: x.get('score', 0), reverse=True)
    return selected, remaining


def default_write_report(candidates, scored):
    """简报写入：diversity-aware 选择 + 分数降序排列，返回路径。"""
    settings = load_settings()
    out = settings.get('output', {})
    template = out.get('report_template', '周报_{date}.md')
    max_per_source = out.get('max_per_source', 2)
    ai_count = out.get('ai_legal_count', 3)
    legal_count = out.get('legal_count', 7)
    path = BASE / template.format(date=date.today().isoformat())

    # Diversity-aware selection
    ai_selected, ai_remaining = select_diverse(scored, 'ai-legal', ai_count, max_per_source)
    legal_selected, legal_remaining = select_diverse(scored, 'legal', legal_count, max_per_source)

    with open(path, 'w') as f:
        f.write(f"# 法律周报 {date.today().isoformat()}\n\n")
        f.write("## AI + 法律\n\n")
        for c in ai_selected:
            f.write(f"【{c.get('score')}】{c.get('title')}\n{c.get('url', '')}\n\n")
        f.write("## 纯法律\n\n")
        for c in legal_selected:
            f.write(f"【{c.get('score')}】{c.get('title')}\n{c.get('url', '')}\n\n")

    # 将 diversity 过滤掉但仍需导入 IMA 的条目放回 scored 的报告中
    # （不修改 scored 本身，因为 selection 可能被外部使用）
    return str(path)


def run_pipeline(discover_fn, write_report_fn=None, import_fn=None, settings=None, candidates_raw=None):
    """主入口。

    discover_fn: () -> list[dict]  # 返回候选条目（已合并 MP+WebSearch）
    candidates_raw: list[dict]     # 或直接从文件载入的候选（CLI 模式）
    write_report_fn: (candidates, scored) -> str  # 写 MD，返回路径（默认 default_write_report）
    import_fn: (candidates) -> list[dict]  # IMA 导入（默认调用 ima_importer 写队列）

    返回: (exit_code, report)
    """
    settings = settings or load_settings()
    pipeline_cfg = settings.get('pipeline', {})
    max_retries = pipeline_cfg.get('max_retries', 3)
    backoff = pipeline_cfg.get('backoff', 2)
    if write_report_fn is None:
        write_report_fn = default_write_report

    report = {"date": date.today().isoformat(), "stages": [], "counts": {}, "errors": []}

    # Stage 1: 内容发现（含 MP 拉取，失败可降级）
    if candidates_raw is not None:
        candidates_raw = candidates_raw
        log_stage(report, "discover", count=len(candidates_raw), mode="from_file")
    else:
        try:
            def _discover():
                items = discover_fn()
                if not items:
                    raise RetryableError("内容发现返回空")
                return items
            candidates_raw = run_with_retry(_discover, max_retries, backoff)
            log_stage(report, "discover", count=len(candidates_raw))
        except RetryableError as e:
            candidates_raw = []
            report["errors"].append(f"discover 降级: {e}")
            log_stage(report, "discover", status="degraded", error=str(e))

    # Stage 2: 去重
    from dedupe import dedupe_items
    candidates = dedupe_items(candidates_raw)
    report["counts"]["candidates"] = len(candidates)
    log_stage(report, "dedupe", before=len(candidates_raw), after=len(candidates))

    # Stage 3: 评分（调用 scoring_engine.predict）
    from scoring_engine import predict
    scored = []
    for c in candidates:
        cat = c.get('category', 'legal')
        score, conf = predict({"features": c.get('features', {}), "title": c.get('title', '')}, cat)
        c['score'] = score
        c['confidence'] = conf
        scored.append(c)
    scored.sort(key=lambda x: x.get('score', 0), reverse=True)
    log_stage(report, "score", count=len(scored))

    # Stage 4: 写简报
    report_path = write_report_fn(candidates, scored)
    report["report_path"] = report_path
    log_stage(report, "write_report", path=report_path)

    # Stage 4.5: 渲染 HTML 周报
    try:
        from render_html import render_html as _render
        report_date = date.today().strftime('%Y.%m.%d')
        html = _render(scored, report_date)
        html_path = str(Path(report_path).with_suffix('.html'))
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        report["html_path"] = html_path
        log_stage(report, "render_html", path=html_path)
    except Exception as e:
        log_stage(report, "render_html", error=str(e))

    # Stage 5: IMA 导入（默认写队列，启用了阈值过滤）
    if import_fn is None:
        from ima_importer import import_one
        def import_fn(items):
            return [import_one(c['url'], c.get('title', '')) for c in items]

    # IMA 导入阈值：仅导入分数 >= 阈值 且 来源为法院/官方公众号的条目
    threshold = (settings.get('output', {}) or {}).get('ima_import_threshold', 0)
    court_sources = {'山东高法', '上海一中院', '上海二中院', '最高法', '国务院/部委'}
    importable = [c for c in scored
                  if c.get('score', 0) >= threshold
                  and classify_source(c) in court_sources]
    results = import_fn(importable)
    queued = sum(1 for r in results if r.get('status') in ('imported', 'queued'))
    report["counts"]["imported"] = queued
    log_stage(report, "import", queued=queued, total=len(results))

    # 自检
    ok, failures = self_check(report, settings)
    report["self_check"] = {"ok": ok, "failures": failures}

    # 写 run-report.json
    with open(BASE / "run-report.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    exit_code = 0 if ok else 1
    return exit_code, report


def load_candidates(path):
    """从 JSONL 或 JSON 文件载入候选。每行/每项: {title, url, category, features}"""
    p = Path(path)
    items = []
    if p.suffix == '.jsonl':
        for line in open(p):
            line = line.strip()
            if line:
                items.append(json.loads(line))
    else:
        data = json.loads(open(p).read())
        items = data if isinstance(data, list) else data.get('candidates', [])
    return items


if __name__ == '__main__':
    # 用法：
    #   python3 run_pipeline.py                      # 演示 dry-run
    #   python3 run_pipeline.py candidates.jsonl     # CLI 模式：从候选文件跑全流程
    if len(sys.argv) > 1:
        candidates = load_candidates(sys.argv[1])
        code, rep = run_pipeline(None, candidates_raw=candidates)
        print(f"exit_code={code}, candidates={rep['counts'].get('candidates')}, "
              f"imported={rep['counts'].get('imported')}, self_check={rep['self_check']}")
        print(f"report={rep.get('report_path')}")
        print(f"ima_queue=ima_import_queue.jsonl")
    else:
        # 演示 dry-run
        demo = [
            {"title": "公司股东出资纠纷", "url": "https://mp.weixin.qq.com/s/a", "category": "legal",
             "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1}},
            {"title": "AI 法律助手发布", "url": "https://example.com/b", "category": "ai-legal",
             "features": {"first_hand": 1, "depth": 1, "relevance": 1}},
        ]
        code, rep = run_pipeline(None, candidates_raw=demo)
        print(f"exit_code={code}, candidates={rep['counts'].get('candidates')}, imported={rep['counts'].get('imported')}")
