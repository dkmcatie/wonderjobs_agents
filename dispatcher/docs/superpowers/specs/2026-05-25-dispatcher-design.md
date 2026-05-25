# Dispatcher 设计文档

**日期**：2026-05-25  
**状态**：已确认  
**目标**：构建一个 MoE-inspired 的 skill 路由系统，模拟 Claude 如何决定调用哪个 skill

---

## 概述

Dispatcher 接收用户的自然语言输入，通过「快速向量路由 + LLM fallback」两级架构，决定调用哪个 skill，并提取执行所需的参数。

---

## 架构

### 目录结构

```
dispatcher/
├── skills/                  # 10 个 skill 定义
│   └── *.yaml               # 每个 skill 的 manifest
├── index/                   # 离线构建的向量索引
│   └── skill_index.json     # {skill_name: centroid_vector, examples: [...]}
├── dispatcher.py            # 主入口，在线路由逻辑
├── builder.py               # 离线脚本，构建 skill 向量索引
└── config.yaml              # 阈值、embedding 模型、LLM 配置
```

### 两阶段运行

**离线阶段（builder.py）**：一次性构建向量索引，skill 新增或修改时重新运行。

**在线阶段（dispatcher.py）**：每次用户请求触发，纯向量计算为主路径，LLM 为兜底。

---

## 10 个示例 Skills

| Skill | 功能描述 |
|-------|---------|
| `web_search` | 搜索网络信息，查询实时数据 |
| `write_email` | 撰写各类邮件 |
| `translate` | 翻译文本，支持多语言 |
| `summarize` | 总结文章或长文本内容 |
| `write_code` | 编写新的代码片段或程序 |
| `debug_code` | 调试已有代码，定位错误原因 |
| `create_image` | 生成图片 |
| `schedule_meeting` | 安排会议或日程 |
| `analyze_data` | 分析表格或数据集 |
| `answer_question` | 回答知识性问题 |

语义相近的难点对（路由最难区分）：
- `web_search` vs `answer_question`
- `write_code` vs `debug_code`
- `summarize` vs `answer_question`

---

## Skill Manifest 格式

```yaml
name: write_code
description: 编写代码，用户需要生成新的代码片段、函数或程序
parameters:
  language: "编程语言（可选）"
  task: "需要实现的功能描述"
examples:
  - "帮我写一个快速排序"
  - "用 Python 实现一个爬虫"
```

---

## 核心算法

### 离线：构建向量索引

```
读取 skills/*.yaml
↓
对每个 skill：
  有 examples → 直接使用
  无 examples → 调 LLM 生成 30 条典型触发 query
↓
DashScope embed(每条 query)
↓
centroid = mean(所有向量)
↓
写入 skill_index.json
```

### 在线：路由决策

```
user_input
↓
embed(user_input) → query_vector
↓
for each skill: score = cosine(query_vector, skill.centroid)
↓
gap = top1_score - top2_score
↓
gap > gap_threshold?
  ✅ 是 → 直接路由到 top-1 skill
  ❌ 否 → 取 top-3 候选，调 LLM 精排
           LLM 仍不确定 → 返回 clarify
```

### 统一输出结构

```json
{
  "skill": "write_code",
  "confidence": 0.31,
  "route": "vector | llm_fallback | clarify",
  "params": {},
  "message": "需要补充参数时的追问话术"
}
```

---

## 错误处理

| 情况 | 处理方式 |
|------|---------|
| 所有 scores < min_score_threshold | 返回 `action: unknown`，提示用户描述更具体 |
| LLM fallback 仍无法判断 | 返回 `action: clarify`，列出候选 skills 让用户选 |
| skill_index.json 不存在 | 启动时报错，提示运行 `python builder.py` |

---

## 配置（config.yaml）

```yaml
embedding:
  model: text-embedding-v3
  api_key_env: DASHSCOPE_API_KEY

routing:
  gap_threshold: 0.15
  min_score_threshold: 0.3
  top_k_for_llm: 3

llm_fallback:
  model: qwen-plus
  api_key_env: DASHSCOPE_API_KEY
```

---

## 技术栈

- Python 3.8+
- DashScope API（embedding + LLM fallback）
- NumPy（向量计算）
- PyYAML（skill manifest 解析）
