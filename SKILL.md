---
name: legal-weekly-briefing
description: "用户说「生成法律周报」「帮我筛法院公众号文章」「法律简报」「案例入库」时触发。从法院公众号（上海一中院/二中院/山东高法等）文章中用可解释的 k-NN 评分引擎筛出 10 条精品周报，其余实务文章全量入库 IMA 知识库做 RAG。临时法律热点查询走 legal-hot，不要用本 skill。"
author: "吴律"
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

## 自动化配置

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
  └─ Level 2 + wechat-ocr-research skill → MP 后台拉取三账号文章
     适用：有微信公众号后台管理权限的用户
```

---

## ⚡ Level 0 · 5 分钟快速体验

**一条命令，看到产出。**

```bash
cd <skill_dir>
python3 scripts/demo.py
```

输出 `周报_demo_<日期>.md` — 一份包含 AI+法律(3 条) + 纯法律(7 条) 的演示周报。预置数据为 10 条真实法律新闻候选，标注好特征向量。

**这个 Demo 不干什么**：不跑评分引擎、不调 API、不需要任何配置。它只是让你看到——「这个工具最终写出来的东西长什么样」。

你看到 demo 之后，下一步就是用自己的数据替换掉这 10 条示范候选，跑真正的评分引擎（Level 1）。怎么替换？进入下面的适配向导。

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
  3. IMA 知识库 → 决定是否启用 Level 2
  4. MP 后台权限 → 决定是否启用 Level 3

收集完毕后，Agent 自动修改 assets/config/ 下的 YAML 文件。
每改完一个配置，告诉用户改了什么、为什么这么改。
```

### 第一问：执业方向 → 调整 interest_keywords + 分类权重

**Agent 引导话术**：

> 你主要是做哪个方向的？多选也行。（婚姻家事 / 公司 / 合同借贷 / 建筑工程 / 劳动法 / 交通事故 / 刑事 / 知识产权 / 行政法 / 其他）
>
> 如果有特别关注的细分领域（比如「医疗损害」「消费维权」「网络侵权」），也可以直接说，我帮你加到兴趣赛道里。

**Agent 收到回答后做什么**：

1. 将用户的执业方向关键词写入 `settings.yaml` 的 `interest_keywords`（替换当前永康视角的关键词）
2. 将用户的首选方向在 `taxonomy.yaml` 中 priority 调至最高（10），次要方向调至 9
3. 告知用户：「兴趣赛道加成 = +0.3 分，你的核心领域文章会天然排在周报前面」

**示范**（永康执业律师当前配置）：
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
2. 如果用户没有提供 MP fakeid（是正常的），先记下名称，等第三问确定 Level 3 启用后再引导获取 fakeid
3. 告知用户：「公众号名称我先记下，fakeid 等后续配置 MP 时教你拿」

### 第三问：有 IMA 知识库吗？→ 决定 Level 2

**Agent 引导话术**：

> 你有 ima.qq.com 的知识库账号吗？如果有，我可以帮你配成全量文章自动入库——以后搜「离婚财产分割」「建工优先权」等关键词时，IMA 会从你积累的文章里直接返回相关判例和观点。没有的话就先只用 Level 1（纯周报）。

**Agent 收到回答后做什么**：

- **有 IMA 账号**：引导用户在 IMA 网页版创建 10 个分类文件夹 → 获取 folder_id → 填入 `taxonomy.yaml` → 获取 `knowledge_base_id` → 获取 API 凭证 → 写入 `~/.config/ima/`
- **没有 IMA 账号**：保持 Level 1 模式。告知用户「以后有了随时可以升级到 Level 2，配置文件不会丢」

### 第四问：有微信公众号后台管理权限吗？→ 决定 Level 3

**Agent 引导话术**：

> 你有微信公众号后台的登录权限吗？如果有，我可以帮你配成「自动从公众号后台拉取文章」——不用手动复制链接。没有的话就用 WebSearch 替代，效果类似但需要你手动筛一下候选。

**Agent 收到回答后做什么**：

- **有 MP 权限**：进入「MP 自动发现完整配置指南」（见 Level 3 章节），逐步安装 `wechat-ocr-research` skill、配 Edge 浏览器 cookie、验证 session
- **没有 MP 权限**：保持 WebSearch 模式。Agent 可建议用户「你也可以每次手动抄一批文章链接到 `candidates.jsonl`，跑 Level 1 评分即可」

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

### 前置条件
- Python 3.9+
- `pip install pyyaml`（仅配置驱动时需要；缺失时回退默认值）

### 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/demo.py` | Level 0 快速体验：一条命令出演示周报 |
| `scripts/scoring_engine.py` | k-NN 加权近邻评分引擎 v2.1 |
| `scripts/run_pipeline.py` | 流水线编排：去重→评分→周报→IMA队列 |
| `scripts/dedupe.py` | URL 去重模块 |
| `scripts/verify.py` | 回归测试（安装后自检） |
| `assets/config/settings.yaml` | 权重/阈值/条数/兴趣赛道 |
| `assets/data/scoring-training.jsonl` | 62 条人工标注训练数据 |

### 使用方式

**步骤 1**：构建候选文件 `candidates.jsonl`（每行一条）
```
{"title":"文章标题","url":"https://...","category":"legal","source":"上海一中院","features":{"author_tier":2,"platform_tier":3,"depth":1,"relevance":1}}
```

- `category`: `legal`（纯法律）或 `ai-legal`（AI+法律交叉）
- `source`: 可选，用于同源多样性限制（如 `山东高法`/`上海一中院`/`上海二中院`）
- `features` 字段见 `references/feature-guide.md` 中的特征标注速查

**步骤 2**：运行流水线
```bash
cd <skill_dir>
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

**步骤 3**：自检（可选但推荐）
```bash
PYTHONPATH=scripts python3 scripts/verify.py
```
全部通过说明评分引擎路径/训练集加载正常。

输出：
- `周报_2026-07-10.md` — 精选周报（10 条，AI+法律 3 + 法律 7）
- `run-report.json` — 执行报告
- `ima_import_queue.jsonl` — IMA 待导入队列（Level 2 使用）

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

- k-NN 依赖训练集质量。初始 62 条偏重"永康市执业律师实务"视角，开源用户需按自己领域偏好重新标注。
- 特征维度有限（4 维），无法区分文章的新颖性/时效性/写作质量。这是有意的设计取舍——增加维度会放大稀疏性问题。
- 兴趣赛道加成（+0.3）是硬编码的，需在 settings.yaml 的 `interest_keywords` 中配置。

---

## Level 2 · + IMA 知识库入库

### 前置条件
- Level 1 已配置
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

`run_pipeline.py` 自动将 `score ≥ 8.0` 且来源为法院公众号的条目写入 `ima_import_queue.jsonl`。之后消费队列：

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

1. 在 IMA 知识库中创建对应文件夹（婚姻家事/公司/合同借贷/建筑工程/劳动法/交通事故/刑事/管辖/房地产物权/侵权）
2. 从 IMA 后台 URL 获取各文件夹的 `folder_id`，替换 `assets/config/taxonomy.yaml` 中的 `YOUR_FOLDER_ID` 占位符
3. 将 `knowledge_base_id` 替换为你的知识库 ID
4. 将 `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 写入本地文件（脚本不读此文件，由外层 IMA 客户端使用）

---

## Level 3 · + MP 自动发现

### 前提条件
- Level 1 已配置（Level 2 不是 Level 3 的前置；可直接从 Level 1 跳 Level 3）
- 微信公众号后台管理权限（mp.weixin.qq.com）
- 本机 Microsoft Edge 浏览器
- 项目内已有 `skills/wechat-ocr-research/`（独立 skill，需单独安装）

### 工作原理

```
Edge 登录 MP 后台 → refresh_session_from_edge.py → session.json
    ↓
wechat_mp_reader.py → list_articles_via_mp_backend()
    ↓
多账号各拉 30 篇 → 合并去重 → 进入候选池 → Level 1 评分
```

---

### MP 自动发现 · 完整配置指南

> **本节适用于想从零搭建 MP 自动发现的用户。如果你没有 MP 权限，跳过往后看「替代方案」。**

#### Step 1: 确认你有 MP 后台登录权限

打开浏览器访问 `https://mp.weixin.qq.com`，用你的微信扫码登录。登录后能看到左侧菜单栏（素材管理/用户管理/数据分析）即可。**你需要的是「公众号运营者」或「管理员」身份**，不是普通关注者。

> 只有你自己运营的公众号或你被授权管理的公众号才能看到后台。关注别人的公众号（比如关注了「山东高法」）不等于有管理权限。如果你没有自己的公众号，跳到本节末尾的「替代方案」。

#### Step 2: 安装 wechat-ocr-research skill

`wechat-ocr-research` 是本 skill 的外部依赖——它负责和微信 MP 后台通信、管理登录态。本 skill 不重复造轮子。

**安装方式**（二选一）：

- **如果从 WorkBuddy/SkillHub 安装**：在对话中说「安装 wechat-ocr-research skill」
- **如果从 GitHub 获取**：
  ```bash
  cd ~/.workbuddy/skills/
  git clone https://github.com/your-org/wechat-ocr-research.git
  ```

安装完成后确认目录存在：
```bash
ls ~/.workbuddy/skills/wechat-ocr-research/scripts/refresh_session_from_edge.py
```

#### Step 3: 用 Edge 浏览器登录 MP 后台

**必须是 Microsoft Edge 浏览器**——refresh_session 脚本通过 Edge 的 cookie 数据库读取登录态，不支持 Chrome/Firefox/Safari。

1. 打开 Edge，访问 `https://mp.weixin.qq.com`
2. 扫描二维码登录
3. 登录后在 MP 后台随便点几个页面，确认一切正常
4. **不要关闭 Edge**——Cookie 必须在浏览器活跃状态才能被脚本读取

#### Step 4: 从 Edge 恢复 MP session

```bash
cd ~/.workbuddy/skills/wechat-ocr-research/scripts
python3 refresh_session_from_edge.py
```

成功输出应包含 `token` 和 `cookie` 字段。如果报错 `Edge cookie database not found`，说明：
- Edge 浏览器未安装，或
- Edge 从未登录过 MP 后台

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
| Edge cookie database not found | Edge 未安装或未用它登录 MP | 用 Edge（不是 Chrome）登录 mp.weixin.qq.com |
| session valid: false | Cookie 已过期（通常 2-4 小时后失效） | 在 Edge 重新登录 MP，重跑 refresh_session |
| 拉不到某公众号的文章 | fakeid 不对或公众号近 30 天未发文 | 用 Step 6 的方式重新获取 fakeid |
| 拉到的文章不是近一周的 | MP 后台默认按发布时间倒序，翻页即可 | 检查 per_account_limit 是否够大 |
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

> ⚠️ `wechat-ocr-research` 是独立的 skill，未包含在本 skill 的打包中。用户需单独安装。开源用户若无 MP 权限，使用上述替代方案即可。

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

## 常见问题与 Gotchas

| 问题 | 原因 | 处理 |
|------|------|------|
| 评分全是同一个数字 | 所有候选标注了相同特征向量 | 按 depth 区分：体系化方法论(depth=1) vs 个案叙事(depth=2) |
| IMA 导入 code=51 | 单次传入 URL 过多 | 分批，每批 ≤10 个 |
| IMA 导入 code=222000 | folder_id 非法 | 根目录不传 folder_id；检查 folder_id 格式 |
| MP session 过期 | Edge cookie 失效 | 在 Edge 重新登录 MP 后台 + 重跑 refresh_session |
| jintiankansha 聚合链接 | 非 mp 原始链接 | 不入 IMA，仅入周报 |
| 分类大量进根目录 | taxonomy 关键词不够细 | 按"精确子串匹配"原则，给多字词补单字别名 |
| "公司"关键词吃掉专业文章 | 太宽泛 | 改用"公司法"替"公司"，降低优先级 |

## 打包内容

```
legal-weekly-briefing/
├── SKILL.md                          ← 本文件（含完整的 Level 0-3 + 适配向导 + MP 配置指南）
├── README.md                         ← 面向用户的项目主页
├── scripts/
│   ├── demo.py                       ← Level 0 快速体验：一条命令出演示周报
│   ├── scoring_engine.py             ← k-NN 评分引擎 v2.1
│   ├── run_pipeline.py               ← 流水线编排：去重→评分→周报→IMA队列
│   ├── dedupe.py                     ← URL/标题去重
│   ├── ima_importer.py               ← IMA 分类+导入
│   ├── normalize_url.py              ← 聚合链接还原为 mp 原始链接
│   └── verify.py                     ← 回归测试（安装后自检）
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
    └── mp-setup-guide.md             ← MP 自动发现独立速查卡（与 SKILL.md 第 3 章同内容，方便离线阅读）
```

## 外部依赖（未打包）

| 依赖 | 说明 |
|------|------|
| `wechat-ocr-research` skill | MP 后台文章拉取 + session 管理 |
| IMA OpenAPI 凭证 | `~/.config/ima/client_id` + `api_key` |
| Microsoft Edge + MP 登录态 | 自动读 cookie 的前提 |
| pyyaml | Python 包，pip install |
