#!/usr/bin/env python3
"""Level 0 · 5分钟快速体验:从预置示范候选生成一份演示周报。

用法:
    python3 scripts/demo.py

输出:
    周报_demo_<日期>.md — 包含 AI+法律(3条) + 纯法律(7条)的演示周报

预置数据:10 条真实法律新闻候选,标注好特征向量。无需手动建 candidates.jsonl,
也无需配置文件。适合首次接触本 skill 的用户快速看到"它最终产出的样子"。
"""

import json
import sys
import os
from datetime import date

# 预置示范候选（与 scoring-training.jsonl 不同——这批是带真实 URL 的文章）
DEMO_CANDIDATES = [
    {
        "title": "全文发布！涉新质生产力企业典型案例",
        "url": "http://mp.weixin.qq.com/s?__biz=MjM5MjkwMDkxMA==&mid=2649581720&idx=1&sn=9dbab238774e7cc02bc8537cec218cc7&chksm=be86fad989f173cf57b0d3311337411a30609385ce802743df9d56f81c4eb600d6037c75c614#rd",
        "category": "legal",
        "source": "上海一中院",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "上海一中院发布涉新质生产力企业典型案例全文，涵盖科技创新、数据权益、绿色转型等前沿领域的司法裁判规则，附完整裁判要旨。",
    },
    {
        "title": "入库案例：抵押预告登记权利人能否就抵押物享有优先受偿权",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451717&idx=1&sn=697022fc928809af13d55f3cfa5c627f&chksm=8bffbfaebc8836b821a8c3348383efb2314b8c8315fc43c2c3a57e563d0e6fc9349b43bfb60f#rd",
        "category": "legal",
        "source": "山东高法",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "人民法院案例库入库参考案例。围绕抵押预告登记权利人的优先受偿权认定和开发商阶段性保证责任免除问题，附完整裁判要旨。",
    },
    {
        "title": "夫妻借款后离婚，债权人要求一方单独出具借条，是否仍为夫妻共同债务？",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451718&idx=1&sn=8d7c1dfb648f9a4169249f37c8638a09&chksm=8bffbfadbc8836bb110fb0e9e6d11f50099a07b4643ed92d839453211b186d7d12fd6097b35e#rd",
        "category": "legal",
        "source": "山东高法",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "夫妻双方共同借款后协议离婚，债权人要求一方单独出具借条确认债务。山东高法结合《民法典》第1064条对夫妻共同债务规则进行实务分析。",
    },
    {
        "title": "董监高违反勤勉义务的赔偿责任认定",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555271&idx=1&sn=b1400188c0f5bacf94f7b60371abfb3b&chksm=8451acf5b32625e34de823f24e72f092553ff26e84fa25bd81e2b0c08a5ec43c8d18214a5d24#rd",
        "category": "legal",
        "source": "上海二中院",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 2},
        "preview": "上海二中院至正栏目案例分析。围绕新《公司法》下董监高勤勉义务的赔偿认定标准，从义务来源、违反判断、损害认定、因果关系四个维度展开。",
    },
    {
        "title": "超龄劳动者工作中受伤，能否获得工伤赔偿？",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451717&idx=2&sn=557fc6616940430b373da3fb0d0eb722&chksm=8bffbfaebc8836b89db92822208a8db9ccfe2c55a1b09befa535ab0e4837098e8f774d515b40#rd",
        "category": "legal",
        "source": "山东高法",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "超龄劳动者与用人单位是劳动关系还是劳务关系？工作中受伤应否适用《工伤保险条例》？山东高法系统梳理了超龄劳动者的工伤认定规则。",
    },
    {
        "title": "Harvey × Microsoft 365 原生集成，法律 AI 工具进入办公套件",
        "url": "https://www.harvey.ai/blog/harvey-accelerates-enterprise-ai-with-agentpowered-platform-and-microsoft-365-copilot",
        "category": "ai-legal",
        "source": "Artificial Lawyer",
        "features": {"signal_strength": 1, "depth": 1, "relevance": 2, "domestic_relevance": 0},
        "preview": "Harvey 与微软达成深度合作，法律 AI 能力嵌入 Word/Outlook/Teams 原生工作流，标志着法律科技从「独立工具」进入「办公基础设施」阶段。信号级别：格局级。",
    },
    {
        "title": "某大所任命首位首席 AI 官，组织架构为 AI 让路",
        "url": "https://legaltechnology.com/littler-appoints-stephanie-goutos-as-inaugural-chief-ai-officer",
        "category": "ai-legal",
        "source": "Law.com",
        "features": {"signal_strength": 2, "depth": 1, "relevance": 1, "domestic_relevance": 1},
        "preview": "美国顶级律所首次设立 C-suite 级别的 AI 职位，负责全所 AI 战略、工具选型与律师培训。国内律所可参考其组织架构调整思路。信号级别：应用落地级。",
    },
    {
        "title": "合同审查 AI 新突破：基于大模型的条款级风险识别",
        "url": "https://justee.ai/blog/ai-contract-review-guide",
        "category": "ai-legal",
        "source": "LegalTech News",
        "features": {"signal_strength": 2, "depth": 1, "relevance": 2, "domestic_relevance": 0},
        "preview": "新一代合同审查 AI 不再做「整体风险评估」，而是直接定位到具体条款并给出修改建议，准确率突破 90%。信号级别：应用落地级。",
    },
    {
        "title": "老板说「滚」，员工离岗后被指旷工遭解雇",
        "url": "http://mp.weixin.qq.com/s?__biz=MjM5MjkwMDkxMA==&mid=2649581701&idx=1&sn=b92674592614324c4f6a087ba8306759&chksm=be86fac489f173d2c9c3d6da743c86ce1bdbe03c5e42c25adec2905c76f9e54c25f8e711b08d#rd",
        "category": "legal",
        "source": "上海一中院",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "老板口头说出「滚」字后员工离岗，用人单位以旷工为由解雇。口头表达是否构成解除劳动合同的意思表示？上海一中院从意思表示解释角度作出认定。",
    },
    {
        "title": "《建工司法解释（二）》条文解读（上）",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555265&idx=1&sn=34f487fd7e48c7d75261a4f304bd83fe&chksm=8451acf3b32625e51f86c195dd96dec936b65a58f37cc808e1158292b818cf2acbe1e718a17a#rd",
        "category": "legal",
        "source": "上海二中院",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "上海二中院对最高法《建工司法解释（二）》逐条解读，涵盖合同效力认定、实际施工人权利保护、工程价款优先受偿等核心条文。",
    },
]


def generate_demo_report():
    today = date.today().strftime("%Y-%m-%d")

    legal_items = [c for c in DEMO_CANDIDATES if c["category"] == "legal"]
    ai_legal_items = [c for c in DEMO_CANDIDATES if c["category"] == "ai-legal"]

    # 简单排序：depth=1 优先，然后 author_tier 低的优先
    def legal_sort_key(c):
        return (c["features"]["depth"], c["features"]["author_tier"])

    def ai_sort_key(c):
        return (c["features"]["signal_strength"], c["features"]["depth"])

    legal_items.sort(key=legal_sort_key)
    ai_legal_items.sort(key=ai_sort_key)

    lines = []
    lines.append(f"# 法律周报 Demo · {today}")
    lines.append("")
    lines.append(
        "> ⚡ 本份为演示周报，使用预置示范候选数据生成。想用自己的数据？看下方「下一步」。"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🤖 AI + 法律")
    lines.append("")

    for item in ai_legal_items[:3]:
        signal = item["features"]["signal_strength"]
        signal_label = {1: "格局级", 2: "应用落地级", 3: "融资动态级"}.get(signal, "")
        lines.append(f"### {item['title']}")
        lines.append(f"{item['url']}")
        lines.append("")
        lines.append(f"{item['preview']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## ⚖️ 纯法律")
    lines.append("")

    for item in legal_items[:7]:
        lines.append(f"### {item['title']}")
        lines.append(f"{item['url']}")
        lines.append("")
        lines.append(f"*{item['source']}* | {item['preview']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📋 元数据")
    lines.append("")
    lines.append(
        f"- **引擎版本**: Level 0 Demo (k-NN 评分引擎 v2.1 就绪，本演示跳过评分)"
    )
    lines.append(f"- **数据来源**: 10 条预置示范候选")
    lines.append(f"- **生成日期**: {today}")
    lines.append("")
    lines.append("## 🚀 下一步")
    lines.append("")
    lines.append(
        "1. **换成你自己的候选文章** → 创建 `candidates.jsonl`（格式见下方示例）"
    )
    lines.append("2. **跑真实评分引擎** → `PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl`")
    lines.append("3. **让 AI 帮你适配** → 在对话中说「帮我配置法律周报」，AI 会引导你设置执业方向、兴趣赛道和公众号来源")
    lines.append("")
    lines.append("### candidates.jsonl 示例格式")
    lines.append("")
    lines.append("```json")
    lines.append(
        '{"title":"你的文章标题","url":"https://...","category":"legal","source":"上海一中院","features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}'
    )
    lines.append("```")
    lines.append("")
    lines.append(
        "> 不知道 `features` 怎么标？看 `references/feature-guide.md` 或者直接问 AI：「帮我对这些文章标注特征向量」。"
    )
    lines.append("")

    report_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        f"周报_demo_{today}.md",
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ 演示周报已生成: {report_path}")
    print(f"   包含 {len(ai_legal_items[:3])} 条 AI+法律 + {len(legal_items[:7])} 条纯法律")
    print(f"   用 Markdown 编辑器/MacDown/Typora 打开即可阅读")
    print(f"")
    print(f"   下一步: 创建你自己的 candidates.jsonl 后跑真实评分引擎:")
    print(f"   PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl")


if __name__ == "__main__":
    generate_demo_report()
