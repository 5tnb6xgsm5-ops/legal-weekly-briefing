# 法律周报 · 交付门禁卡

> 评分引擎回归测试只保证「打分没崩」。这张门禁卡保证「产出的东西是对的」。

## 自动检查（`scripts/verify.py`）

```bash
python3 scripts/verify.py
# 期望：17 通过 / 0 失败
```

## 门禁项

| 编号 | 检查项 | 级别 | 失败后果 |
|------|--------|------|----------|
| G1 | `render_html.py` 存在且可导入 | P0 | 阻塞交付 |
| G2 | 模板风格 = #f8f7f5（浅色背景）+ #1a1a2e（深色页眉）、无翻页 JS | P0 | 阻塞交付 |
| G3 | 模板含 `{abstract}` / `{recommend}` / `fav-btn` | P0 | 阻塞交付 |
| G4 | `demo.py` 候选数据含 `abstract` + `recommend` 字段 | P0 | 阻塞交付 |
| G5 | `run_pipeline.py` 含 HTML 渲染调用 | P0 | 阻塞交付 |
| G6 | `taxonomy.yaml` `knowledge_base_id` 非作者/他人 KB | P0 | 作者 KB → 阻断；占位符 → 警告（打包版合法） |

## 四条铁律（Agent 强制执行）

```
1. HTML 只用 render_html.py
   禁止自造深色翻页幻灯片、ImageGen、或任何替代样式。

2. 每条候选必须含 abstract + recommend
   构建 candidates.jsonl 时同步补充，缺失 = 空卡片 = 阻塞。

3. 样式不可改
   不改配色/布局/交互，改前必须先问用户。

4. IMA 知识库必须是用户自建的「个人知识库」
   禁止引导用户订阅/加入他人 KB（含共享/团队/社区）。
   唯一合法路径：ima.qq.com → 创建知识库 → 个人知识库 → 自行获取 KB_ID。
   禁止向用户提供或暗示任何具体 knowledge_base_id。
```

## 违规案例

### 案例 1: 自造深色翻页版 HTML（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 交付了 `#0f1117` 背景 + ← → 翻页的幻灯片 |
| 根因 | 未读已确认模板，从跨项目记忆里臆造了样式 |
| 修复 | 改用 render_html.py 重渲；verify.py G2 拦截 |

### 案例 2: 候选缺 abstract/recommend（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | HTML 卡片空摘要空推荐 |
| 根因 | candidates.jsonl 缺渲染必需字段 |
| 修复 | 补字段；verify.py G4 拦截 |

### 案例 3: 流水线无 HTML 步骤（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 项目目录旧版 run_pipeline.py 只出 MD |
| 根因 | 项目版与 skill 版不同步 |
| 修复 | 补 Stage 4.5；verify.py G5 拦截 |

### 案例 4: IMA 引导缺失·自建 KB（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 用户反馈配置流程未引导自建知识库，出现引导订阅他人 KB 的情况 |
| 根因 | SKILL.md 第三问跳过了「Step 0: 自建知识库」；Agent 铁律未禁止提供他人 KB_ID |
| 修复 | SKILL.md 第三问重写（加 KB 归属确认 + Step 0-5 + 铁律 4）；verify.py G6 拦截作者 KB_ID 泄漏；import_ima.py 运行时 guard 阻断占位符/作者 KB；项目目录 taxonomy.yaml KB_ID 清除为占位符 |
