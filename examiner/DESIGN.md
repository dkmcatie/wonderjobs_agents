# Examiner 组件设计文档

**日期**: 2026-04-27  
**状态**: 设计阶段  
**最后更新**: 2026-04-27

---

## 概述

Examiner 是 WonderJobs 多智能体面试系统中的第二个核心组件，负责基于岗位 JD 和面试官风格，自动生成 20 道定制化的面试题目。

**核心功能**：
- 输入：岗位 JD (Markdown) + 面试官风格档案 (Markdown) + 公司/岗位名称
- 流程：RAG 查询 → WebSearch 检索 → Qwen 生成 → 格式化输出
- 输出：20 道定制化题目 (JSON + Markdown 格式)

---

## 需求分析

### 输入需求

| 输入 | 类型 | 说明 |
|------|------|------|
| JD | Markdown 文件 | 岗位职位描述 |
| Personality | Markdown 文件 | 面试官风格档案 |
| Company | 字符串 | 公司名称（用于标签） |
| Position | 字符串 | 岗位名称（用于标签） |

### 输出需求

**题目数量**: 20 道

**题目标签体系**:
- **公司** (company): 如"字节跳动"
- **岗位** (position): 如"广告大模型算法工程师"
- **提问环节** (question_phase): 
  - 简历提问
  - 技术能力提问
  - 项目经验提问
  - 行为/软技能提问
- **难度** (difficulty): 初级、中级、高级

**输出格式**: 
- JSON 结构化格式（便于系统处理）
- Markdown 可读格式（便于人工审查）

### 题目生成策略

**三层融合**:
1. **RAG 参考** (10 道): 从历史库随机生成参考题目
2. **WebSearch 参考** (5-10 道): 搜索行业真实题目
3. **Qwen 生成** (20 道): 基于以上参考，生成定制化题目

---

## 架构设计

### 目录结构

```
examiner/
├── examiner.py              # 主入口，CLI 和核心流程
├── prompts.yaml             # Qwen API 的 prompt 模板
├── config.yaml              # 配置文件（API 端点、Key 等）
├── requirements.txt         # Python 依赖
├── DESIGN.md                # 本设计文档
├── README.md                # 使用文档
│
├── modules/
│   ├── __init__.py
│   ├── rag_client.py        # RAG 知识库查询模块
│   ├── web_search.py        # WebSearch 集成模块
│   ├── qwen_client.py       # Aliyun Qwen API 调用
│   └── question_generator.py # 题目生成和协调
│
├── utils/
│   ├── __init__.py
│   ├── validators.py        # 输入验证
│   ├── formatters.py        # 输出格式化（JSON、Markdown）
│   └── file_handler.py      # 文件读写操作
│
└── outputs/                 # 输出目录（git ignore）
    └── .gitkeep
```

### 核心数据流

```
输入阶段
├── 读取 JD (Markdown)
├── 读取 Personality (Markdown)
├── 验证输入（非空、文件存在等）
└── 从 config.yaml 加载 API 配置

处理阶段
├── 步骤 1: RAG 查询
│   └── 随机生成 10 道参考题目（模拟历史库查询）
│       包含标签：[公司, 岗位, 提问环节, 难度]
│
├── 步骤 2: WebSearch
│   └── 搜索"[公司] [岗位] 面试题目"相关结果
│       提取 5-10 道行业真实题目
│
├── 步骤 3: 题目生成
│   └── 调用 Qwen API，输入：
│       - JD 内容
│       - Personality 风格
│       - RAG 参考题目（10 道）
│       - WebSearch 参考题目（5-10 道）
│       - 任务 Prompt：生成 20 道定制化题目
│       输出：20 道题目 + 标签
│
└── 步骤 4: 输出格式化
    ├── 生成 questions.json（结构化）
    └── 生成 questions.md（可读版本）

输出阶段
├── questions.json (20 道题目 + 元数据)
└── questions.md (Markdown 格式)
```

---

## CLI 接口设计

### 命令语法

```bash
python examiner.py \
  --jd job_description.md \
  --personality interviewer_style.md \
  --company "字节跳动" \
  --position "广告大模型算法工程师" \
  [--output questions.json] \
  [--config config.yaml]
```

### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--jd` | 文件路径 | ✅ | 岗位 JD（Markdown） |
| `--personality` | 文件路径 | ✅ | 面试官风格档案（Markdown） |
| `--company` | 字符串 | ✅ | 公司名称（用于标签） |
| `--position` | 字符串 | ✅ | 岗位名称（用于标签） |
| `--output` | 文件路径 | ❌ | 输出文件路径（默认：questions.json） |
| `--config` | 文件路径 | ❌ | 配置文件（默认：config.yaml） |

---

## 输出格式规范

### questions.json 结构

```json
{
  "metadata": {
    "company": "字节跳动",
    "position": "广告大模型算法工程师",
    "total_questions": 20,
    "generated_at": "2026-04-27T10:30:00Z",
    "model": "qwen-omni-mini"
  },
  "questions": [
    {
      "id": 1,
      "text": "请介绍一下你在简历中提到的XXX项目，以及你在其中的具体贡献。",
      "phase": "简历提问",
      "difficulty": "初级",
      "tags": {
        "company": "字节跳动",
        "position": "广告大模型算法工程师",
        "question_phase": "简历提问",
        "difficulty": "初级"
      }
    },
    {
      "id": 2,
      "text": "在实现LLM推荐系统时，如何处理冷启动问题？",
      "phase": "技术能力提问",
      "difficulty": "高级",
      "tags": {
        "company": "字节跳动",
        "position": "广告大模型算法工程师",
        "question_phase": "技术能力提问",
        "difficulty": "高级"
      }
    }
  ]
}
```

### questions.md 结构

```markdown
# 面试题目池

**岗位**: 字节跳动 - 广告大模型算法工程师  
**生成时间**: 2026-04-27  
**题目总数**: 20

---

## 简历提问 (5道)

### 1. 初级 - 请介绍一下你在简历中提到的XXX项目...
[题目文本]

### 2. 中级 - [题目文本]
[题目文本]

...

## 技术能力提问 (8道)

### 6. 高级 - 在实现LLM推荐系统时...
[题目文本]

...

## 项目经验提问 (4道)
...

## 行为/软技能提问 (3道)
...
```

---

## 模块职责划分

### modules/rag_client.py

**职责**: 模拟 RAG 知识库查询

**核心函数**:
```python
def query_similar_questions(company: str, position: str, phase: str = None) -> List[Dict]:
    """
    查询历史库中的相似题目
    
    Args:
        company: 公司名称
        position: 岗位名称
        phase: 提问环节（可选）
    
    Returns:
        10 道参考题目的列表，每道包含 text、phase、difficulty、tags
    
    当前实现: 随机生成（后续可替换为真实 RAG API 调用）
    """
```

### modules/web_search.py

**职责**: 调用 WebSearch API 查找行业题目

**核心函数**:
```python
def search_interview_questions(company: str, position: str, limit: int = 10) -> List[str]:
    """
    搜索行业标准面试题目
    
    Args:
        company: 公司名称
        position: 岗位名称
        limit: 返回题目数量
    
    Returns:
        搜索到的题目文本列表
    
    当前实现: 暂时禁用（enabled: false），返回空列表
    后续可接入 SerpAPI、Google Custom Search 等
    """
```

### modules/qwen_client.py

**职责**: 封装 Aliyun Qwen API 调用

**核心函数**:
```python
def generate_questions(
    jd: str,
    personality: str,
    rag_questions: List[Dict],
    web_questions: List[str],
    company: str,
    position: str,
    config: Dict
) -> List[Dict]:
    """
    调用 Qwen API 生成定制化题目
    
    Returns:
        20 道题目列表，每道包含 id、text、phase、difficulty、tags
    """
```

### modules/question_generator.py

**职责**: 协调生成流程，管理整体逻辑

**核心函数**:
```python
def generate_questions_pool(
    jd: str,
    personality: str,
    company: str,
    position: str,
    config: Dict
) -> Tuple[List[Dict], str]:
    """
    协调调用 RAG、WebSearch、Qwen，生成题目池
    
    Returns:
        (题目列表, 生成摘要)
    """
```

### utils/validators.py

**职责**: 输入验证

**核心函数**:
```python
def validate_jd(content: str) -> bool
def validate_personality(content: str) -> bool
def validate_company_position(company: str, position: str) -> bool
```

### utils/formatters.py

**职责**: 输出格式化

**核心函数**:
```python
def to_json(questions: List[Dict], metadata: Dict) -> str
def to_markdown(questions: List[Dict], metadata: Dict) -> str
```

### utils/file_handler.py

**职责**: 文件读写操作

**核心函数**:
```python
def read_markdown(path: str) -> str
def write_json(path: str, data: Dict) -> None
def write_markdown(path: str, content: str) -> None
```

---

## 配置管理

### config.yaml 结构

```yaml
# Aliyun Qwen API 配置
qwen:
  api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "${ALIYUN_API_KEY}"  # 从环境变量读取
  model: "qwen-omni-mini"
  timeout: 30

# WebSearch API 配置（未来使用）
web_search:
  enabled: false
  provider: "serpapi"  # 或 "google_custom_search"
  api_key: "${WEB_SEARCH_API_KEY}"

# RAG 配置
rag:
  enabled: false  # 当前禁用，后续可接入真实服务
  # type: "pinecone"
  # endpoint: "https://..."
  # api_key: "${RAG_API_KEY}"

# 题目生成配置
generation:
  total_questions: 20
  rag_reference_count: 10
  web_search_reference_count: 5
  
  # 提问环节分布
  phase_distribution:
    简历提问: 5
    技术能力提问: 8
    项目经验提问: 4
    行为/软技能提问: 3

# 输出配置
output:
  format: ["json", "markdown"]
  directory: "./outputs"
  json_indent: 2

# Prompt 配置
prompts:
  path: "./prompts.yaml"
```

---

## 错误处理

### 输入验证

```
检查项目：
├── JD 文件存在且非空
├── Personality 文件存在且非空
├── 公司名称非空
├── 岗位名称非空
└── 输出目录可写

异常处理：
├── FileNotFoundError → "找不到输入文件"
├── ValueError → "公司名称/岗位名称格式错误"
├── PermissionError → "输出目录权限不足"
└── 返回清晰的错误消息 + 建议
```

### API 调用异常处理

```
Qwen API 异常：
├── Timeout → 重试机制（最多 3 次）
├── RateLimit → 等待后重试
├── InvalidAPIKey → 提示检查 ALIYUN_API_KEY
├── 其他错误 → 记录详细错误日志

WebSearch 异常（未来使用时）：
└── 失败时返回空列表，继续进行
```

### 数据质量检查

```
生成的题目验证：
├── 每道题目 text 非空
├── phase 值在允许范围内
├── difficulty 值在允许范围内
├── 总数恰好为 20 道
└── 标签完整性检查

失败处理：
└── 输出警告但继续（不中断整个流程）
```

### 日志输出

```
输出级别：
├── INFO: 流程进度（"已读取 JD 文件", "Qwen API 调用中"等）
├── WARNING: 数据质量警告（"题目 X 的 phase 值无效"等）
└── ERROR: 致命错误（文件不存在、API Key 无效等）

日志目标：
├── 控制台输出（用户可见）
└── 可选：log 文件（./outputs/examiner.log）
```

---

## 后续扩展点

1. **RAG 集成**: 替换随机生成，接入真实 RAG 服务（Pinecone、Milvus 等）
2. **WebSearch 集成**: 启用 WebSearch 功能，接入 SerpAPI 或 Google Custom Search
3. **多语言支持**: 扩展对英文等其他语言的支持
4. **题目库管理**: 生成的题目自动存储回 RAG 知识库，持续优化
5. **评分机制**: 为每道题目添加难度预测和质量评分

---

## 依赖清单

```
pyyaml>=6.0          # YAML 配置解析
requests>=2.28.0     # HTTP 请求
python-dotenv>=0.19  # 环境变量管理
```

---

## 成功标准

实现完成后应满足：

- ✅ CLI 接口可正常调用，参数校验完整
- ✅ 生成 20 道题目（不多不少）
- ✅ 每道题目包含完整的标签（公司、岗位、提问环节、难度）
- ✅ 输出 JSON 和 Markdown 两种格式
- ✅ 错误处理完善，提供清晰的错误提示
- ✅ 代码模块清晰，易于维护和扩展
- ✅ 文档完整，包括 README 和使用示例

---

**设计完成日期**: 2026-04-27  
**下一步**: 编写实现计划
