#!/usr/bin/env python3
"""IMA 知识库导入模块（开源化：幂等 + 失败队列 + 配置驱动 + 队列解耦）

职责：
- 从 config/taxonomy.yaml 解析领域 → folder_id
- 导入前查重（imported_cache.jsonl，url 为键）
- 分类决策后写入 ima_import_queue.jsonl（待导入队列）
- 硬件失败（IO/磁盘）写入 failed_import.jsonl + 指数退避重试
- 分类失败（keywords+heuristic 均不命中）写入 needs_llm_classify.jsonl
  由外层 Agent 批量 LLM 分类后回填 ima_import_queue.jsonl
- 多领域命中 → 主领域优先，副类记录

设计：本模块不直接调用 IMA API。它产出"待导入队列"，由外层客户端消费：
- WorkBuddy 环境：自动化运行时读取队列 → 调用 ima-skill 的 import_urls MCP 工具
- 开源用户：可用 IMA OpenAPI / 客户端手动导入队列中的 url+folder_id
这样 Python 模块保持可测试、不耦合 MCP 运行时，且不硬编码凭证。
"""
import json, time, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# 技能根目录（scripts/ 的上一级），assets/ 与 scripts/ 同级
BASE = Path(__file__).resolve().parent.parent
TAXONOMY = BASE / "assets" / "config" / "taxonomy.yaml"
CACHE = BASE / "imported_cache.jsonl"
FAILED = BASE / "failed_import.jsonl"
NEEDS_LLM = BASE / "needs_llm_classify.jsonl"


def load_taxonomy():
    if yaml is None or not TAXONOMY.exists():
        return None
    with open(TAXONOMY) as f:
        return yaml.safe_load(f) or {}


def classify(title, tags=None):
    """返回 (primary_category, folder_id, secondary_categories)。

    两层匹配：
    1. 主关键词精确匹配（taxonomy.yaml categories 的 keywords）
    2. 兜底推断（_heuristic_classify）：主关键词不命中时按标题语义特征推断
    两层都不命中 → 返回 (None, uncategorized_folder_id, [])。
    """
    tax = load_taxonomy()
    if not tax:
        return None, "", []
    cats = tax.get('categories', [])
    text = (title or '') + ' ' + ' '.join(tags or [])
    matched = []
    for c in cats:
        kw = c.get('keywords', [])
        if any(k in text for k in kw):
            matched.append(c)

    # 兜底：主关键词不命中时尝试推断
    if not matched:
        inferred = _heuristic_classify(title, cats)
        if inferred:
            return inferred['name'], inferred.get('folder_id', ''), []

    if not matched:
        return None, tax.get('uncategorized_folder_id', ''), []
    # 主领域：priority 最高；并列取首个
    matched.sort(key=lambda c: c.get('priority', 0), reverse=True)
    primary = matched[0]
    secondary = [c['name'] for c in matched[1:]]
    return primary['name'], primary.get('folder_id', ''), secondary


# 兜底推断规则：当主关键词不命中时，按语义特征推断分类。
# 每条规则: (signal_words, category_name)
# signal_words 中任一命中标题 → 推断为该分类。
# 规则按置信度排序，先命中先得（不回溯）。
_HEURISTIC_RULES = [
    # 刑事信号（优先级最高，避免误分类到其他域）
    (['罪', '避险', '危险作业', '刑事', '诈骗', '渎职'], '刑事'),
    # 劳动法信号
    (['欠薪', '雇主', '打工', '工资', '工伤', '解雇', '辞退'], '劳动法'),
    # 建筑工程信号
    (['建工', '工程款', '施工', '分包', '转包'], '建筑工程'),
    # 婚姻家事信号
    (['赠与', '婚外', '离婚', '继承', '抚养', '彩礼'], '婚姻家事'),
    # 合同借贷信号
    (['借条', '欠条', '留置', '担保', '违约金', '定金'], '合同借贷'),
    # 侵权信号
    (['热射病', '受伤', '致死', '损害赔偿', '安全保障'], '侵权'),
    # 执行信号
    (['执行', '查封', '冻结', '拍卖', '失信'], '执行'),
    # 房地产/物权信号
    (['矿产资源', '拆迁', '宅基地', '不动产', '物业'], '房地产/物权'),
    # 公司信号（最宽泛，优先级最低）
    (['股东', '股权', '法人', '章程', '董监高', '公司'], '公司'),
]


def _heuristic_classify(title, categories):
    """兜底推断：标题命中 heuristic 规则 → 返回对应 category dict。

    在 categories 列表中查找 name 匹配的 category，返回其 dict（含 folder_id）。
    无命中返回 None。
    """
    if not title:
        return None
    cat_map = {c['name']: c for c in categories}
    for signal_words, cat_name in _HEURISTIC_RULES:
        if any(w in title for w in signal_words):
            return cat_map.get(cat_name)
    return None


def load_cache():
    if not CACHE.exists():
        return set()
    with open(CACHE) as f:
        return set(line.strip() for line in f if line.strip())


def save_cache(url):
    with open(CACHE, 'a') as f:
        f.write(url + '\n')


def load_failed():
    if not FAILED.exists():
        return []
    with open(FAILED) as f:
        return [json.loads(line) for line in f if line.strip()]


def reset_failed():
    """清空硬件失败队列 —— 每轮 pipeline 启动时调用，避免跨轮累积。"""
    with open(FAILED, 'w') as f:
        f.write('')


def save_failed(entry):
    """追加单条硬件失败记录（IO/磁盘错误）。同一轮 pipeline 内多次调用。"""
    with open(FAILED, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def reset_needs_llm():
    """清空 LLM 待分类队列 —— 每轮 pipeline 启动时调用。"""
    with open(NEEDS_LLM, 'w') as f:
        f.write('')


def save_needs_llm(url, title, source=""):
    """追加一条需要 LLM 兜底分类的条目。
    
    格式：{url, title, source, ts}
    Agent 层读取此文件后批量 LLM 分类，结果回填 ima_import_queue.jsonl。
    """
    with open(NEEDS_LLM, 'a') as f:
        f.write(json.dumps({
            "url": url,
            "title": title,
            "source": source,
            "ts": time.time()
        }, ensure_ascii=False) + '\n')


def import_one(url, title, source="", max_retries=3, backoff=2):
    """决定单条是否导入 IMA，并写入待导入队列。

    三层分流：
    1. 关键词 + 启发式命中 → 直接 enqueue（确定性，零延迟）
    2. 均不命中 → 写入 needs_llm_classify.jsonl（Agent 层批量 LLM 处理）
    3. IO/磁盘错误 → 写入 failed_import.jsonl（硬件故障）

    返回 dict: {url, status, folder_id, category, error}
    status: 'queued' | 'skipped_duplicate' | 'needs_llm' | 'failed'
    """
    cache = load_cache()
    if url in cache:
        return {"url": url, "status": "skipped_duplicate", "folder_id": "", "category": "", "error": ""}

    category, folder_id, secondary = classify(title)
    if not folder_id:
        # 分类不命中 → LLM 兜底队列，不标 failed
        save_needs_llm(url, title, source)
        return {"url": url, "status": "needs_llm", "folder_id": "", "category": "", "error": "needs_llm_classify"}

    # 重试：队列写出可能因 IO 失败，退避重试
    last_err = ""
    for attempt in range(max_retries):
        try:
            _enqueue(url, title, folder_id, category, secondary)
            save_cache(url)
            return {"url": url, "status": "queued", "folder_id": folder_id, "category": category or "", "error": ""}
        except Exception as e:
            last_err = str(e)
            time.sleep(backoff ** attempt)

    # IO 失败 → 硬件故障队列
    entry = {"url": url, "title": title, "folder_id": folder_id, "error": last_err, "ts": time.time()}
    save_failed(entry)
    return {"url": url, "status": "failed", "folder_id": folder_id, "category": category or "", "error": last_err}


def _enqueue(url, title, folder_id, category, secondary):
    """将待导入条目追加到队列文件，供外层 IMA 客户端消费。

    队列格式（JSONL）：{url, title, folder_id, category, secondary, ts}
    外层消费后调用 import_urls(knowledge_base_id, folder_id, [url])。
    """
    queue = BASE / "ima_import_queue.jsonl"
    record = {
        "url": url,
        "title": title,
        "folder_id": folder_id,
        "category": category,
        "secondary": secondary,
        "ts": time.time(),
    }
    with open(queue, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    # CLI: python3 ima_importer.py < url_list.jsonl
    # 每行: {"url":..., "title":...}
    results = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        r = import_one(obj['url'], obj.get('title', ''))
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))
    queued = sum(1 for r in results if r['status'] == 'queued')
    failed = sum(1 for r in results if r['status'] == 'failed')
    print(f"# summary: queued={queued} failed={failed} total={len(results)}", file=sys.stderr)
    print("# 待导入队列已写入 ima_import_queue.jsonl，由外层 IMA 客户端（MCP/API/手动）消费", file=sys.stderr)
