# legal-weekly-briefing

> **你的第二大脑的输入管道。** 每周法院公众号发几十篇文章——7 维可解释法律评分引擎帮你挤出 10 条值得精读的判例和方法论，其余全量进 IMA 知识库，以后打官司直接搜。

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-22c55e)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Level 1](https://img.shields.io/badge/Level%201-zero--deps-blue)](scripts/scoring_engine.py)
[![CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-green.svg)](LICENSE)
[![community](https://img.shields.io/badge/community-open%20source-7c5e3e)](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing)
[![version](https://img.shields.io/badge/version-v3.0.0-7c5e3e)](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing/releases)

> [查看 Demo 周报效果](https://github.com/5tnb6xgsm5-ops/legal-weekly-briefing/blob/main/assets/showcase/demo-weekly.png)

> ⚠️ **通道状态披露**：2026-07-29 微信公众平台关闭 MP 跨号搜索接口，本仓库内容发现通道已切换至微信读书「搜一搜」（主）+ 元宝反查（补），公开 API 通道（WSA / TokenHub）经实测均不覆盖公众号内容。详见 [STATUS.md](STATUS.md) —— 含微信读书可实施接口端点清单（不含实施步骤）。

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
| HTML 周报 · Radar 雷达区 | 未进精读的 legal 条目（最多 8 条），低分条做低调视觉标记——执业圈外趋势不放过 | 【6.5】矿产资源法实施条例施行 |
| `candidates.jsonl` | `build_candidates.py` 构建的 7 维特征候选池 | `{"features":{"case_density":4,"norm_anchoring":3,...}}` |
| `ima_import_queue.jsonl` | 待入库队列（url + folder_id + 分类），由 IMA 客户端消费 | `{"url":"...","folder_id":"...","category":"公司"}` |
| `run-report.json` | 执行报告（候选数、导入数、自检结果） | `{"self_check":{"ok":true}}` |

## 快速开始

```bash
# 1. 安装 skill 后，进入技能目录
cd ~/.workbuddy/skills/legal-weekly-briefing   # 或你的 skill 安装路径

# 2. 构建候选池（7 维特征标注）
# build_candidates.py 负责特征提取+标注+分类，产出入参格式的 candidates.jsonl
PYTHONPATH=scripts python3 scripts/build_candidates.py

# 3. 跑流水线（周报输出在 scripts/ 下：周报_<日期>.md / .html）
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

**输入**（`candidates.jsonl` 节选，v3 7 维特征）：
```json
{"title":"董监高违反勤勉义务的赔偿责任认定","url":"http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555271&idx=1&sn=b1400188c0f5bacf94f7b60371abfb3b&chksm=8451acf5b32625e3#rd",
 "category":"legal","source":"上海二中院",
 "features":{"case_density":3,"norm_anchoring":4,"actionability":3,
   "author_empirical_depth":4,"framework_quality":3,"relevance_halflife":4,
   "jurisdictional_proximity":0}}
```

**执行**：`run_pipeline.py` 去重 → 7-D k-NN 评分 → diversity-aware 选 10 条 → 写周报 → 法院来源且分数≥7.0 的写入 IMA 队列。

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
| 评分依据 | 发布时间 / 来源权重 | **7 维 k-NN 加权评分**，基于 62 条人工标注训练集，自动映射旧维度保持向后兼容 |
| 三层分流 | 单一输出 | **精读区（10 条）+ Radar 雷达区（8 条）+ IMA 入库（全量）** 分流，噪音自然落选 |
| 法律专业性 | 通用关键词 | 法院公众号专属 taxonomy（10 类），priority 裁决避免误分类 |
| 内容发现 | 固定来源 | **Pre-flight Check**：启动时检测 MP 可用性 → 路径声明 → 摘要三级回退（MP digest → snippet → WebFetch） |
| 冷启动 | 无 | 训练集缺失时线性降级打分，不崩 |

## 核心升级：v3.0 评分引擎 4D → 7D

v3.0 将法律条目评分从 4 维扩展到 7 维，提供更精细的实务价值区分度：

| 维度 | 权重 | 说明 |
|------|------|------|
| `case_density` | 0.18 | 案例密度——有没有具体案子 |
| `norm_anchoring` | 0.18 | 规范锚定——是否回到法条/司法解释/入库案例 |
| `actionability` | 0.18 | 可操作性——读完能直接拿走的规则 |
| `author_empirical_depth` | 0.16 | 作者实证深度——不看头衔看审级+论证功底 |
| `framework_quality` | 0.12 | 框架定性——先定法域框架 vs 堆材料 |
| `relevance_halflife` | 0.10 | 时效半衰期——基础方法永不过时 vs 前沿快过时 |
| `jurisdictional_proximity` | 0.08 | 地域贴近度——管辖地匹配加分 |

旧 4 维（`author_tier` / `platform_tier` / `depth` / `relevance`）权重置零，保留字段兼容旧训练集。

## 安全边界

- **不删不改你的文件**：流水线只新增 `周报_*.md` / `candidates.jsonl` / `ima_import_queue.jsonl` / `run-report.json`，不碰源数据。
- **不自动发外部请求**：`ima_importer.py` 只产出队列文件，真正的 IMA API 调用由外层客户端（MCP/你的脚本）显式执行——你掌控每一次上传。
- **不泄露凭证**：`~/.config/ima/client_id` + `api_key` 由你本地保管，脚本不读取、不打印、不打包。
- **分类不确定会停下**：无 folder_id 匹配时写入 `failed_import.jsonl` 等你补配置，不静默丢弃。
- **不会因同一来源刷屏**：`max_per_source=2` 限制同源在周报中最多 2 条。
- **IMA 知识库仅限自建**：不指引用户订阅/加入非自建 KB，`knowledge_base_id` 占位符未替换时导入自动阻断。

## 文件结构

```
legal-weekly-briefing/
├── SKILL.md                     ← 技能主文档（触发词 + 架构 + 用法）
├── README.md                    ← 本文件
├── scripts/
│   ├── scoring_engine.py        ← 7-D k-NN 评分引擎 v3.0（核心）
│   ├── run_pipeline.py          ← 流水线编排：去重→评分→周报→HTML渲染→IMA队列
│   ├── build_candidates.py      ← 候选构建：7 维特征标注 + 动态法院层级检测
│   ├── demo.py                  ← 演示周报生成（零配置体验）
│   ├── render_html.py           ← HTML 渲染器（含 Radar 雷达区）
│   ├── dedupe.py                ← URL/标题去重
│   ├── ima_importer.py          ← IMA 分类 + 队列写出 + 去重缓存管理
│   ├── import_ima.py            ← 独立 IMA OpenAPI 导入器
│   ├── fetch_mp_week.py         ← MP 文章批量拉取（需 Session）
│   ├── normalize_url.py         ← 聚合链接还原为 mp 原始链接
│   ├── verify.py                ← 回归测试（23 项，安装后自检）
│   └── install.sh               ← 一键安装脚本
├── assets/
│   ├── config/
│   │   ├── settings.yaml        ← v3 权重/阈值/条数/兴趣赛道（开源用户按领域改）
│   │   ├── sources.yaml         ← 搜索关键词 / MP 账号配置
│   │   └── taxonomy.yaml        ← IMA 分类映射（⚠️ folder_id 需替换为你自己的）
│   └── data/
│       ├── scoring-training.jsonl  ← 62 条标注训练集（v3 自动映射旧维度→新维度）
│       └── test-prompts.json       ← verify.py 使用的回归样例
└── references/
    ├── feature-guide.md            ← 特征标注速查 + 石头评分八判据（v2.0）
    ├── 评分体系维护指南.md          ← 评分标准维护 + 加新号/校准操作清单
    ├── adaptation-wizard.md        ← 适配向导 4 问流程
    ├── ima-level2-guide.md         ← IMA Level 2 完整指南
    ├── ima-pitfalls.md             ← IMA 接入踩坑卡
    ├── mp-setup-guide.md           ← ~~MP 自动发现完整配置~~ ⚠️ DEPRECATED（2026-07-29 微信关闭跨号接口）
    ├── weread-setup-guide.md       ← 微信读书搜一搜配置（主通道）
    ├── yuanbao-setup-guide.md      ← 元宝反查配置（补充通道）
    ├── delivery-gate.md            ← 交付门禁卡（23 项核查）
    └── automation-setup.md         ← 自动化调度配置
```

## 验证与测试

安装后运行：

```bash
PYTHONPATH=scripts python3 scripts/verify.py
```

期望输出：`23 通过 / 0 失败`（已配置微信读书登录态时）；未配置登录态的机器为 `22 通过 / 1 失败`——W1 门禁会提示运行 `python3 scripts/weread_login.py` 扫码，属预期行为，不影响评分/演示链路。若其余项失败，说明 `assets/config/` 路径未被正确加载（检查 `BASE` 解析），或训练集格式损坏。

**Level 3 内容发现前置**：自动抓取公众号文章需要 `pip3 install playwright && python3 -m playwright install chromium`（首次）并完成微信读书扫码登录；缺任一依赖时，流水线会自动降级到下一层通道，周报仍可产出。

**真实数据回放**：将你自己的周报候选粘贴为 `candidates.jsonl`，跑 `run_pipeline.py`，对比输出分数与你的主观判断。62 条训练集偏特定执业方向视角，若你的领域不同，直接编辑 `scoring-training.jsonl` 的标注即可——引擎会自动 coalesce 同向量、冷启动兜底。

## 分级架构（按需取用）

| Level | 依赖 | 能力 |
|-------|------|------|
| **Level 0** | Python 3.9+ | `demo.py` 演示周报（零配置，5 分钟体验） |
| **Level 1** | Python 3.9+ | 评分引擎 + 周报生成（零外部依赖） |
| **Level 2** | + IMA 账号 | 全量入库 IMA 知识库（RAG 检索增强） |
| **Level 3** | + 微信读书账号 | 自动发现法院公众号文章（微信读书「搜一搜」主通道，2026-07-29 微信关闭 MP 跨号接口后确立；元宝反查为补充通道） |

每一级可独立运行，上层依赖下层。开源用户若无微信读书账号，用 WebSearch 替代 Level 3 的内容发现即可。

## License

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) —— 可自由共享、演绎（含商业用途），须署名并相同方式共享。
