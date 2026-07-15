# legal-weekly-briefing

> **你的第二大脑的输入管道。** 每周法院公众号发几十篇文章——可解释的 k-NN 评分引擎帮你挤出 10 条值得精读的判例和方法论，其余全量进 IMA 知识库，以后打官司直接搜。

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-22c55e)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Level 1](https://img.shields.io/badge/Level%201-zero--deps-blue)](scripts/scoring_engine.py)
[![MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![community](https://img.shields.io/badge/community-open%20source-7c5e3e)](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing)

> [查看 Demo 周报效果](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing/blob/main/assets/showcase/demo-weekly.png)

## 🚀 安装（30 秒）

**只需把这个仓库地址发给 AI 工具：**

```
https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing
```

然后说一句：**"帮我安装这个 skill"**——WorkBuddy 会自动 clone、配置、就绪。

> 也可以手动安装：下载 [最新 Release](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing/releases/latest)，解压到 `~/.workbuddy/skills/legal-weekly-briefing/`。

## 5 分钟看到产出

```bash
# 一行安装
bash scripts/install.sh

# 一条命令看演示周报
python3 scripts/demo.py
```

输出 `周报_demo_<日期>.md` — AI+法律 3 条 + 纯法律 7 条，用任意 Markdown 编辑器打开即可阅读。想用自己的数据？在对话中说「帮我配置法律周报」，AI 会引导你设置执业方向、兴趣赛道和公众号来源。

## 你什么时候需要它？

1. **你关注了 5+ 个法院/法律类公众号**，每周末想快速知道"这周哪些文章值得精读"——但手动刷要半小时，且容易漏掉深度好文。
2. **你在用 IMA / 类似知识库做 RAG**，需要持续往里喂高质量法律实务文章，但手动复制链接太慢、分类太烦。
3. **你带团队或做内容运营**，需要一份可复用的"法律周报生成 SOP"，而不是每次都从零写提示词。

## 它会交付什么？

| 产物 | 说明 | 示例 |
|------|------|------|
| 周报 MD / HTML | 10 条精选（AI+法律 3 + 纯法律 7），按分数降序，带领域标签 | 【9.5】Harvey × Microsoft 365 原生集成 |
| `ima_import_queue.jsonl` | 待入库队列（url + folder_id + 分类），由 IMA 客户端消费 | `{"url":"...","folder_id":"...","category":"公司"}` |
| `run-report.json` | 执行报告（候选数、导入数、自检结果） | `{"self_check":{"ok":true}}` |

## 快速开始

```bash
# 1. 安装 skill 后，进入技能目录
cd ~/.workbuddy/skills/legal-weekly-briefing   # 或你的 skill 安装路径

# 2. 准备候选文件 candidates.jsonl（每行一条）
# {"title":"文章标题","url":"https://...","category":"legal","source":"上海一中院",
#  "features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}

# 3. 跑流水线
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl

# 4. 自检评分引擎是否工作正常
PYTHONPATH=scripts python3 scripts/verify.py
```

**零依赖运行**：Level 1（纯评分引擎）只需 Python 3.9+，不需要任何第三方账号。
`pip install pyyaml` 可选——缺失时自动回退内置默认值。

## 触发方式

用户/Agent 在对话中说这些话时，应加载本 skill：

- "生成法律周报"
- "帮我筛这周的法院公众号文章"
- "把这批法律文章按质量排个序"
- "案例入库 / 法律文章分类到 IMA"
- "AI 法律新闻简报"

## 示例

**输入**（`candidates.jsonl` 节选）：
```json
{"title":"董监高违反勤勉义务的赔偿责任认定","url":"http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555271&idx=1&sn=b1400188c0f5bacf94f7b60371abfb3b&chksm=8451acf5b32625e3#rd",
 "category":"legal","source":"上海二中院",
 "features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}
```

**执行**：`run_pipeline.py` 去重 → k-NN 评分 → diversity-aware 选 10 条 → 写周报 → 法院来源且分数≥8.0 的写入 IMA 队列。

**输出**（周报片段）：
```
# 法律周报 2026-07-10

## AI + 法律
【9.5】Harvey × Microsoft 365 原生集成
https://www.harvey.ai/blog/harvey-accelerates-enterprise-ai

## 纯法律
【9.0】董监高违反勤勉义务的赔偿责任认定
http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555271&idx=1&sn=b1400188c0f5bacf...
```

## 它和同类有什么不同？

| 维度 | 通用 RSS/News Digest Skill | 本 Skill |
|------|---------------------------|---------|
| 评分依据 | 发布时间 / 来源权重 | **k-NN 近邻评分**，基于 62 条人工标注训练集，区分"体系化方法论"vs"个案叙事" |
| 双管道 | 单一输出 | **周报管道（精选 10 条）+ 知识库管道（全量入库）** 分流 |
| 法律专业性 | 通用关键词 | 法院公众号专属 taxonomy（婚姻家事/公司/建工/劳保…10 类），priority 裁决避免误分类 |
| 冷启动 | 无 | 训练集缺失时线性降级打分，不崩 |

## 安全边界

- **不删不改你的文件**：流水线只新增 `周报_*.md` / `ima_import_queue.jsonl` / `run-report.json`，不碰源数据。
- **不自动发外部请求**：`ima_importer.py` 只产出队列文件，真正的 IMA API 调用由外层客户端（MCP/你的脚本）显式执行——你掌控每一次上传。
- **不泄露凭证**：`~/.config/ima/client_id` + `api_key` 由你本地保管，脚本不读取、不打印、不打包。
- **分类不确定会停下**：无 folder_id 匹配时写入 `failed_import.jsonl` 等你补配置，不静默丢弃。
- **不会因同一来源刷屏**：`max_per_source=2` 限制同源在周报中最多 2 条。

## 文件结构

```
legal-weekly-briefing/
├── SKILL.md                     ← 技能主文档（触发词 + 架构 + 用法）
├── README.md                    ← 本文件
├── scripts/
│   ├── scoring_engine.py        ← k-NN 评分引擎 v2.1（核心）
│   ├── run_pipeline.py          ← 流水线编排：去重→评分→周报→IMA队列
│   ├── dedupe.py                ← URL/标题去重
│   ├── ima_importer.py          ← IMA 分类 + 队列写出（不直接调 API）
│   ├── normalize_url.py         ← 聚合链接还原为 mp 原始链接
│   └── verify.py                ← 回归测试（6 样例，安装后自检）
├── assets/
│   ├── config/
│   │   ├── settings.yaml        ← 权重/阈值/条数/兴趣赛道（开源用户按领域改）
│   │   ├── sources.yaml         ← 搜索关键词 / MP 账号配置
│   │   └── taxonomy.yaml        ← IMA 分类映射（⚠️ folder_id 需替换为你自己的）
│   └── data/
│       ├── scoring-training.jsonl  ← 62 条人工标注训练集
│       └── test-prompts.json       ← verify.py 使用的回归样例
└── references/
    └── feature-guide.md         ← 特征标注速查（4 维度取值定义 + 示例）
```

## 验证与测试

安装后运行：

```bash
PYTHONPATH=scripts python3 scripts/verify.py
```

期望输出：`6 通过 / 0 失败`。若失败，说明 `assets/config/` 路径未被正确加载（检查 `BASE` 解析），或训练集格式损坏。

**真实数据回放**：将你自己的周报候选粘贴为 `candidates.jsonl`，跑 `run_pipeline.py`，对比输出分数与你的主观判断。62 条训练集偏特定执业方向视角，若你的领域不同，直接编辑 `scoring-training.jsonl` 的标注即可——引擎会自动 coalesce 同向量、冷启动兜底。

## 分级架构（按需取用）

| Level | 依赖 | 能力 |
|-------|------|------|
| **Level 1** | Python 3.9+ | 评分引擎 + 周报生成（零外部依赖） |
| **Level 2** | + IMA 账号 | 全量入库 IMA 知识库（RAG 检索增强） |
| **Level 3** | + MP 后台权限 | 自动拉取法院公众号三账号文章（需 [wechat-ocr-research](https://github.com/5tnb6xgsm5-ops/wechat-ocr-research) skill） |

每一级可独立运行，上层依赖下层。开源用户若无 MP 权限，用 WebSearch 替代 Level 3 的内容发现即可。

## License

MIT —— 随便改，随便发，注明出处就行。
