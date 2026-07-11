#!/usr/bin/env python3
"""周报条目优先级自动打分引擎 v2.1（开源化改造）

变更：
- 权重/阈值/兴趣关键词从 config/settings.yaml 读取
- 训练集缺失或为空时冷启动降级（线性映射打分 + confidence=0）
- 不再依赖硬编码个人路径

用法：
    echo '{"features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}' | python3 scoring_engine.py legal
    echo '{"features":{"first_hand":1,"depth":1,"relevance":1}}' | python3 scoring_engine.py ai-legal
"""

import json, sys, math
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# 技能根目录（scripts/ 的上一级），assets/ 与 scripts/ 同级
BASE = Path(__file__).resolve().parent.parent
CONFIG = BASE / "assets" / "config" / "settings.yaml"

# 默认值（config 缺失时回退，保证单文件可用）
DEFAULT_LEGAL_WEIGHTS = {'author_tier': 0.35, 'platform_tier': 0.30, 'depth': 0.20, 'relevance': 0.15}
DEFAULT_AI_LEGAL_WEIGHTS = {'signal_strength': 0.50, 'depth': 0.25, 'relevance': 0.15, 'domestic_relevance': 0.10, 'author_tier': 0.00, 'platform_tier': 0.00}
DEFAULT_INTEREST_KW = ['婚姻', '家事', '抚养', '继承', '离婚', '恋爱', '公司', '股东', '股权', '法人', '商标', '医疗', '诊疗', '知情']
DEFAULT_TRAINING = BASE / "assets" / "data" / "scoring-training.jsonl"


def normalize_features(feat, category):
    """字段兼容：补齐 v2 新增维度，旧训练集/候选缺字段时填中性默认。

    - signal_strength: 缺则按 first_hand 映射（1→2 应用落地, 0→3 融资动态），均缺默认 2
    - domestic_relevance: 缺默认 0
    - author_tier/platform_tier: 保留（权重已置 0，不影响距离）
    """
    f = dict(feat)
    if category == 'ai-legal':
        if 'signal_strength' not in f:
            fh = f.get('first_hand')
            if fh == 1:
                f['signal_strength'] = 2
            elif fh == 0:
                f['signal_strength'] = 3
            else:
                f['signal_strength'] = 2  # 中性默认：应用落地级
        if 'domestic_relevance' not in f:
            f['domestic_relevance'] = 0
    return f


def coalesce_vectors(data):
    """训练集加载后合并相同特征向量：同向量多条 → 1 条，分数取均值。

    防 k-NN 同向量多重命中（1/dist 权重虚高绑架预测）。
    训练集文件全量保留（不物理删除），仅此处运行时合并。
    返回新 list，每条含合并后的 'features' 与 'score'（均值）。
    """
    groups = {}
    for d in data:
        cat = d.get('category', d.get('type', ''))
        f = normalize_features(d.get('features', {}), cat)
        key = (cat, tuple(sorted(f.items())))
        groups.setdefault(key, []).append(d)
    out = []
    for (cat, _), items in groups.items():
        scores = [it.get('score', it.get('manual', it.get('predicted', 5.0))) for it in items]
        merged = dict(items[0])
        merged['features'] = normalize_features(items[0].get('features', {}), cat)
        merged['score'] = round(sum(scores) / len(scores), 2)
        merged['_merged_count'] = len(items)
        out.append(merged)
    return out


def load_settings():
    if yaml is None or not CONFIG.exists():
        return {}
    cfg = yaml.safe_load(open(CONFIG)) or {}
    # 版本化 merge：旧 config（无 schema_version）自动补全缺失字段，不全量覆盖
    if 'schema_version' not in cfg.get('scoring', {}):
        sc = cfg.setdefault('scoring', {})
        sc.setdefault('legal_weights', DEFAULT_LEGAL_WEIGHTS)
        sc.setdefault('ai_legal_weights', DEFAULT_AI_LEGAL_WEIGHTS)
        sc.setdefault('schema_version', 1)
    return cfg


def get_weights(category, settings):
    sc = settings.get('scoring', {})
    if category == 'legal':
        return sc.get('legal_weights', DEFAULT_LEGAL_WEIGHTS)
    return sc.get('ai_legal_weights', DEFAULT_AI_LEGAL_WEIGHTS)


def get_interest_kw(settings):
    sc = settings.get('scoring', {})
    return sc.get('interest_keywords', DEFAULT_INTEREST_KW)


def get_training_path(settings):
    sc = settings.get('scoring', {})
    p = sc.get('training_path', str(DEFAULT_TRAINING))
    return Path(p) if Path(p).is_absolute() else BASE / p


def load_training(path):
    """返回训练集 list；文件缺失/空返回 []（冷启动）。"""
    if not path.exists():
        return []
    data = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data


def feature_distance(a_feat, b_feat, weights):
    dist = 0.0
    total_w = 0.0
    for k, w in weights.items():
        if k in a_feat and k in b_feat:
            dist += w * abs(a_feat[k] - b_feat[k])
            total_w += w
    return dist / max(total_w, 0.001)


def linear_fallback(entry, category, weights):
    """冷启动：无训练集时按特征权重线性映射到 1-10 分。"""
    feat = entry.get('features', {})
    if category == 'legal':
        # author_tier 1-4（越小越高），platform_tier 1-5（越小越高），depth/relevance 1-3（越小越高）
        score = 10.0
        score -= (feat.get('author_tier', 3) - 1) * 1.2
        score -= (feat.get('platform_tier', 3) - 1) * 0.8
        score -= (feat.get('depth', 2) - 1) * 0.6
        score -= (feat.get('relevance', 2) - 1) * 0.4
    else:
        # AI+法律冷启动：signal_strength 1格局/2落地/3融资（越小越高），depth/relevance 越小越高
        ss = feat.get('signal_strength', feat.get('first_hand', 1))
        # signal_strength 映射：1→9分基准, 2→7分, 3→5分
        base = {1: 9.0, 2: 7.0, 3: 5.0}.get(ss, 7.0)
        score = base
        score -= (feat.get('depth', 2) - 1) * 0.5
        score -= (feat.get('relevance', 2) - 1) * 0.3
    return max(1.0, min(10.0, score))


def predict(entry, category='legal'):
    """Predict score and confidence for a single entry."""
    settings = load_settings()
    weights = get_weights(category, settings)
    training_path = get_training_path(settings)
    data = load_training(training_path)

    # 冷启动降级
    if not data:
        score = linear_fallback(entry, category, weights)
        bonus = 0.0
        if category == 'legal' and 'title' in entry:
            for kw in get_interest_kw(settings):
                if kw in entry['title']:
                    bonus = 0.3
                    break
        return round(score + bonus, 1), 0.0  # confidence=0 标记冷启动

    pool = [d for d in data if d.get('category', d.get('type', '')) == category]
    if not pool:
        # 该类别无训练样本，退回到全量近邻
        pool = data

    # 训练集 coalesce：同特征向量合并取均值（防权重虚高）
    pool = coalesce_vectors(pool)

    entry_feat = normalize_features(entry.get('features', {}), category)

    scored = []
    for d in pool:
        dist = feature_distance(entry_feat, d.get('features', {}), weights)
        scored.append((dist, d.get('score', d.get('manual', d.get('predicted', 5.0)))))
    scored.sort()

    k = min(5, len(scored))
    neighbors = scored[:k]

    total_w = 0.0
    weighted_sum = 0.0
    for dist, score in neighbors:
        w = 1.0 / max(dist, 0.001)
        weighted_sum += w * score
        total_w += w
    predicted = weighted_sum / max(total_w, 0.001)

    nscores = [s for _, s in neighbors]
    score_range = max(nscores) - min(nscores)
    avg_dist = sum(d for d, _ in neighbors) / len(neighbors)
    agreement = 1.0 - (score_range / 5.0)
    proximity = max(0, 1.0 - avg_dist * 2)
    confidence = (agreement * 0.6 + proximity * 0.4)
    if score_range == 0 and avg_dist < 0.3:
        confidence = max(confidence, 0.85)

    bonus = 0.0
    if category == 'legal' and 'title' in entry:
        for kw in get_interest_kw(settings):
            if kw in entry['title']:
                bonus = 0.3
                break

    return round(predicted + bonus, 1), round(min(1.0, confidence), 2)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: echo '{...}' | python3 scoring_engine.py <legal|ai-legal>", file=sys.stderr)
        sys.exit(1)
    cat = sys.argv[1]
    inp = json.loads(sys.stdin.read())
    score, conf = predict(inp, cat)
    print(json.dumps({"predicted_score": score, "confidence": conf, "need_review": conf < 0.8}, ensure_ascii=False))
