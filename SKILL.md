---
name: 法律周报
description: "用户说「生成法律周报」「帮我筛法院公众号文章」「法律简报」「案例入库」时触发。从法院公众号（上海一中院/二中院/山东高法等）文章中用可解释的 k-NN 评分引擎筛出 10 条精品周报，其余实务文章全量入库 IMA 知识库做 RAG。临时法律热点查询走 legal-hot，不要用本 skill。"
author: "社区贡献者"
agent_created: true
version: 2.0.0
---

# 法律周报自动化 · Legal Weekly Briefing

## 全局禁令（Agent 铁律）

> 以下规则在整个 skill 执行期间**必须遵守**。违反任一条 = 交付阻断。

| 场景 | 必须遵守 | 不应发生 |
|------|---------|---------|
| IMA 知识库 | 仅限用户自建个人 KB，使用前确认归属 | 不应指引订阅/加入/接受邀请非自建 KB |
| KB_ID | 用 `YOUR_KNOWLEDGE_BASE_ID` 占位符；用户提供后先确认「是自建的吗？」再写入 | 不应提供或暗示任何具体 KB_ID（含示例） |
| HTML 交付 | 仅用 `render_html.py` 渲染（`#f8f7f5` / `#1a1a2e` 浅色简报风） | 不应自造深色翻页幻灯片或其他替代样式 |
| 交付验证 | 每次修改后必须跑 `python3 scripts/verify.py`，17 项全通过 | 不应跳过验证或仅凭人眼判断 |
| 候选数据 | 每条候选必须含 `abstract` + `recommend` | 不应构建缺少必填字段的 candidates.jsonl |
| session.json | 仅本地使用，`.gitignore` 已排除 | 不应分享/提交到 Git/发送到任何服务器 |
| 样式修改 | 需要改样式时先问用户确认 | 不应擅自改动配色/布局/交互 |
| 适配流程 | 用户说「配置法律周报」→ 必须按适配向导 4 问引导 | 不应跳过适配向导给通用配置 |

---

## 第一性原理

同一批法院公众号文章，走两条管道分流：

> **周报管道**：k-NN 评分引擎挑 10 条精品 → 律师主动阅读
> **知识库管道**：全量实务文章入库 IMA → 检索增强（RAG）

周报解决"本周重点看什么"，知识库解决"以后能找到什么"。两条管道共享内容发现层，在评分环节分叉。

**核心交付模式**：「配置一次，每周自动推送」——依赖外部调度层（WorkBuddy Automation / GitHub Actions cron）定时触发。

---

## 分级架构

```
Level 0 · 5 分钟快速体验（零配置，零依赖）
  └─ 预置 10 条示范候选 → demo.py → 演示周报 MD+HTML

Level 1 · 纯评分引擎（零外部依赖）
  └─ 用户提供候选 URL 列表 → k-NN 评分排序 → 周报 MD+HTML

Level 2 · + IMA 知识库（需 IMA 账号）
  └─ Level 1 + ima_importer.py → 分类 → import_urls → 全量入库

Level 3 · + MP 自动发现（需 MP 后台权限）
  └─ Level 1 + wechat-ocr-research → MP 后台拉取三账号文章
```

---

## 快速开始

**生成演示周报**：在 WorkBuddy 对话中说「帮我用 legal-weekly-briefing 生成一份演示周报」。AI 自动运行 `demo.py`，生成 MD + HTML 两份文件。

**生成真实周报**：对话中说「帮我生成本周法律周报」。AI 自动搜索 → 构建候选 → 评分排序 → 交付。

**配置自己的周报**：对话中说「帮我配置法律周报」。AI 按适配向导引导你完成四问配置。

<details>
<summary>终端手动运行（备选）</summary>

```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
python3 scripts/demo.py
```
</details>

---

## 适配向导（4 问流程）

> 用户表达「想配置法律周报」意图时，Agent 必须主动引导。完整话术和分支逻辑见 `references/adaptation-wizard.md`。

| 问次 | 主题 | 决定 | Agent 关键动作 |
|------|------|------|--------------|
| 1 | 执业方向 | `interest_keywords` + taxonomy priority | 写入 settings.yaml；告知「兴趣赛道加成 +0.3 分」 |
| 2 | 关注公众号 | `sources.yaml` | 保留三个示范法院默认；追加用户指定的公众号 |
| 3 | MP 后台权限 | 是否启用 Level 3 | 有 → 引导 MP 配置（见 `references/mp-setup-guide.md`）；无 → 保持 WebSearch 模式 |
| 4 | IMA 知识库 | 是否启用 Level 2 | 有 → 先确认「自建个人 KB」（铁律检查）→ 引导获取 KB_ID/folder_id/API 凭证；无 → 保持 Level 1 |

**只想要 Level 1**：在 Agent 问完前两问后告知，Agent 跳过第三、四问。

---

## Level 1 · 纯评分引擎

### 核心工作流

```
用户说「帮我生成本周法律周报」
  → Agent 搜索近一周法律动态 + 法院公众号文章
  → 构建 candidates.jsonl（含 abstract + recommend）
  → run_pipeline.py（去重 → k-NN 评分排序 → MD + HTML）
  → present_files 交付周报
```

### k-NN 评分引擎 v2.1

**法律条目（4 维）**

| 维度 | 权重 | 1 | 2 | 3 | 4 | 5 |
|------|------|---|---|---|---|---|
| author_tier | 0.35 | 最高法/知名学者 | 省高院/中院法官 | 基层/编辑 | 媒体 | — |
| platform_tier | 0.30 | 入库案例/最高法公报 | 中国审判/人民法院报 | 品牌栏目 | 一般 | 聚合 |
| depth | 0.20 | 规则+交锋+结论 | 有具体分析 | 综述/新闻 | — | — |
| relevance | 0.15 | 直接对标实务 | 有一定参考 | 泛资讯 | — | — |

**AI+法律条目（4 维）**

| 维度 | 权重 | 1 | 2 | 3 |
|------|------|---|---|---|
| signal_strength | 0.50 | 格局级（大厂入局/旗舰模型/监管） | 应用落地级 | 融资动态级 |
| depth | 0.25 | 有具体功能细节+分析 | 有具体分析 | 新闻/综述 |
| relevance | 0.15 | 直接对标国内律师实务 | 有一定参考 | 泛行业资讯 |
| domestic_relevance | 0.10 | 国内可借鉴=1 | 不适用=0 | — |

### 评分锚定

| 分数 | 法律条目锚点 | AI+法律条目锚点 |
|------|-------------|----------------|
| 9-10 | 入库案例/司法解释+配套案例 | signal_strength=1 格局级 + depth=1 |
| 8-8.9 | 中院法官+品牌栏目+具体结论 | signal_strength=2 应用落地级 |
| 7-7.9 | 高院公众号一般案例 | 行业动态有参考 |
| 5-6 | 发布会/报告/立法动态 | signal_strength=3 融资动态级 |

### 特征区分原则（核心）

内容深度是评分区分度的核心维度。**不能给所有法院公众号文章统一标相同的特征向量。**

```
depth=1  体系化分析方法论（类型化框架、风险清单、审查要点系统梳理）
depth=2  个案叙事/案例选登（有案例事实+裁判要旨，但偏个案）
```

### 降级行为

| 场景 | 行为 |
|------|------|
| 无训练集 | 线性降级打分 + confidence=0，不崩 |
| 候选不足 10 | run_pipeline 非零退出 |
| 评分全部 conf < 0.8 | 正常（训练样本尚少），分数直接采用 |

### 已知限制

- k-NN 依赖训练集质量。内置 62 条偏重特定执业方向，开源用户需按自己领域重新标注
- 特征维度有限（4 维），无法区分新颖性/时效性/写作质量（有意设计取舍）
- 兴趣赛道加成（+0.3）硬编码，在 `settings.yaml` 的 `interest_keywords` 中配置

> 特征标注速查、训练数据替换指引 → `references/feature-guide.md`

---

## Level 2 · IMA 知识库入库

> 完整指南、接入链路、踩坑速查 → `references/ima-level2-guide.md`

**前置条件**：Level 1 验证通过 + IMA 账号 + API 凭证已配。

**工作原理**：`run_pipeline.py` 产出 `ima_import_queue.jsonl` → 按 `taxonomy.yaml` 关键词分配 folder_id → 调用 IMA OpenAPI `import_urls` 入库。

**周报 vs IMA 入库**（两条独立管道）：
- 周报：diversity-aware 选 10 条，同源≤2
- IMA：score ≥ 7.0 法院源条目全部入库，不限条数

**分类规则**：10 个分类，按优先级排序——专业领域（建筑工程/劳动法/交通事故 priority=9）高于通用兜底（合同借贷 priority=8），避免"劳动合同"被"合同"误捕获。

**IMA 铁律**：仅使用用户自建个人知识库；`knowledge_base_id` 占位符未替换时导入自动阻断。

---

## Level 3 · MP 自动发现

> 完整配置指南、工作原理、替代方案 → `references/mp-setup-guide.md`

**前提条件**：自有微信公众号（订阅号即可，不需发文章）+ Edge 浏览器 + `wechat-ocr-research` skill。

**原理**：微信无公开 API。通过个人 MP 后台的内部接口 `appmsgpublish`（cookie + token + fakeid）拉取目标公众号文章列表。Edge 的 cookie 数据库在 macOS 上不受 SIP 保护，可被脚本直接读取。

**替代方案**（无 MP 权限）：WebSearch 手动发现 → 整理 `candidates.jsonl` → 评分；或 RSS/邮件订阅自动收集；或纯依赖 `legal-hot` skill。

---

## 周报交付格式

标题: `# 法律周报 2026年X月X日-X月X日 · 第N期`

双板块（按评分降序）：
```
## AI + 法律
【9.5】标题 | URL | 描述（含信号级别）

## 纯法律
【9.0】标题 | URL | 描述（含领域标签）
```

页脚：引擎版本 + MP session 状态 + IMA 导入统计 + 排除清单。

---

## 交付门禁

> 完整门禁清单、四条铁律、违规案例 → `references/delivery-gate.md`

| 编号 | 检查项 | 级别 | 说明 |
|------|--------|------|------|
| G1 | `render_html.py` 存在且可导入 | P0 | 文件缺失即阻塞 |
| G2 | 模板风格 = `#f8f7f5` + `#1a1a2e`，无翻页 JS | P0 | 样式不符即阻塞 |
| G3 | 模板含 `abstract`/`recommend`/`fav-btn` | P0 | 缺字段即阻塞 |
| G4 | `demo.py` 候选含 `abstract`/`recommend` | P0 | 示范数据不完整即阻塞 |
| G5 | `run_pipeline.py` 含 HTML 渲染步骤 | P0 | 流水线缺步骤即阻塞 |
| G6 | `taxonomy.yaml` 的 `knowledge_base_id` 非作者/他人 KB | P0 | 作者 KB → 阻断；占位符 → 警告 |

```bash
python3 scripts/verify.py
# 期望: "17 通过 / 0 失败" → exit code 0
```

---

## 外部依赖

| 依赖 | 说明 |
|------|------|
| `wechat-ocr-research` skill | MP 后台文章拉取 + session 管理 |
| IMA OpenAPI 凭证 | `~/.config/ima/client_id` + `api_key` |
| Microsoft Edge + MP 登录态 | 自动读 cookie 的前提 |
| pyyaml | Python 包，`pip3 install pyyaml` |
| Python 3.9+ | 脚本运行环境 |

---

## 安全与隐私

- **IMA 知识库**：文章导入的是**你自己的知识库**，不在第三方服务器上
- **MP 登录态**：`session.json` 仅存储本地，**绝对不要分享或提交到 Git**（`.gitignore` 已排除）
- **API 凭证**：`client_id` / `api_key` 仅请求 IMA 官方 API（`ima.qq.com`），不发送到其他服务器

### 绝对不要分享

| 文件 | 风险 | 防护 |
|------|------|------|
| `cache/session.json` | 含完整 MP 登录态，可被他人操纵你的公众号 | `.gitignore` 已排除 |
| `~/.config/ima/client_id` + `api_key` | 他人可向你的 IMA 知识库写入 | 仅本地存储 |
| `config/.env` | 可能含 API 密钥 | `.gitignore` 已排除 |

---

## References 索引

| 文件 | 内容 |
|------|------|
| [`references/feature-guide.md`](references/feature-guide.md) | 特征标注速查 + 训练数据替换指引 |
| [`references/adaptation-wizard.md`](references/adaptation-wizard.md) | 适配向导 4 问流程（Agent 话术 + 分支逻辑） |
| [`references/ima-level2-guide.md`](references/ima-level2-guide.md) | IMA Level 2 完整指南（接入链路 + 分类规则 + 踩坑表） |
| [`references/ima-pitfalls.md`](references/ima-pitfalls.md) | IMA 接入踩坑卡（7 坑速查 + 接入链路图） |
| [`references/mp-setup-guide.md`](references/mp-setup-guide.md) | MP 自动发现完整配置（8 步 + 常见问题 + 替代方案） |
| [`references/delivery-gate.md`](references/delivery-gate.md) | 交付门禁卡（17 项核查 + 铁律 + 违规案例） |
| [`references/automation-setup.md`](references/automation-setup.md) | 自动化调度配置（WorkBuddy / GitHub / cron） |

---

## 打包结构

```
legal-weekly-briefing/
├── SKILL.md                         ← 本文件
├── scripts/                         ← 评分引擎 + 流水线 + 渲染 + 验证
├── assets/config/                   ← settings.yaml / sources.yaml / taxonomy.yaml
├── assets/data/                     ← 训练样本 + 回归用例
└── references/                      ← 详细指南（7 个文件）
```

## Rationalizations

1. **分级架构**：四级独立运行，上层依赖下层，降低开源用户门槛
2. **k-NN 选型**：4 维特征向量可解释，训练数据可替换，降级不崩
3. **IMA 独立管道**：周报精选 ≠ IMA 全量，各自优化目标不同
4. **MP 走 Edge**：macOS SIP 限制 Chrome/Safari，Edge 路径不受保护
5. **门禁驱动**：verify.py 17 项检查保证交付一致性，评分回归测试 ≠ 交付质量保证

## 配置指南（零基础版）

> 用户说「配置法律周报」时触发此段。按 Level 逐级引导，每级完成后再问是否升级。

### Level 1 · 纯评分（零配置，2 分钟可用）
用户只需说「帮我生成本周法律周报」→ Agent 自动 WebSearch → 评分排序 → 交付。
**无需任何配置**。唯一可选：告诉 Agent 你的执业方向（如「建筑工程」），评分会自动加成 +0.3 分。

### Level 2 · + IMA 知识库（需 5 分钟配置）
**需要什么**：IMA 账号（ima.qq.com 注册，免费）+ 自建个人知识库。
**怎么做**：① 登录 IMA → 左侧「知识库」→「新建」→ 记住名称 ② 打开 IMA 开发者设置 → 复制 `client_id` 和 `api_key` ③ 在知识库设置 → 复制 `knowledge_base_id`（一串数字）④ 把三个值告诉 Agent → Agent 写入配置 → 完成。
**效果**：每周评分 ≥ 7.0 的文章自动入库，以后可检索。

### Level 3 · + MP 自动发现（需 10 分钟配置）
**需要什么**：个人微信公众号（订阅号即可，不需发文章）+ Edge 浏览器。
**怎么做**：① 登录微信公众平台（mp.weixin.qq.com）→ 左侧「内容管理」→ 确认能看到已发布文章列表 ② Agent 引导关注目标公众号（建议关注至少 3 个法院公众号）③ Agent 读取 Edge cookie 中的 MP 登录态 → 自动拉取文章列表。
**效果**：不再需要手动搜文章，Agent 自动从关注的公众号拉取。

### 常见问题
- **没有 MP 权限**：直接用 Level 1，Agent 用 WebSearch 搜索文章，效果类似
- **IMA 注册不了**：跳过 Level 2，周报功能完全不受影响
- **Edge vs Chrome**：macOS 下 Edge 的 cookie 路径不受 SIP 保护，Chrome 受保护读不到
- **不想装 Python 包**：Agent 会帮你装 `pip3 install pyyaml`，一行命令
