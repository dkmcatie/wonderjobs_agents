# Bocha WebSearch API 集成设计文档

**日期**: 2026-04-28  
**状态**: 设计阶段  
**作者**: Claude Code (Brainstorming)

---

## 1. 概述

### 目标

将 **Bocha AI Search API** 集成到 Examiner 组件的 WebSearch 模块，用于搜索行业真实的面试题目，作为 Qwen 生成题目的参考。

### 核心需求

- 搜索 3-5 个不同角度的关键词，获取 10-15 道行业参考题目
- 仅提取题目文本，不需要 URL 或摘要
- 支持失败重试（最多 3 次）+ 降级继续流程
- 配置驱动，支持环境变量注入 API Key
- 搜索词由 Qwen 根据 JD 智能生成

---

## 2. 设计决策

| 决策项 | 选项 | 理由 |
|--------|------|------|
| **搜索结果内容** | 仅提取题目文本 | 简洁高效，减少 token 消耗 |
| **搜索词生成** | Qwen 生成多个搜索词 + Bocha 并行调用 | 提高覆盖面和相关性 |
| **参考题目数量** | 10-15 道 | 丰富参考，成本可控 |
| **配置管理** | config.yaml 基础参数 + prompts.yaml 搜索策略 | 关注点分离，易于维护 |
| **错误处理** | 重试机制 + 降级继续 | 提高鲁棒性，不中断主流程 |
| **架构方案** | 模块解耦（三个新模块） | 职责清晰，易于测试和扩展 |

---

## 3. 架构设计

### 3.1 模块结构

```
examiner/modules/
├── bocha_client.py         [NEW] Bocha API 底层调用
├── query_generator.py      [NEW] 搜索词生成
├── web_search.py           [MODIFY] WebSearch 流程协调
├── question_generator.py   [MODIFY] 集成 Bocha 调用
├── rag_client.py           (保持不变)
└── qwen_client.py          (保持不变)
```

### 3.2 数据流

```
question_generator.py
│
├─ Step 1: RAG 查询
│   └─→ rag_client.query_similar_questions()
│       └─→ 10 道历史参考题目
│
├─ Step 2: 生成搜索词 [NEW]
│   └─→ query_generator.generate_search_queries()
│       └─→ 调用 Qwen（通过 prompts.yaml）
│           └─→ 3-5 个搜索关键词
│
├─ Step 3: Bocha WebSearch [NEW]
│   └─→ web_search.search_interview_questions()
│       ├─→ query_generator.generate_search_queries()
│       ├─→ bocha_client.call_bocha_api() × N（并行）
│       └─→ 合并去重
│           └─→ 10-15 道网络参考题目
│
└─ Step 4: Qwen 生成最终题目
    └─→ qwen_client.generate_questions()
        └─→ 用 RAG + WebSearch 参考生成 20 道题
```

---

## 4. 模块设计详情

### 4.1 `bocha_client.py` — Bocha API 封装

**职责**：底层 HTTP 调用，处理认证、重试、错误处理

**关键函数**：

```python
def call_bocha_api(
    query: str,
    config: Dict,
    max_retries: int = 3
) -> List[str]:
    """
    调用 Bocha API 搜索面试题目
    
    Args:
        query (str): 搜索关键词
        config (Dict): 包含以下字段：
            - bocha_api_endpoint: API 端点
            - bocha_api_key: API Key
            - bocha_timeout: 单次请求超时（秒）
            - bocha_max_retries: 失败重试次数
            - bocha_freshness: 时间过滤（oneDay/oneWeek/oneMonth/oneYear/noLimit）
        max_retries (int): 重试次数
    
    Returns:
        List[str]: 搜索到的题目文本列表
    
    Raises:
        ValueError: API Key 无效时抛出
    
    异常处理：
        - 网络超时 / 速率限制 (429)：指数退避重试
        - 无效 API Key (401)：立即抛出 ValueError
        - 其他 HTTP 错误：重试 1 次，失败返回空列表
        - JSON 解析失败：记录警告，返回空列表
    """
```

**实现要点**：
- 认证：`Authorization: Bearer {bocha_api_key}`
- 重试策略：指数退避 (1s, 2s, 4s)
- 结果提取：从 Bocha 响应中提取 `title` 字段（题目文本）
- 日志：INFO 级别记录每次调用，WARNING 记录重试和降级

---

### 4.2 `query_generator.py` — 搜索词生成 [NEW]

**职责**：用 Qwen 根据 JD 和岗位信息生成多个搜索关键词

**关键函数**：

```python
def generate_search_queries(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> List[str]:
    """
    生成 3-5 个不同角度的搜索词用于 Bocha 搜索
    
    Args:
        jd (str): 岗位描述 (Markdown)
        company (str): 公司名称
        position (str): 岗位名称
        prompts (Dict): prompts.yaml 中的 generate_search_queries 部分
        config (Dict): 配置对象
    
    Returns:
        List[str]: 搜索词列表，例如：
            [
                "字节跳动 算法工程师 面试题",
                "推荐系统 技术题库",
                "算法工程师 项目经验考察"
            ]
    
    调用流程：
        1. 使用 qwen_client.call_api() 调用 Qwen
        2. 传入 system prompt 和 user prompt
        3. 解析 JSON 返回值
        4. 返回搜索词列表
    """
```

**实现要点**：
- 调用 `qwen_client.call_api()` 完成 Qwen 请求
- Prompt 从 `prompts.yaml` 的 `generate_search_queries` 部分加载
- 期望返回 JSON 数组：`["词1", "词2", "词3"]`
- 错误处理：JSON 解析失败返回空列表

---

### 4.3 `web_search.py` — WebSearch 流程协调 [MODIFY]

**职责**：协调搜索词生成和 Bocha 并行调用，返回合并的搜索结果

**关键函数**：

```python
def search_interview_questions(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict,
    limit: int = 10
) -> List[str]:
    """
    完整的 WebSearch 工作流：生成搜索词 → 并行调用 Bocha → 合并去重
    
    Args:
        jd (str): 岗位描述
        company (str): 公司名称
        position (str): 岗位名称
        prompts (Dict): Prompt 模板
        config (Dict): 配置对象
        limit (int): 目标返回数量（默认 10-15）
    
    Returns:
        List[str]: 最多 limit 条的题目文本列表
    
    流程：
        1. 调用 query_generator.generate_search_queries()
           → 获得 3-5 个搜索词
        2. 用 ThreadPoolExecutor 并行调用 bocha_client.call_bocha_api()
           → 每个搜索词最多返回 5 条
        3. 合并所有结果 + 去重（保持原始顺序）
        4. 截断到 limit 条返回
    
    并发策略：
        - max_workers = 3（每次最多 3 个并发搜索）
        - 单个搜索失败不中断其他搜索
    
    异常处理：
        - 搜索词生成失败：返回空列表
        - 部分 Bocha 调用失败：继续其他调用
        - 全部调用失败：返回空列表
    """
```

**实现要点**：
- 使用 `concurrent.futures.ThreadPoolExecutor` 并行调用
- `max_workers=3`（可配置）
- 结果去重：`list(dict.fromkeys(results))`
- 日志：记录生成的搜索词、并行调用数、最终返回数量

---

### 4.4 `question_generator.py` — 集成点 [MODIFY]

**改动点**：

```python
# 当前签名
def generate_questions_pool(
    jd: str,
    personality: str,
    company: str,
    position: str,
    prompts: Dict,        # 已有
    config: Dict          # 已有
) -> Tuple[List[Dict], str]:
    
    # 现有流程
    rag_questions = query_similar_questions(...)
    
    # 改动：search_interview_questions 增加 jd 和 prompts 参数
    web_questions = search_interview_questions(
        jd=jd,                    # [新增]
        company=company,
        position=position,
        prompts=prompts,          # [新增]
        config=config,
        limit=config.get("generation", {}).get("web_search_reference_count", 10)
    )
    
    # 继续生成最终题目
    questions = generate_questions(
        jd=jd,
        personality=personality,
        rag_questions=rag_questions,
        web_questions=web_questions,
        company=company,
        position=position,
        prompts=prompts,
        config=config
    )
    
    return questions, summary
```

---

## 5. 配置管理

### 5.1 `config.yaml` 新增配置块

```yaml
# Bocha WebSearch API 配置
bocha:
  enabled: true                    # 是否启用 Bocha WebSearch
  api_endpoint: "https://api.bochaai.com/v1/web-search"
  api_key: "${BOCHA_API_KEY}"      # 从环境变量读取
  timeout: 30                      # 单次请求超时（秒）
  max_retries: 3                   # 失败重试次数
  freshness: "noLimit"             # 搜索时间范围
  max_results_per_query: 5         # 每个搜索词最多返回条数
```

**环境变量**：

```bash
export BOCHA_API_KEY="sk-13124b292238447b87b38a82e4344e38"
```

### 5.2 `prompts.yaml` 新增 Prompt

```yaml
generate_search_queries:
  system: |
    你是一个面试题搜索专家。根据岗位描述和面试官风格，
    生成 3-5 个不同角度的搜索关键词，用于找到相关的真实面试题目。
    
    生成的搜索词应该能够帮助找到：
    1. 该公司的真实面试题目
    2. 该岗位的技术面试题
    3. 项目经验相关的考察题
  
  user: |
    请为以下岗位生成 3-5 个高质量的搜索关键词。
    
    公司: {company}
    岗位: {position}
    
    岗位描述:
    {jd}
    
    返回一个 JSON 数组，格式如下（只返回 JSON，不要其他内容）：
    ["搜索词1", "搜索词2", "搜索词3", ...]
```

---

## 6. 错误处理和降级流程

### 6.1 Bocha API 调用异常

```
调用 Bocha API
    ↓
成功? ──YES──→ 返回结果
    │
    NO
    ↓
异常类型?
    ├─ Timeout / 429 (速率限制)
    │   └─→ 指数退避重试（1s, 2s, 4s）
    │       → 成功? → 返回 / 失败? → 下一步
    │
    ├─ 401 (无效 API Key)
    │   └─→ 立即抛出 ValueError
    │       → examiner.py 捕获，显示错误并退出
    │
    └─ 其他 HTTP 错误 / 网络异常
        └─→ 重试 1 次
            → 成功? → 返回 / 失败? → 返回空列表
                                    + 记录 WARNING 日志
```

### 6.2 WebSearch 流程降级

```
生成搜索词
    ↓
成功? ──NO──→ 返回空列表
    │        → question_generator 继续
    │        → Qwen 仅用 RAG 参考生成
    │
    YES
    ↓
并行调用 Bocha（3-5 个搜索词）
    ↓
部分失败?
    ├─ YES ──→ 继续其他搜索词
    │           → 合并成功的结果
    │           → 截断到 limit 条
    │
    └─ NO
        └─→ 全部成功
            → 合并去重
            → 截断到 limit 条
```

### 6.3 日志输出

| 级别 | 场景 | 示例 |
|------|------|------|
| INFO | 流程进度 | `[流程] Bocha 搜索词：['词1', '词2']` |
| INFO | 调用结果 | `[流程] 获取 12 道 WebSearch 参考题` |
| WARNING | 重试 | `[警告] Bocha API 超时，重试 (1/3)` |
| WARNING | 降级 | `[警告] Bocha 搜索全部失败，继续使用 RAG 参考` |
| ERROR | 致命错误 | `[错误] BOCHA_API_KEY 无效` |

---

## 7. 接口设计

### 7.1 函数签名汇总

#### `bocha_client.call_bocha_api()`
```python
def call_bocha_api(query: str, config: Dict, max_retries: int = 3) -> List[str]:
    """返回题目文本列表"""
```

#### `query_generator.generate_search_queries()`
```python
def generate_search_queries(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> List[str]:
    """返回搜索词列表"""
```

#### `web_search.search_interview_questions()`
```python
def search_interview_questions(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict,
    limit: int = 10
) -> List[str]:
    """返回合并去重后的题目列表"""
```

#### `question_generator.generate_questions_pool()`
```python
def generate_questions_pool(
    jd: str,
    personality: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> Tuple[List[Dict], str]:
    """返回 (题目列表, 流程摘要)"""
```

---

## 8. 数据结构

### 8.1 搜索词列表

```python
[
    "字节跳动 算法工程师 面试题",
    "推荐系统 LLM 技术题库",
    "字节算法 项目经验考察",
    "大模型优化 工程师面试"
]
```

### 8.2 题目文本列表

```python
[
    "请介绍一下你在简历中提到的 XXX 项目，以及你在其中的具体贡献。",
    "在实现 LLM 推荐系统时，如何处理冷启动问题？",
    "如何优化深度学习模型的推理延迟？",
    # ... 更多题目
]
```

### 8.3 最终生成的题目（与现有格式一致）

```python
[
    {
        "id": 1,
        "text": "请介绍一下...",
        "phase": "简历提问",
        "difficulty": "初级",
        "tags": {
            "company": "字节跳动",
            "position": "算法工程师",
            "question_phase": "简历提问",
            "difficulty": "初级"
        }
    },
    # ... 更多题目
]
```

---

## 9. 测试策略

### 9.1 单元测试

**`test_bocha_client.py`**：
- `test_call_bocha_api_success()` — 正常调用，返回题目
- `test_call_bocha_api_with_retry()` — 失败后重试成功
- `test_call_bocha_api_invalid_key()` — 无效 API Key，抛出 ValueError
- `test_call_bocha_api_timeout()` — 超时降级，返回空列表

**`test_query_generator.py`**：
- `test_generate_search_queries()` — 生成搜索词正确格式
- `test_generate_search_queries_variation()` — 不同 JD 生成不同搜索词

**`test_web_search.py`**：
- `test_search_interview_questions()` — 完整流程
- `test_parallel_calls()` — 并行调用正确性
- `test_deduplication()` — 结果去重功能

### 9.2 集成测试

```bash
export BOCHA_API_KEY="sk-..."
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "字节跳动" \
  --position "算法工程师"
```

预期：
- 成功生成 20 道题目
- 输出包含来自 WebSearch 的参考题目
- 日志显示搜索词和调用结果

### 9.3 Mock 策略

- **单元测试**：Mock `requests.post()` 和 `qwen_client.call_api()`
- **集成测试**：使用真实 API Key（需要设置 `BOCHA_API_KEY`）

---

## 10. 依赖

### 10.1 新增依赖

无新增依赖！（已有 `requests` 和 `concurrent.futures`）

### 10.2 现有依赖

- `pyyaml>=6.0` — 配置文件解析
- `requests>=2.28.0` — HTTP 请求（已用于 Qwen）
- `python-dotenv>=0.19` — 环境变量管理

---

## 11. 实现路线图

### Phase 1: 核心模块实现
- [ ] `bocha_client.py` — API 调用 + 重试逻辑
- [ ] `query_generator.py` — 搜索词生成
- [ ] 更新 `config.yaml` 和 `prompts.yaml`
- [ ] 集成 `web_search.py`

### Phase 2: 集成测试
- [ ] 修改 `question_generator.py`
- [ ] 端到端测试
- [ ] 日志检查

### Phase 3: 优化
- [ ] 性能测试
- [ ] 错误处理完善
- [ ] 文档更新

---

## 12. 成功标准

- ✅ 3 个新模块实现完成，无语法/逻辑错误
- ✅ Bocha API 调用成功，返回真实题目
- ✅ 搜索词由 Qwen 智能生成（3-5 个）
- ✅ 并行调用 Bocha，返回 10-15 道题目
- ✅ 错误重试机制工作正常（3 次重试）
- ✅ 无效 API Key 时立即抛错，有效提示
- ✅ 配置通过环境变量注入
- ✅ 单元测试覆盖 80% 以上
- ✅ 集成测试端到端通过
- ✅ 日志输出清晰，便于调试

---

**设计完成**: 2026-04-28  
**下一步**: 实现计划
