---
name: legal-weekly-briefing
description: "用户说「生成法律周报」「帮我筛法院公众号文章」「法律简报」「案例入库」时触发。从法院公众号（上海一中院/二中院/山东高法等）文章中用可解释的 k-NN 评分引擎筛出 10 条精品周报，其余实务文章全量入库 IMA 知识库做 RAG。临时法律热点查询走 legal-hot，不要用本 skill。"
author: "社区贡献者"
agent_created: true
---

# 法律周报自动化 · Legal Weekly Briefing

## 第一性原理

律师每周从关注的法院公众号（山东高法、上海一中院、上海二中院等）中筛选高质量文章。这件事的本质是：

> **同一批法院公众号文章，走两条管道分流——**
> **周报管道：** 评分引擎挑 10 条精品 → 律师主动阅读
> **知识库管道：** 全量实务文章入库 IMA → 检索增强（RAG）

周报解决"本周重点看什么"，知识库解决"以后能找到什么"。两条管道共享同一个内容发现层，在评分环节分叉。

**本 skill 的核心交付模式是「配置一次，每周自动推送」——不是每次手动触发。** 配置完成后依赖外部调度层（WorkBuddy Automation / GitHub Actions cron / 系统 cron）每周定时触发，用户只需读周报。

### 🚀 快速开始（零基础·不看下面也能用）

> **如果你不想读完整篇文档**，只需在 WorkBuddy 对话中说：
>
> 「使用 legal-weekly-briefing skill 生成本周法律周报」
>
> AI 会自动搜索近一周的法律动态和法院公众号文章，评分排序后输出周报。
>
> **想看到底长什么样？**→ 在对话中说「帮我用 legal-weekly-briefing 生成一份演示周报」，AI 自动生成。
>
> **想用自己的数据跑？**→ 在对话中说「帮我配置法律周报」，AI 按适配向导一步步引导你。
>
> ⚠️ 以下「自动化配置」和「分级架构」是进阶内容——第一次用可以先跳过，直接看 Level 0。

## 自动化配置

> 📌 **如果你只打算在对话中手动触发周报**（每次说「生成法律周报」），**跳过本节**，直接看 [Level 0](#level-0)。本节是为想设置「每周自动推送」的用户准备的进阶内容。

本 skill 需要外部调度层定时触发。推荐每周推送两次（周三 + 周五），覆盖工作周中段和周末前的法律更新节奏。

### 方式 A：WorkBuddy Automation（推荐）

在 WorkBuddy 中创建自动化任务，每周三、周五上午 9:00 自动执行：

```
schedule: FREQ=WEEKLY;BYDAY=WE,FR;BYHOUR=9;BYMINUTE=0
prompt: 使用 legal-weekly-briefing skill 生成本周法律周报，拉取近一周公众号文章，评分排序后输出周报并入库 IMA。
```

> 注意：自动化任务和日常对话共用同一模型额度池。若额度紧张，建议用方式 B 隔离执行环境。

### 方式 B：GitHub Actions cron

将本仓库 Fork 后，添加 `.github/workflows/weekly-briefing.yml`：

```yaml
on:
  schedule:
    - cron: '0 1 * * 3'   # 每周三北京时间 9:00
    - cron: '0 1 * * 5'   # 每周五北京时间 9:00
```

这种方式隔离额度，且运行日志可追溯。

### 方式 C：系统 cron / launchd

```bash
# macOS launchd: ~/Library/LaunchAgents/com.legal-weekly.plist
# 每周三、周五上午 9:00 运行 pipeline
```

---

## 分级架构

为降低开源用户的门槛，架构按依赖关系分为四级。每一级可以独立运行，上层依赖下层。

```
Level 0 · 5 分钟快速体验（零配置，零依赖）
  └─ 预置 10 条示范候选 → demo.py → 演示周报 MD
     适用：第一次接触，想看看「最终产出长什么样」的用户

Level 1 · 纯评分引擎（零外部依赖）
  └─ 用户提供候选 URL 列表 → scoring_engine.py → 评分排序 → 周报 MD
     适用：任何有 Python 的环境，不需要任何第三方账号

Level 2 · + IMA 知识库（需 IMA 账号）
  └─ Level 1 + ima_importer.py → 分类 → import_urls OpenAPI → 全量入库
     适用：有 IMA 知识库权限的用户

Level 3 · + MP 自动发现（需 MP 后台权限）
  └─ Level 1 + wechat-ocr-research skill → MP 后台拉取三账号文章
     适用：有微信公众号后台管理权限的用户
```

---

## ⚡ Level 0 · 5 分钟快速体验（零配置，零终端）{#level-0}

### 方式一：对 AI 说句话（推荐 · 不需要打开终端）

在 WorkBuddy 对话中输入：

> **「帮我用 legal-weekly-briefing 生成一份演示周报」**

AI 会自动运行 `demo.py`，生成一份演示周报（MD + HTML），包含 AI+法律 3 条 + 纯法律 7 条的示例内容。你只需等几秒，然后直接查看文件。

> **原理**：WorkBuddy 的 AI 可以直接在后台执行命令——你不需要知道终端是什么、Python 在哪、路径怎么配。AI 帮你处理这一切。

<details>
<summary>🖥️ 方式二：终端手动运行（备选）</summary>

如果你习惯用终端，或者在没有 WorkBuddy 的环境下使用：

```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
python3 scripts/demo.py
```

| 报错 | 解决 |
|------|------|
| `python3: command not found` | [python.org](https://python.org) 下载安装 |
| `No such file or directory` | 先确认路径正确：`ls ~/.workbuddy/skills/legal-weekly-briefing/scripts/demo.py` |
| `ModuleNotFoundError: No module named 'yaml'` | `pip3 install pyyaml` |

</details>

### 期望产出

无论方式一还是方式二，跑完后会生成两个文件：
- `周报_demo_<日期>.md` — 文字版周报
- `周报_demo_<日期>.html` — 网页版周报（浏览器打开，含摘要/推荐理由/原文链接）

### 下一步

看完 Demo 后想用自己的数据跑真实周报？

> 在 WorkBuddy 对话中说：**「帮我配置法律周报」**
>
> AI 会按适配向导一步步问你四个问题（执业方向、公众号、IMA、MP），配完后自动出你的第一份真实周报。

<details>
<summary>⚙️ 给 Agent 的指令：用户说「帮我生成演示周报」时</summary>

```
1. 确认 skill 目录存在：ls ~/.workbuddy/skills/legal-weekly-briefing/scripts/demo.py
2. 运行：cd ~/.workbuddy/skills/legal-weekly-briefing && python3 scripts/demo.py
3. 用 present_files 工具展示生成的两个文件（MD + HTML）
4. 告知用户：这就是最终产出——接下来可以用真实数据替换
```
</details>

---

## 🧭 适配向导 — 让 AI 帮你配置

**本节是给 Agent 的指令**。当你（用户）表示「想用这个 skill 生成我的法律周报」时，Agent 必须主动引导你完成以下四问，而不是等你去找配置文件。

### Agent 行为规则

```
加载本 skill 后，Agent 应主动询问用户：
  "我看到你想配置法律周报。我先问你几个问题，帮你一键配好——不用手动改配置文件。"

四个必问，按顺序：
  1. 执业方向 → 决定 interest_keywords + taxonomy priority
  2. 关注公众号 → 决定 sources.yaml（默认保留三个示范法院）
  3. MP 后台权限 → 决定是否启用 Level 3
  4. IMA 知识库 → 决定是否启用 Level 2

收集完毕后，Agent 自动修改 assets/config/ 下的 YAML 文件。
每改完一个配置，告诉用户改了什么、为什么这么改。
```

> 💡 **只想用 Level 1（纯周报，不建知识库）？** 在 Agent 问完前两问后，直接告诉它：「我只用 Level 1，不配 IMA 和 MP」。Agent 会跳过第三、四问，直接帮你完成 Level 1 配置。

### 第一问：执业方向 → 调整 interest_keywords + 分类权重

**Agent 引导话术**：

> 你主要是做哪个方向的？多选也行。（婚姻家事 / 公司 / 合同借贷 / 建筑工程 / 劳动法 / 交通事故 / 刑事 / 知识产权 / 行政法 / 其他）
>
> 如果有特别关注的细分领域（比如「医疗损害」「消费维权」「网络侵权」），也可以直接说，我帮你加到兴趣赛道里。

**Agent 收到回答后做什么**：

1. 将用户的执业方向关键词写入 `settings.yaml` 的 `interest_keywords`（替换当前默认视角的关键词）
2. 将用户的首选方向在 `taxonomy.yaml` 中 priority 调至最高（10），次要方向调至 9
3. 告知用户：「兴趣赛道加成 = +0.3 分，你的核心领域文章会天然排在周报前面」
4. **如果用户说「没有固定方向，只是广泛关注」**：Agent 保持 settings.yaml 默认配置不动，回复：「好的，那我保持全部分类权重均匀——周报会按文章质量自然排序，不偏向任何领域。以后有了主攻方向随时可以加。」

**示范**（某执业律师的当前配置）：
```
interest_keywords: 婚姻、家事、抚养、继承、离婚、恋爱、公司、股东、股权、法人、商标、医疗、诊疗、知情
```
→ 你的配置会按你的执业方向替换这行。

### 第二问：关注哪些公众号？→ 调整 sources.yaml

**Agent 引导话术**：

> 当前默认关注三个法院公众号：上海一中院、上海二中院、山东高法——这是示范配置。你有没有想加的其他法院或法律类公众号？
>
> 比如：你所在地的高院公众号、你常看案例的法院公众号、某个法律科技媒体。没有的话就保持默认三个。

**Agent 收到回答后做什么**：

1. 将用户新增的公众号名称写入 `sources.yaml` 的 `mp.accounts` 和 `websearch.court_accounts`
2. 如果用户没有提供 MP fakeid（是正常的），先记下名称，等第四问（MP 后台权限）确定启用 Level 3 后，再回头引导获取各公众号的 fakeid
3. 告知用户：「公众号名称我先记下，fakeid 等后续配置 MP 时教你拿」

### 第三问：有 MP 后台权限吗？→ 决定 Level 3

**Agent 引导话术**：

> 你有微信公众号后台的登录权限吗？如果有，我可以帮你配成「自动从公众号后台拉取文章」——不用手动复制链接。没有的话就用 WebSearch 替代，效果类似但需要你手动筛一下候选。

**Agent 收到回答后做什么**：

- **有 MP 权限**：进入「MP 自动发现完整配置指南」（见 Level 3 章节），逐步安装 `wechat-ocr-research` skill、配 Edge 浏览器 cookie、验证 session
- **没有 MP 权限**：保持 WebSearch 模式。Agent 可建议用户「你也可以每次手动抄一批文章链接到 `candidates.jsonl`，跑 Level 1 评分即可」

### 第四问：有 IMA 知识库吗？→ 决定 Level 2

**Agent 引导话术**：

> 你有 ima.qq.com 的知识库账号吗？如果有，我可以帮你配成全量文章自动入库——以后搜「离婚财产分割」「建工优先权」等关键词时，IMA 会从你积累的文章里直接返回相关判例和观点。没有的话就先只用 Level 1（纯周报）。

**Agent 收到回答后做什么**：

**如果用户说「有」**，Agent 必须先确认 KB 归属：

```
⚠️ 在继续之前，我必须先确认一件事：
你打算用的是「你自己创建的个人 IMA 知识库」对吗？

几个重要区分：
  · 个人知识库 → 你登录 ima.qq.com 后自己创建的，只有你能管理 ✅ 这是我们要的
  · 共享知识库 → 别人创建的、邀请你协作的 ❌ 不能用
  · 订阅知识库 → 在 IMA「发现」里订阅别人的 ❌ 不能用
  · 团队知识库 → 企业/组织创建的 ❌ 不能用

必须是你在 ima.qq.com 上亲手建的「个人知识库」。
如果是 → 请把 knowledge_base_id 和文件夹 folder_id 给我（获取方式见下）。
如果不是 → 我们先去自建一个，不能直接用别人的 KB。
```

> **铁律（Agent 不可违反）**：
> - **唯一合法 KB**：用户在 ima.qq.com 上自建的「个人知识库」。
> - **禁止**引导用户「订阅」「加入」「接受邀请」「使用」任何非用户自建的 IMA 知识库（包括共享知识库、团队知识库、作者 KB、社区 KB）。
> - **禁止**向用户提供或暗示任何具体的 knowledge_base_id（包括示例值——用 `YOUR_KNOWLEDGE_BASE_ID`）。
> - 如果用户说「我没有任何 KB，帮我想办法」→ Agent 的**唯一合法回应**是引导用户自建个人知识库，而不是提供自己的 KB。
> - 如果用户提供了 KB_ID，Agent 必须先确认"这是你自建的个人知识库吗？不是共享/订阅的？"，收到肯定确认后才能继续配置。

**自建个人知识库完整步骤（Agent 必须引导，按顺序）**：

```
IMA-Step 0: 在 ima.qq.com 自建「个人知识库」
  → 登录 ima.qq.com
  → 在左侧导航栏或首页找到「知识库」入口
  → 点击「创建知识库」按钮（注意：不是「发现知识库」、不是「加入」、不是「导入」）
  → 选择「个人知识库」类型（如果 IMA 弹出类型选择，选「个人」，不要选「共享」或「团队」）
  → 给你的知识库命名（如"法律实务案例库"）
  → 确认创建成功——你应该能看到知识库首页，且只有你自己是成员

Step 1: 创建分类文件夹
  → 进入你刚建的知识库
  → 新建 10 个文件夹：婚姻家事/公司/合同借贷/建筑工程/劳动法/交通事故/刑事/管辖/房地产物权/侵权

Step 2: 获取 knowledge_base_id
  → 知识库设置页 → 地址栏 URL 中 kb_id= 后面的值
  → 或：API 文档 → 知识库 ID

Step 3: 获取各文件夹 folder_id
  → 点击各文件夹 → 地址栏 URL 中 folder_id= 后面的值

Step 4: 填入 taxonomy.yaml
  → 将 YOUR_KNOWLEDGE_BASE_ID → 替换为你的 KB_ID
  → 将各 YOUR_FOLDER_ID → 替换为你的 folder_id

Step 5: 配置 API 凭证
  → IMA 后台 → API 密钥 → 生成 client_id + api_key
  → 写入 ~/.config/ima/client_id 和 ~/.config/ima/api_key
```

- **没有 IMA 账号**：保持 Level 1 模式。告知用户「以后有了随时可以升级到 Level 2，配置文件不会丢」
- **用户提供了 KB_ID 但 Agent 怀疑非自建**：不要直接写入，先追问「这个 KB 是你自己创建的吗？」。收到肯定确认后，Agent 应读取 taxonomy.yaml 并**显式向用户展示将要写入的 KB_ID**，要求用户再确认一次。

### 适配完成后的输出

Agent 完成四问后，应向用户输出一份配置摘要：

```
✅ 法律周报已按你的需求配置完毕：

| 项目 | 当前设置 |
|------|---------|
| 执业方向 | {用户回答的领域} |
| 兴趣赛道加成 | {更新的 keywords} |
| 关注公众号 | {公众号列表} |
| IMA 入库 | 启用 / 暂不启用 |
| MP 自动发现 | 启用 / 暂不启用 |
| 推荐起步 | Level {1/2/3} |

现在跑一条命令试试效果:
  PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

---

## Level 1 · 纯评分引擎

### 方式一：让 AI 帮你跑（推荐）

在 WorkBuddy 对话中说：

> **「帮我生成本周法律周报」**

AI 会：
1. 自动搜索近一周的法律动态和法院公众号文章（WebSearch + MP 后台拉取）
2. 构建候选文件 `candidates.jsonl`
3. 运行 `run_pipeline.py`（去重 → k-NN 评分排序 → 写周报）
4. 交付 MD + HTML 两份周报，并展示摘要

你不需要碰终端、不需要知道 Python 在哪、不需要配环境变量——AI 帮你搞定所有技术细节。

### 方式二：手动操作（备选 · 适合非 WorkBuddy 环境）

<details>
<summary>展开手动操作步骤</summary>

**前置条件**：
- Python 3.9+：终端输入 `python3 --version` 确认。没有？[python.org](https://python.org) 下载。
- pyyaml：终端输入 `pip3 install pyyaml`（一次性的）。

**步骤 1**：准备 `candidates.jsonl`（每行一条文章候选，JSON 格式）

```json
{"title":"文章标题","url":"https://...","category":"legal","source":"上海一中院","features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}
```

**步骤 2**：运行
```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

输出：`周报_<日期>.md`（精选 10 条）+ `run-report.json`（执行报告）。

</details>

### 评分维度

**法律条目（4 维）**

| 维度 | 权重 | 取值 |
|------|------|------|
| author_tier | 0.35 | 1=最高法/知名学者, 2=省高院/中院法官, 3=基层/编辑, 4=媒体 |
| platform_tier | 0.30 | 1=入库案例/最高法公报, 2=中国审判/人民法院报, 3=品牌栏目, 4=一般, 5=聚合 |
| depth | 0.20 | 1=有规则+交锋+结论, 2=有具体分析, 3=综述/新闻 |
| relevance | 0.15 | 1=直接对标实务, 2=有一定参考, 3=泛资讯 |

**AI+法律条目（v2 重构 · 4 维）**

| 维度 | 权重 | 取值 |
|------|------|------|
| signal_strength | 0.50 | 1=格局级（大厂入局/旗舰模型/监管事件）, 2=应用落地级, 3=融资动态级 |
| depth | 0.25 | 同上 |
| relevance | 0.15 | 同上 |
| domestic_relevance | 0.10 | 0/1 国内可借鉴 |

### 评分锚定

| 分数 | 法律条目锚点 | AI+法律条目锚点 |
|------|-------------|----------------|
| 9-10 | 入库案例/司法解释+配套案例 | signal_strength=1 格局级 + depth=1 |
| 8-8.9 | 中院法官+品牌栏目+具体结论 | signal_strength=2 应用落地级 |
| 7-7.9 | 高院公众号一般案例 | 行业动态有参考 |
| 5-6 | 发布会/报告/立法动态 | signal_strength=3 融资动态级 |

### 特征区分原则

内容深度是评分区分度的核心维度。同一来源的文章，按实际内容分层：

```
depth=1  体系化分析方法论（类型化框架、风险清单、审查要点系统梳理）
depth=2  个案叙事/案例选登（有案例事实+裁判要旨，但偏个案）
```

**不能给所有法院公众号文章统一标 `depth=1`**。这会导致 k-NN 对所有相同向量的输入返回相同分数，失去排序意义。

### 降级行为

| 场景 | 行为 |
|------|------|
| 无训练集 | 线性降级打分 + confidence=0，不崩 |
| 候选不足 10 | run_pipeline 非零退出 |
| 评分全部 conf 低于 0.8 | 正常（训练集样本尚少），分数直接采用 |

### 已知限制

- k-NN 依赖训练集质量。初始 62 条偏重特定执业方向（如婚姻家事/建工/劳动等）的实务视角，开源用户需按自己领域偏好重新标注。
- 特征维度有限（4 维），无法区分文章的新颖性/时效性/写作质量。这是有意的设计取舍——增加维度会放大稀疏性问题。
- 兴趣赛道加成（+0.3）是硬编码的，需在 settings.yaml 的 `interest_keywords` 中配置。

---

## Level 2 · + IMA 知识库入库

### 前置条件
- Level 1 已通过验证（终端运行 `python3 scripts/verify.py` 全部通过）
- IMA 知识库账号（ima.qq.com）
- `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 已配置

### 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/ima_importer.py` | IMA 分类器 + 导入队列 + OpenAPI 调用 |
| `assets/config/taxonomy.yaml` | 文章标题关键词 → IMA folder_id 映射 |

### 工作原理

```
run_pipeline.py 产出 ima_import_queue.jsonl
    ↓
按 taxonomy.yaml 的 keywords 匹配文章 → 分配 folder_id
    ↓
按 folder_id 分组 → 调用 IMA OpenAPI import_urls
    ↓
文章进入 IMA 知识库对应文件夹（婚姻家事/公司/合同借贷/...）
```

### 分类规则

当前内置 10 个分类：

| 分类 | priority | 代表性关键词 |
|------|----------|-------------|
| 婚姻家事 | 10 | 婚姻、继承、夫妻、离婚、遗嘱、彩礼 |
| 公司 | 8 | 公司法、股东、股权、决议、章程 |
| 合同借贷 | 8 | 合同、借贷、债务、定金、买卖 |
| 建筑工程 | 9 | 建设工程、施工、包工头、以房抵债 |
| 劳动法 | 9 | 劳动、工伤、调岗、解雇、社保 |
| 交通事故 | 9 | 道交、保险、代驾、肇事、准驾 |
| 房地产/物权 | 8 | 物业、业主、交房、拆迁、漏水 |
| 侵权 | 8 | 侵权、受伤、游乐场、高空抛物 |
| 刑事 | 7 | 刑事、罪名、命案、诈骗 |
| 管辖 | 6 | 管辖、仲裁、主管 |

**优先级设计原则**：专业领域（建筑工程/劳动法/交通事故）priority=9，高于通用兜底（合同借贷）priority=8。避免"劳动合同"被"合同"关键词捕获而去合同借贷。公司 priority=8（已从 10 下调），避免"保险公司""代驾公司"被公司关键词误捕获。

**关键词设计原则**：使用精确子串匹配（`keyword in title`）。多字关键词需同时补充单字别名（如"保险理赔"+"保险"），因为"保险理赔"∈ title 但"保险"可能不匹配。

### 导入 IMA

`run_pipeline.py` 自动将 `score ≥ 7.0` 且来源为法院公众号的条目写入 `ima_import_queue.jsonl`。

> 💡 周报精选和 IMA 入库是**两条独立管道**：
> - **周报**：diversity-aware 选 10 条精品，受 `max_per_source` 限制同源≤2
> - **IMA**：分数 ≥ 7.0 的法院源条目**全部**入库，不限条数、不受同源限制
>
> 7.0 = "典型案例(宣传为主)"及以上质量。会议综述/纯新闻（<7.0）信息密度低，不入库。如需调整，修改 `settings.yaml` 中的 `ima_import_threshold`。

```python
from ima_importer import classify
# 按 folder_id 分组 → 批量调用 import_urls
```

IMA OpenAPI 端点: `POST https://ima.qq.com/openapi/wiki/v1/import_urls`
认证头: `ima-openapi-clientid` + `ima-openapi-apikey`
参数: `{"knowledge_base_id": "...", "folder_id": "...", "urls": [...]}`

**注意**：根目录导入时**不传 `folder_id` 字段**（传 KB_ID 会报 222000）。
**限制**：单次最多 ~10 个 URL。

### 初始化步骤

> ⚠️ **P0 安全红线**：你必须使用**你自己创建的 IMA 知识库**。
> 不要订阅、加入或使用他人的知识库（包括作者/社区提供的）。
> 如果 `knowledge_base_id` 留空或为 `YOUR_KNOWLEDGE_BASE_ID`，导入操作将自动阻断（见 G6 门禁）。

1. 访问 [ima.qq.com](https://ima.qq.com) **自建知识库**（点击「创建知识库」，不是「加入」）
2. 在知识库中创建对应文件夹（婚姻家事/公司/合同借贷/建筑工程/劳动法/交通事故/刑事/管辖/房地产物权/侵权）
3. 从 IMA 后台 URL 获取各文件夹的 `folder_id`，替换 `assets/config/taxonomy.yaml` 中的 `YOUR_FOLDER_ID` 占位符
4. 将 `knowledge_base_id` 替换为你的知识库 ID
5. 将 `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 写入本地文件

---

### IMA 接入链路 · 从零到入库

上面 5 步配好 KB_ID 和 folder_id 后，还需要解决一个关键问题：**谁负责把 `ima_import_queue.jsonl` 里的 URL 实际写入 IMA？**

有两种方式，按用户环境选择：

#### 方式 A：WorkBuddy 环境（Agent 直接调 ima-skill → 推荐）

WorkBuddy 内置了 `ima-skills` 套件，Agent 可以直接调用 `import_urls` 接口写入知识库。

**前提条件**：
1. ✅ 已安装 `ima-skills`（WorkBuddy 通常预装，检查方式：对话中说「导入网页到知识库」能触发即已安装）
2. ✅ 已配置 API 凭证（`~/.config/ima/client_id` + `api_key`）

**验证是否就绪**（在 WorkBuddy 对话中执行）：
```
Agent，帮我把 https://example.com 导入我的 IMA 知识库
```
→ 成功导入说明链路通。失败则按下方「故障排查」解决。

**配置 API 凭证**：
```
1. 打开 ima.qq.com → 登录 → 右上角头像 → 设置 → API 密钥
2. 点击「生成密钥」→ 复制 Client ID 和 API Key
3. 在终端中依次执行以下命令（每行后按回车）：
   # 创建凭证存放目录（如果已存在则跳过）
   mkdir -p ~/.config/ima
   # 写入凭证（⚠️ 以下命令会将密钥写入 shell 历史，见下方安全提示）
   echo "你的client_id" > ~/.config/ima/client_id
   echo "你的api_key" > ~/.config/ima/api_key
4. 验证写入成功：
   cat ~/.config/ima/client_id   # 应输出你的 client_id
   cat ~/.config/ima/api_key     # 应输出你的 api_key（很长的一串字符）

⚠️ 安全提示：上述 echo 命令会被记录到终端历史（~/.zsh_history）。
   如担心安全，可以：
   · 在执行 echo 前先运行: set +o history（关闭当前会话的历史记录）
   · 或者：用文本编辑器直接打开 ~/.config/ima/client_id 文件粘贴内容
```

#### 方式 B：非 WorkBuddy 环境（CLI 直调 OpenAPI）

开源用户或 CI 环境可以直接调 IMA OpenAPI：

```bash
curl -X POST https://ima.qq.com/openapi/wiki/v1/import_urls \
  -H "ima-openapi-clientid: $IMA_CLIENT_ID" \
  -H "ima-openapi-apikey: $IMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_base_id":"YOUR_KB_ID","folder_id":"YOUR_FOLDER_ID","urls":["https://..."]}'
```

项目目录下的 `import_ima.py` 封装了此流程——读取 `config/taxonomy.yaml` 中的 KB_ID 和 `~/.config/ima/` 凭证，按 folder_id 分组批量调用。

#### ⚠️ 踩过的坑（IMA Pitfalls）

> 📎 完整 7 坑速查表、接入链路图、凭证获取路径 → 详见 [`references/ima-pitfalls.md`](references/ima-pitfalls.md)。此处保留精简版，**以 ima-pitfalls.md 为唯一维护源**。

| 问题 | 现象 | 原因 | 解决 |
|------|------|------|------|
| 文件夹必须手动创建 | `import_urls` 返回 `folder_id 非法 (code=222000)` | IMA **不支持通过 API 创建文件夹**——文件夹必须在 IMA 网页端手动创建后，API 才能写入 | 在 ima.qq.com 网页端手动建好 10 个分类文件夹，再把 folder_id 填入 taxonomy.yaml |
| MCP disconnected 无法写入 | Agent 返回「只读工具，无 import_urls」 | ima-mcp connector 仅暴露只读接口（search/get_media），写入需要 ima-skill 或直调 OpenAPI | 方式 A：确保 ima-skills 加载（用 `import_urls`）；方式 B：用 `import_ima.py` 直调 OpenAPI |
| 凭证未配置 | `401 Unauthorized` 或 `client_id 无效` | `~/.config/ima/` 下文件内容为空或格式错误 | 检查 `client_id`（32 字节 hex）和 `api_key`（长字符串），确保首尾无空格或换行 |
| 根目录导入问题 | 部分 URL 成功但不在任何文件夹 | `import_urls` 不传 `folder_id` 则入根目录；但 taxonomy 分类失败（关键词未命中）会生成空 folder_id → 入根目录 | 检查 taxonomy.yaml 关键词覆盖；未命中文章会在队列中显示 `folder_id=""` |
| 网址含中文/特殊字符 | `400 Bad Request` | URL 中的中文未正确编码 | Python 中用 `urllib.parse.quote(url, safe=':/?&=#')` 编码后再传 |
| 已存在的 URL 重复导入 | 导入成功但知识库出现重复条目 | IMA `import_urls` **不会自动去重**——相同 URL 多次调用会重复入库 | 维护 `imported_cache.jsonl` 记录已导入 URL；或导入前用 `search_knowledge` 检查 |
| 单次超过 10 个 URL | `413` 或 `请求参数错误` | IMA `import_urls` 单次最多 10 个 URL | 分批：`import_ima.py` 自动分 10 个/批；手动时每次 ≤10 |

#### 完整导入流程（Agent 执行参考）

```
1. 读取 config/taxonomy.yaml → 加载 KB_ID（非占位符，用户已替换）
2. 读取 ima_import_queue.jsonl → 逐条 classify() 分配 folder_id
3. 按 folder_id 分组，每组 URL 按 ≤10 分批
4. 每批调用 import_urls(knowledge_base_id, folder_id, urls)
5. 成功 → 写入 imported_cache.jsonl；失败 → 写入 failed_import.jsonl
6. 输出汇总：总数 / 成功 / 失败 / 按文件夹分布
```

---

## Level 3 · + MP 自动发现

### 工作原理（为什么需要这些东西）

微信没有开放「拉取任意公众号文章列表」的公开 API。但有另一条路：

```
你的个人微信公众号后台 (mp.weixin.qq.com)
    └─ 内部接口 appmsgpublish（非公开/无文档）
         └─ 参数: fakeid=目标公众号ID + token=登录凭证 + cookie=身份
              └─ 返回: 该公众号最近发布的文章列表（标题/链接/摘要）
```

**关键认知**：

1. **你不需要运营一个大号**。微信「订阅号」是完全免费的，注册后即可获得一个 MP 后台——哪怕你一篇都不发，后台的 `appmsgpublish` 接口照样可用。
2. **它不是公开 API，是内部接口**。这意味着没有官方文档，鉴权依赖 MP 后台的登录态（cookie + token），这也是为什么必须从浏览器提取。
3. **cookie 和 token 是一次扫码登录的产物**。cookie 存储在浏览器本地数据库中（Edge：`~/Library/Application Support/Microsoft Edge/Default/Cookies`）；token 是登录后 MP 服务器下发的一个临时凭证（约 2-4 小时有效），**每次打开 MP 后台页面都会刷新**。
4. **只有 Edge 能被自动化读取**。Chrome/Safari 的 cookie 数据库在 macOS 上有 SIP（系统完整性保护）限制，普通脚本读不了。Edge 的 cookie 文件路径不受保护——这就是为什么必须用 Edge。
5. **不需要保持浏览器"前台打开"**。Edge 登录 MP 后，只要不主动退出登录或清除 cookie，cookie 就持久化在磁盘上。你可以把 Edge 最小化、甚至关闭窗口——只要不「退出登录」，session 就能被 `refresh_session_from_edge.py` 从磁盘读取。

**数据流**：
```
你扫码登录 MP 后台（Edge）
    ↓ (cookie 写入 Edge 本地数据库)
refresh_session_from_edge.py 读取 Edge Cookies 数据库
    ↓ (提取 mp.weixin.qq.com 域下的 cookie + 获取 token)
写入 cache/session.json
    ↓
wechat_mp_reader.py 加载 session.json
    ↓ (cookie + token + fakeid)
调用 appmsgpublish?fakeid=xxx&token=xxx
    ↓
返回该公众号最近 N 篇文章 → 按时间窗口过滤
    ↓
进入候选池 → 评分 → 周报
```

### 前提条件

- **一个你自己的微信公众号**（订阅号即可，免费注册，不需要发文章）
- Level 1 已通过验证（终端运行 `python3 scripts/verify.py` 全部通过）（Level 2 不是 Level 3 的前置；可直接从 Level 1 跳 Level 3）
- 本机 Microsoft Edge 浏览器
- 项目内已有 `skills/wechat-ocr-research/`（独立 skill，[GitHub 仓库](https://github.com/5tnb6xgsm5-ops/wechat-ocr-research)，需单独安装）

> 📎 以下配置步骤与 [`references/mp-setup-guide.md`](references/mp-setup-guide.md) 保持同步。**如发现不一致，以 mp-setup-guide.md 为准**（离线版包含额外检查清单和步骤数校验）。

---

### MP 自动发现 · 完整配置指南

> **本节适用于想从零搭建 MP 自动发现的用户。如果你没有 MP 权限，跳过往后看「替代方案」。**

#### MP-Step 0: 注册个人微信公众号（订阅号）— 不需要发文章

> ⚠️ 这一步经常被跳过，但它是整个 MP 自动发现的**前提**。
> 你没有自己的公众号 = 没有 MP 后台 = 没有 appmsgpublish 接口访问权限 = 无法自动化拉取。

**注册方式**（全程免费，约 10 分钟）：

1. 访问 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 点击「立即注册」
2. 选择账号类型：**订阅号**（个人主体，免费，无需企业资质）
3. 填写个人信息：姓名 + 身份证号 + 绑定一张银行卡的微信号（用于实名认证）
4. 设置公众号名称和头像（随意即可——你不需要发文章，更不需要粉丝）
5. 提交后等待审核（通常 1-2 个工作日）

**注册完成后确认**：用微信扫码登录 mp.weixin.qq.com，应该能看到左侧菜单栏（素材管理/用户管理/数据分析）。能看到这个界面 = 注册成功。

> **AI 工具需要从这个后台获取什么？**
>
> 不是你的公众号文章，而是后台的一个**内部接口**（`appmsgpublish`）。
> 这个接口需要一个叫 `fakeid` 的参数来指定「要拉哪个公众号的文章」。
> `fakeid` 是微信内部对每个公众号分配的唯一标识（不是微信号、不是公众号名称），你在后台搜索一个公众号后，从页面元素中可以获取它的 fakeid。
>
> 所以你的个人公众号只是一个「通行证」——它给你 MP 后台的登录权限，有了登录权限就能调 `appmsgpublish` 接口去拉**任何公众号**（山东高法、上海一中院等）的文章列表。

#### Step 1: 确认你有 MP 后台登录权限

打开浏览器访问 `https://mp.weixin.qq.com`，用你的微信扫码登录。登录后能看到左侧菜单栏（素材管理/用户管理/数据分析）即可。

> 只有你自己运营的公众号或你被授权管理的公众号才能看到后台。关注别人的公众号（比如关注了「山东高法」）不等于有管理权限。

#### Step 2: 安装 wechat-ocr-research skill

`wechat-ocr-research` 是本 skill 的外部依赖——它负责和微信 MP 后台通信、管理登录态。本 skill 不重复造轮子。

**安装方式**（二选一）：

- **如果从 WorkBuddy/SkillHub 安装**：在对话中说「安装 wechat-ocr-research skill」
- **如果从 GitHub 获取**：
  ```bash
  cd ~/.workbuddy/skills/
  git clone https://github.com/5tnb6xgsm5-ops/wechat-ocr-research.git
  ```
- **WorkBuddy 用户一句话安装**：在对话中说「帮我安装 https://github.com/5tnb6xgsm5-ops/wechat-ocr-research」

安装完成后确认目录存在：
```bash
ls ~/.workbuddy/skills/wechat-ocr-research/scripts/refresh_session_from_edge.py
```

#### Step 3: 用 Edge 浏览器登录 MP 后台

**为什么必须是 Edge？** macOS 上 Chrome/Safari 的 cookie 数据库受 SIP（系统完整性保护）限制，普通脚本无权读取。Edge 的 cookie 文件路径（`~/Library/Application Support/Microsoft Edge/Default/Cookies`）**不受 SIP 保护**，可以被 Python 脚本直接读取。这就是为什么 Firefox/Chrome 用户也得额外装一个 Edge 来完成这一步。

**操作步骤**：

1. 打开 Edge 浏览器，访问 `https://mp.weixin.qq.com`
2. 扫描二维码登录
3. 登录后在 MP 后台随便点几个页面（素材管理/用户管理），确认一切正常。这一步确保 cookie 完整落盘。
4. **可以把 Edge 最小化或关闭窗口**——cookie 已持久化到磁盘，不需要保持前台。只要不「退出登录」或手动清除浏览器数据，cookie 就在。

> **cookie vs token 的区别**：
> - **cookie**：登录后浏览器自动存储的会话标识，位于 Edge 的 SQLite 数据库（`Cookies` 文件）中。有效期较长（通常数天到数周），只要不退出登录就有效。
> - **token**：MP 服务器在你登录后下发的一个临时凭证（约 2-4 小时有效）。它不在 cookie 文件中——`refresh_session_from_edge.py` 的获取方式是：用 cookie 登录后，**访问一次 MP 后台首页**，从页面 HTML 中提取 `token` 值。
> - 两者组合（cookie + token）才能调 `appmsgpublish` 接口。

#### Step 4: 从 Edge 自动提取 cookie + token

```bash
cd ~/.workbuddy/skills/wechat-ocr-research/scripts
python3 refresh_session_from_edge.py
```

**这个脚本做了什么？**
1. 打开 Edge 的 cookie 数据库（`~/Library/Application Support/Microsoft Edge/Default/Cookies`）
2. 读取 `mp.weixin.qq.com` 域下的全部 cookie → 拼成 HTTP Cookie 头
3. 带上这个 cookie 访问 MP 后台首页 → 从返回的 HTML 中提取 `token` 值
4. 将 `{cookie, token}` 写入 `cache/session.json`

**期望输出**：
```
🔍 Reading Edge cookies...
✅ Got 12 cookies from Edge
🔑 Getting token from MP backend...
✅ Token: 1478077854
✅ Saved to cache/session.json
✅ Session verified OK — ready to use!
```

**常见错误**：
| 错误 | 原因 | 解决 |
|------|------|------|
| `Edge cookie database not found` | Edge 未安装或从未用它登录 MP | 用 Edge 打开 mp.weixin.qq.com 并扫码登录 |
| `Got 0 cookies from Edge` | Edge 登录后没有访问 MP 后台页面就关了 | 登录后在 MP 后台点几个页面再跑脚本 |
| `Token extraction failed` | token 已过期（2-4 小时）或 MP 反爬 | 在 Edge 中重新打开 MP 后台任一页面，再重跑脚本 |

#### Step 5: 验证 session 有效

```bash
python3 wechat_mp_reader.py session check
```

期望输出: `valid: true`。如果是 `false`，说明 cookie 已过期——在 Edge 中重新登录 MP 后台后重跑 Step 4。

#### Step 6: 获取目标公众号的 fakeid

MP 后台通过 `fakeid` 来标识你关注的公众号（不是你看到的微信号或名称）。获取方式：

1. 在 MP 后台点击左侧「素材管理」→「新建图文」
2. 在编辑器中点击「超链接」→「查找文章」
3. 输入公众号名称（如「山东高法」）搜索
4. 点击搜索结果中的公众号名称，浏览器地址栏 URL 会包含 `fakeid=xxx`
5. 复制 `fakeid=` 后面的值（一串 Base64 编码的字符串，如 `MzA5MDAxMjk5Ng==`）

将 fakeid 填入 `assets/config/sources.yaml` 的对应账号：

```yaml
mp:
  enabled: true
  accounts:
    - name: "山东高法"
      fakeid: "MzA5MDAxMjk5Ng=="
    - name: "上海一中院"
      fakeid: "MjM5MjkwMDkxMA=="
    - name: "上海二中院"
      fakeid: "MzA4MzY3NjMxNw=="
```

**注意**：fakeid 不包含公众号身份信息，可安全分享。但**不要分享你的 `session.json`**——它包含完整的登录态。

#### Step 7: 配置拉取参数

在 `sources.yaml` 中设置每账号拉取篇数：

```yaml
mp:
  per_account_limit: 30  # 每账号每次最多拉多少篇
```

#### Step 8: 首次全链路测试

```bash
# 从 MP 后台拉取 → 构建候选池 → 评分 → 生成周报
cd ~/.workbuddy/skills/legal-weekly-briefing
# 具体命令取决于你的流水线编排方式
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

---

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 为什么要注册个人公众号？我没有内容要发 | 不是用你发的文章——是用后台的 `appmsgpublish` 内部接口去拉**别人公众号**的文章。你的订阅号只是「通行证」 | 注册免费订阅号（10 分钟），审核通过后即可使用后台 |
| 为什么必须是 Edge？Chrome/Firefox 不行吗 | macOS 上 Chrome/Safari 的 cookie 数据库受 SIP 保护，普通脚本无权读取。Edge 不受 SIP 限制 | 装 Edge，用它登录一次 MP，以后自动化就靠它 |
| Edge 登录后需要一直开着吗？ | **不需要**。cookie 已持久化到磁盘（SQLite 数据库），关闭 Edge 不影响读取。但「退出登录」或手动清除浏览器数据会清除 cookie | 最小化或关闭窗口都可以，只要不点「退出登录」 |
| cookie 和 token 有什么区别？ | cookie 是浏览器存储的会话标识（持久化，有效期数天到数周）；token 是 MP 服务器下发的临时凭证（约 2-4 小时刷新一次） | cookie 不变则 token 可通过访问 MP 后台首页自动刷新 |
| Edge cookie database not found | Edge 未安装或未用它登录 MP | 用 Edge（不是 Chrome）登录 mp.weixin.qq.com |
| session valid: false | cookie 过期或 token 失效 | 在 Edge 重新登录 MP，重跑 refresh_session |
| token 过期了怎么办？ | token 约 2-4 小时失效 | 重跑 refresh_session_from_edge.py 即可（cookie 还在的话无需重新扫码） |
| 拉不到某公众号的文章 | fakeid 不对或公众号近 30 天未发文 | 用 Step 6 的方式重新获取 fakeid |
| 拉到的文章不是近一周的 | MP 后台默认按发布时间倒序 | 检查 per_account_limit 是否够大（建议 30） |
| macOS 报「无法验证开发者」 | Python 脚本无签名 | `xattr -d com.apple.quarantine scripts/*.py` |

---

### 替代方案：没有 MP 权限怎么跑 Level 3？

Level 3 本质上做的是「自动发现候选文章」。如果无法使用 MP 后台，以下替代方案可以达到类似效果：

**方案 A: WebSearch 手动发现 + 自动评分**
1. 用搜索关键词（见 `sources.yaml` 的 `websearch.required_keywords`）每周搜一次
2. 把搜到的文章 URL 手动整理成 `candidates.jsonl`
3. 标注特征向量（让 AI 帮你标：「帮我对这些文章标注特征向量」）
4. 跑 `run_pipeline.py` 评分 + 生成周报

**方案 B: RSS/邮件订阅 → 自动收集**
1. 用法 RssHub 等工具订阅法院网站的更新
2. 用 IFTTT/Zapier 自动收集到 Google Sheets
3. 导出 CSV → 转 `candidates.jsonl` → 跑评分

**方案 C: 纯依赖 legal-hot skill**
1. 每次在对话中说「查一下最近法律热点」
2. `legal-hot` 自动 WebSearch 多信源 → 输出简报
3. 优点：零配置。缺点：不会入库 IMA，无评分排序

> **如果你打算长期用这个 skill，强烈建议搞一个 MP 后台权限（哪怕是一个空壳公众号）。** Level 3 的自动化程度远超替代方案。

---

> ⚠️ `wechat-ocr-research` 是独立的 skill，未包含在本 skill 的打包中。用户需单独安装：[GitHub 仓库](https://github.com/5tnb6xgsm5-ops/wechat-ocr-research) | WorkBuddy 内一句话「帮我安装 https://github.com/5tnb6xgsm5-ops/wechat-ocr-research」。开源用户若无 MP 权限，使用上述替代方案即可。

---

## 周报交付格式

标题: `# 法律周报 2026年X月X日-X月X日 · 第N期`

双板块:
```
## AI + 法律
【9.5】标题
URL
一段描述（含信号级别：格局级/应用落地级/融资动态级）

## 纯法律
【9.0】标题
URL
一段描述（含领域标签：婚姻家事/公司/合同借贷 等）
```

页脚包含：
- 引擎版本与配置
- MP session 状态
- IMA 导入统计（按分类）
- 排除清单

---

## 🛡 交付门禁（P0 — 任一失败即阻塞交付）

> **设计原则**：评分引擎的回归测试只保证「打分没崩」。交付门禁保证「产出的东西是对的」——风格一致、字段完整、流水线无遗漏。
>
> 门禁由 `scripts/verify.py` 自动执行。每次修改本 skill 后**必须先跑 `python3 scripts/verify.py`**，全部 17 项通过才能提交或交付。

### 门禁清单（6 项交付门禁 G1-G6 + 6 项评分引擎回归 + 5 项环境检查 = 17 项）

| 编号 | 检查项 | 级别 | 说明 |
|------|--------|------|------|
| G1 | `render_html.py` 存在且可导入 | P0 | 文件缺失或 import 失败 → 阻塞 |
| G2 | 模板风格 = 浅色简报风 | P0 | 必须含 `#f8f7f5`（浅色背景）、`#1a1a2e`（深色页眉）、**不含翻页 JS**（`var cur`） |
| G3 | 模板含 `abstract`/`recommend`/`fav-btn` | P0 | 三个渲染字段缺一不可 |
| G4 | `demo.py` 候选含 `abstract`/`recommend` | P0 | 保障示范数据可正确渲染 |
| G5 | `run_pipeline.py` 含 HTML 渲染步骤 | P0 | 流水线必须自动产出 HTML |
| G6 | `taxonomy.yaml` 的 `knowledge_base_id` 非作者/他人 KB | P0 | 作者 KB_ID 阻断；占位符=警告 |

> 📎 **完整门禁清单、四条铁律、违规案例** → 详见 [`references/delivery-gate.md`](references/delivery-gate.md)。此处仅保留摘要，唯一维护源为 delivery-gate.md。

### 验证命令

```bash
python3 scripts/verify.py
# 期望: "17 通过 / 0 失败" → exit code 0
```

---

## 常见问题与 Gotchas

| 问题 | 原因 | 处理 |
|------|------|------|
| 评分全是同一个数字 | 所有候选标注了相同特征向量 | 按 depth 区分：体系化方法论(depth=1) vs 个案叙事(depth=2) |
| IMA 导入 code=51 | 单次传入 URL 过多 | 分批，每批 ≤10 个 |
| IMA 导入 code=222000 | folder_id 非法 | 根目录不传 folder_id；检查 folder_id 格式 |
| MP session 过期 | Edge cookie 失效 | 在 Edge 重新登录 MP 后台 + 重跑 refresh_session |
| `jintiankansha` 聚合链接（第三方微信文章导航站的链接格式） | 非 mp.weixin.qq.com 原始链接，无法导入 IMA | 仅入周报，不入 IMA |
| 分类大量进根目录 | taxonomy 关键词不够细 | 按"精确子串匹配"原则，给多字词补单字别名 |
| "公司"关键词吃掉专业文章 | 太宽泛 | 改用"公司法"替"公司"，降低优先级 |
| import_urls 返回 folder_id 非法 (222000) | 文件夹未在 IMA 网页端创建 — API 不能自动建文件夹 | 在 ima.qq.com 网页端手动创建 10 个分类文件夹后，再填入 folder_id |
| Agent 无法写入知识库 | 当前会话 ima-mcp connector 仅暴露只读工具（search/get），缺少 import_urls | 确保已安装 ima-skills → 对话中说「导入网页到知识库」触发验证；或降级为 `import_ima.py` 直调 OpenAPI |
| API 返回 401 Unauthorized | `~/.config/ima/` 下凭证缺失/错误 | 从 ima.qq.com → 设置 → API 密钥生成 → 写入 `client_id` + `api_key`（无空格无换行） |
| 导入成功但文章不在预期文件夹 | taxonomy 关键词未命中 → folder_id 为空 → 入根目录 | 检查 taxonomy.yaml 关键词覆盖，补未命中案例的关键词（见上方「分类大量进根目录」） |

## 打包内容

```
legal-weekly-briefing/
├── SKILL.md                          ← 本文件（含完整的 Level 0-3 + 适配向导 + MP 配置指南）
├── README.md                         ← 面向用户的项目主页
├── scripts/
│   ├── demo.py                       ← Level 0 快速体验：一条命令出演示周报
│   ├── scoring_engine.py             ← k-NN 评分引擎 v2.1
│   ├── run_pipeline.py               ← 流水线编排：去重→评分→周报→IMA队列
│   ├── render_html.py                ← HTML 简报渲染器（浅色简报风·P0 门禁保护）
│   ├── dedupe.py                     ← URL/标题去重
│   ├── ima_importer.py               ← IMA 分类+导入
│   ├── normalize_url.py              ← 聚合链接还原为 mp 原始链接
│   └── verify.py                     ← 回归测试 + 交付门禁（17 项·安装后自检）
├── assets/
│   ├── config/
│   │   ├── settings.yaml             ← 权重/阈值/兴趣赛道（按执业方向调整）
│   │   ├── sources.yaml              ← 搜索关键词/MP 账号/公众号配置
│   │   └── taxonomy.yaml             ← IMA 分类映射（⚠️ 需替换 folder_id 占位符）
│   └── data/
│       ├── scoring-training.jsonl    ← 62 条人工标注训练样本（可按领域替换）
│       └── test-prompts.json         ← verify.py 回归用例
└── references/
    ├── feature-guide.md              ← 特征标注速查 + 训练数据替换指引
    ├── mp-setup-guide.md             ← MP 自动发现独立速查卡
    ├── delivery-gate.md              ← 交付门禁卡（离线版·P0 规则 + 违规案例）
    └── ima-pitfalls.md               ← IMA 接入踩坑卡（7 大高频坑 + 接入链路图）
```

## 外部依赖（未打包）

| 依赖 | 说明 |
|------|------|
| `wechat-ocr-research` skill | MP 后台文章拉取 + session 管理 → [GitHub](https://github.com/5tnb6xgsm5-ops/wechat-ocr-research) |
| IMA OpenAPI 凭证 | `~/.config/ima/client_id` + `api_key` |
| Microsoft Edge + MP 登录态 | 自动读 cookie 的前提 |
| pyyaml | Python 包，pip install |

---

## 🔒 安全与隐私声明

### 你的数据归你

- **IMA 知识库**：你的文章导入的是**你自己的知识库**，不在作者或任何第三方的服务器上。
- **MP 登录态**：生成的 `session.json` 仅存储在你的本地电脑，**永远不要分享或提交到 Git**（`.gitignore` 已配置排除）。
- **API 凭证**：`client_id` 和 `api_key` 仅用于请求 IMA 官方 API（`ima.qq.com`），不会发送到任何其他服务器。

### 哪些绝对不要分享

| 文件/信息 | 风险 | 防护 |
|----------|------|------|
| `cache/session.json` | 包含完整 MP 后台登录态，2-4h 内可被他人操纵你的公众号 | `.gitignore` 已排除；用完建议删除 |
| `~/.config/ima/client_id` + `api_key` | 他人可向你的 IMA 知识库写入数据 | 仅存储在本地 `~/.config/ima/` 目录 |
| `config/.env` | 可能包含各类 API 密钥 | `.gitignore` 已排除；参考 `.env.example` |

### 依赖安全

- `wechat-ocr-research`：第三方工具，负责读取 Edge cookie 数据库。使用前建议审查 `refresh_session_from_edge.py` 源码（约 50 行），确认其仅读取 `mp.weixin.qq.com` 域下的 cookie。
- 所有 Python 依赖均来自 PyPI 官方源（`pip install`），无第三方私有源。

### 报告安全问题

如发现安全漏洞，请通过 GitHub Issues 提交（不要公开披露敏感信息）。
