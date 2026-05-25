# Dispatcher — Skill 路由系统

基于 MoE（Mixture of Experts）思路设计的 skill 路由模块，接收用户自然语言输入，自动决定调用哪个 skill。

## 工作原理

两级路由架构：

```
用户输入
   ↓
向量路由（快速）: cosine similarity 与所有 skill 质心对比
   ↓
gap > 阈值 → 直接路由到最匹配 skill
gap ≤ 阈值 → LLM 精排（只传 top-3 候选）
   ↓
scores 全低 → 返回 unknown，提示用户描述更具体
```

**离线阶段**（`builder.py`）：为每个 skill 生成示例 query，计算 embedding 质心，保存向量索引。

**在线阶段**（`dispatcher.py`）：embed 用户输入，与索引做相似度匹配，输出路由结果。

---

## 目录结构

```
dispatcher/
├── skills/              # Skill 定义（YAML）
│   ├── web_search.yaml
│   ├── write_email.yaml
│   ├── translate.yaml
│   ├── summarize.yaml
│   ├── write_code.yaml
│   ├── debug_code.yaml
│   ├── create_image.yaml
│   ├── schedule_meeting.yaml
│   ├── analyze_data.yaml
│   └── answer_question.yaml
├── index/               # 离线构建的向量索引（gitignored）
│   └── skill_index.json
├── tests/               # 单元测试
├── embed.py             # DashScope embedding 封装
├── builder.py           # 离线索引构建
├── dispatcher.py        # 在线路由
├── config.yaml          # 配置
└── requirements.txt
```

---

## 环境依赖

```bash
pip install -r requirements.txt
```

需要阿里云 DashScope API Key：

```bash
export DASHSCOPE_API_KEY="your-key-here"
```

---

## 快速开始

### 第一步：构建向量索引

```bash
python builder.py
```

输出：`Building index for 10 skills... Index saved to index/skill_index.json`

### 第二步：路由用户输入

```bash
python dispatcher.py "帮我写一个快速排序算法"
```

输出示例：

```json
{
  "skill": "write_code",
  "confidence": 0.312,
  "route": "vector",
  "params": {},
  "message": ""
}
```

---

## 输出字段说明

| 字段 | 说明 |
|------|------|
| `skill` | 匹配到的 skill 名称，`null` 表示无法确定 |
| `confidence` | 路由置信度（top1 与 top2 的 cosine 差值） |
| `route` | 路由路径：`vector` / `llm_fallback` / `clarify` / `unknown` |
| `params` | 提取的参数（当前为空，可扩展） |
| `message` | 需要追问用户时的提示语 |

### route 字段说明

| 值 | 含义 |
|----|------|
| `vector` | 向量路由直接命中，置信度高 |
| `llm_fallback` | 向量路由不确定，LLM 精排后命中 |
| `clarify` | LLM 也无法确定，需要用户澄清 |
| `unknown` | 所有 skill 相似度都很低，无法路由 |

---

## CLI 参数

```bash
python dispatcher.py <用户输入> [--config config.yaml] [--index index/skill_index.json]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `input` | ✅ | — | 用户的自然语言输入 |
| `--config` | ❌ | `config.yaml` | 配置文件路径 |
| `--index` | ❌ | `config` 中指定 | 向量索引文件路径 |

---

## Skill Manifest 格式

每个 skill 是一个 YAML 文件，放在 `skills/` 目录下：

```yaml
name: write_code
description: 编写新的代码片段、函数、脚本或完整程序
parameters:
  task: "需要实现的功能描述"
  language: "编程语言（可选）"
examples:
  - "帮我写一个快速排序算法"
  - "用 Python 实现一个文件读取脚本"
```

- `examples` 存在时直接使用，不存在时由 LLM 自动生成 30 条
- 新增 skill 后需重新运行 `python builder.py`

---

## 配置说明（config.yaml）

```yaml
embedding:
  model: text-embedding-v3       # DashScope embedding 模型
  api_key_env: DASHSCOPE_API_KEY # API key 环境变量名

routing:
  gap_threshold: 0.15            # 向量路由置信度阈值，低于此值触发 LLM
  min_score_threshold: 0.3       # 最低相似度，低于此值返回 unknown
  top_k_for_llm: 3               # LLM 精排时传入的候选数量

llm_fallback:
  model: qwen-plus               # LLM 精排使用的模型

builder:
  examples_per_skill: 30         # 每个 skill 自动生成的示例数量
  skills_dir: skills             # skill YAML 目录
  index_path: index/skill_index.json
```

---

## 运行测试

```bash
python -m pytest tests/ -v
```

预期：15 个测试全部通过。

---

## 典型路由示例

| 用户输入 | 路由结果 | 路径 |
|---------|---------|------|
| `帮我写一个排序算法` | `write_code` | vector |
| `这段代码报错了` | `debug_code` | vector / llm_fallback |
| `量子计算是什么原理` | `answer_question` | vector |
| `帮我查一下今天天气` | `web_search` | vector |
| `把这段话翻译成英文` | `translate` | vector |
