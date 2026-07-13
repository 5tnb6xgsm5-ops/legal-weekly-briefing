# MP 自动发现 · 独立速查卡

> 从零搭建微信公众号后台自动拉取文章。内容与 SKILL.md Level 3 章节同步，方便离线阅读。

## 前提条件

- 微信公众号后台管理权限（mp.weixin.qq.com）
- 本机 Microsoft Edge 浏览器
- `wechat-ocr-research` skill 已安装 → [GitHub](https://github.com/5tnb6xgsm5-ops/wechat-ocr-research)

## 快速配置（8 步）

### Step 1: 确认 MP 后台登录权限

访问 `https://mp.weixin.qq.com`，用微信扫码登录。能看见左侧菜单栏（素材管理/用户管理/数据分析）即为有权限。**需要「公众号运营者」或「管理员」身份。**

### Step 2: 安装 wechat-ocr-research

```bash
cd ~/.workbuddy/skills/
git clone https://github.com/5tnb6xgsm5-ops/wechat-ocr-research.git
```

或 WorkBuddy 内：「帮我安装 https://github.com/5tnb6xgsm5-ops/wechat-ocr-research」

### Step 3: Edge 登录 MP 后台

1. 打开 Edge，访问 `https://mp.weixin.qq.com`
2. 微信扫码登录
3. 随便点几个页面确认正常
4. **不要关闭 Edge** — Cookie 需浏览器活跃状态才能被脚本读取

### Step 4: 恢复 session

```bash
cd ~/.workbuddy/skills/wechat-ocr-research/scripts
python3 refresh_session_from_edge.py
```

成功输出应包含 `token` 和 `cookie` 字段。

### Step 5: 验证 session

```bash
python3 wechat_mp_reader.py session check
```

期望: `valid: true`。若 `false`，在 Edge 重新登录 MP → 重跑 Step 4。

### Step 6: 获取目标公众号 fakeid

1. MP 后台 → 左侧「素材管理」→「新建图文」
2. 编辑器 →「超链接」→「查找文章」
3. 输入公众号名称搜索
4. 点击搜索结果中的公众号名称 → 地址栏 URL 会包含 `fakeid=xxx`
5. 复制 `fakeid=` 后面的值

填入 `assets/config/sources.yaml`：

```yaml
mp:
  enabled: true
  accounts:
    - name: "公众号名称"
      fakeid: "你获取到的fakeid值"
  per_account_limit: 30
```

### Step 7: 测试

```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Edge cookie database not found | Edge 未安装或未用它登录 MP | 用 Edge 登录 mp.weixin.qq.com |
| session valid: false | Cookie 过期（通常 2-4 小时） | Edge 重新登录 MP，重跑 refresh_session |
| 拉不到某公众号文章 | fakeid 不对或近 30 天未发文 | 重新获取 fakeid |
| 拉到的不是近一周的 | 翻页不够 | 增大 per_account_limit |

## 没有 MP 权限？

- **方案 A**：WebSearch 手动发现 → 整理 `candidates.jsonl` → 跑评分
- **方案 B**：RSS/邮件订阅 → 自动收集 → 转候选人文件
- **方案 C**：在对话中说「查一下最近法律热点」，利用通用搜索

> 长期使用建议搞一个 MP 后台权限（空壳公众号也行），自动化程度远超替代方案。
