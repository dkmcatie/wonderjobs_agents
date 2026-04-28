# Examiner 组件

**状态**: 实现阶段  
**最后更新**: 2026-04-28

---

## 概述

Examiner 是 WonderJobs 多智能体面试系统中的第二个核心组件，负责基于岗位 JD 和面试官风格，自动生成 20 道定制化的面试题目。

**核心功能**：
- 输入：岗位 JD (Markdown) + 面试官风格档案 (Markdown) + 公司/岗位名称
- 流程：RAG 查询 → WebSearch 检索 → Qwen 生成 → 格式化输出
- 输出：20 道定制化题目 (JSON + Markdown 格式)

---

## 快速开始

### 1. 安装依赖

```bash
cd examiner/
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
export ALIYUN_API_KEY="your-aliyun-api-key"
```

### 3. 准备输入文件

创建 JD 和面试官风格档案的 Markdown 文件。

**sample_jd.md**:
```markdown
# 广告大模型算法工程师

## 岗位职责
- 负责大模型在广告系统中的应用...
- 优化推荐算法效率...

## 要求
- 熟悉 Python、深度学习框架
- 有 NLP 或推荐系统经验
```

**sample_personality.md**:
```markdown
# 面试官风格档案

## 提问风格
- 注重实战经验，喜欢深入追问技术细节
- 关注候选人的系统设计能力

## 倾向
- 倾向于开放式问题
- 重视问题解决能力而非死记硬背
```

### 4. 运行 Examiner

基础用法：
```bash
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "字节跳动" \
  --position "广告大模型算法工程师" \
  --output outputs/questions.json
```

启用 Bocha WebSearch：
```bash
export BOCHA_API_KEY="sk-your-key-here"
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "字节跳动" \
  --position "算法工程师"
```

处理过程输出示例：
```
[流程] 步骤 1: 生成搜索词
[流程] 生成 4 个搜索词: ['字节跳动面试题', '推荐系统设计面试', '深度学习工程师面试题', 'LLM应用开发面试']
[流程] 步骤 2: 并行调用 Bocha 搜索
[流程] Bocha API 调用: '字节跳动面试题' (尝试 1/3)
[流程] 搜索词 '字节跳动面试题' 获取 5 道题目
...
[流程] 步骤 3: 去重并截断结果
[流程] 最终返回 12 道题目
```

### 5. 查看结果

- **questions.json**: 结构化的题目数据，便于系统集成
- **questions.md**: 可读的 Markdown 格式，便于人工审查

---

## CLI 参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--jd` | 文件路径 | ✅ | 岗位 JD（Markdown） |
| `--personality` | 文件路径 | ✅ | 面试官风格档案（Markdown） |
| `--company` | 字符串 | ✅ | 公司名称 |
| `--position` | 字符串 | ✅ | 岗位名称 |
| `--output` | 文件路径 | ❌ | 输出文件路径（默认：questions.json） |
| `--config` | 文件路径 | ❌ | 配置文件（默认：config.yaml） |

---

## 输出格式

### questions.json 结构

```json
{
  "metadata": {
    "company": "字节跳动",
    "position": "广告大模型算法工程师",
    "total_questions": 20,
    "generated_at": "2026-04-28T10:30:00Z",
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
**生成时间**: 2026-04-28  
**题目总数**: 20

---

## 简历提问 (5道)

### 1. 初级 - 请介绍一下你在简历中提到的XXX项目...

### 2. 中级 - ...

...

## 技术能力提问 (8道)

### 6. 高级 - 在实现LLM推荐系统时...

...

## 项目经验提问 (4道)

...

## 行为/软技能提问 (3道)

...
```

---

## 配置文件 (config.yaml)

### Qwen API 配置

```yaml
qwen:
  api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "${ALIYUN_API_KEY}"  # 从环境变量读取
  model: "qwen-omni-mini"
  timeout: 30
```

### 题目生成配置

```yaml
generation:
  total_questions: 20
  rag_reference_count: 10
  web_search_reference_count: 5

  phase_distribution:
    简历提问: 5
    技术能力提问: 8
    项目经验提问: 4
    行为/软技能提问: 3
```

### Bocha WebSearch 配置

Bocha WebSearch 已集成到 Examiner 组件中。此功能自动生成多角度搜索词并并行调用 Bocha API 来检索行业参考题目。

**配置:**
```yaml
bocha:
  enabled: true
  api_endpoint: "https://api.bochaai.com/v1/web-search"
  api_key: "${BOCHA_API_KEY}"
  timeout: 30
  max_retries: 3
  freshness: "noLimit"
  max_results_per_query: 5
```

**环境变量设置:**
```bash
export BOCHA_API_KEY="your-bocha-api-key"
```

**特性:**
- 使用 Qwen LLM 自动生成 3-5 个多角度搜索词
- 并行调用 Bocha API（最多 3 个并发连接）
- 从行业真实数据返回 10-15 道参考题目
- 支持失败重试（指数退避：1s, 2s, 4s）
- 自动降级：若 WebSearch 失败，继续使用 RAG 参考生成题目

**工作流程:**
1. 根据 JD、公司名、岗位名生成搜索词（使用 Qwen API）
2. 并行调用 Bocha API 执行搜索
3. 去重并合并搜索结果
4. 融合到题目生成提示词中

**集成点:**
- `examiner.modules.query_generator`: 搜索词生成（使用 Qwen）
- `examiner.modules.bocha_client`: Bocha API 调用与重试逻辑
- `examiner.modules.web_search`: 完整的 WebSearch 工作流

### RAG 配置（未来启用）

```yaml
rag:
  enabled: false  # 当前禁用，后续可接入真实服务
```

---

## 开发指南

### 项目结构

```
examiner/
├── examiner.py                  # 主入口
├── prompts.yaml                 # Qwen prompt 模板
├── config.yaml                  # 配置文件（包括 Bocha 配置）
├── requirements.txt             # 依赖
├── README.md                    # 本文档
├── modules/
│   ├── qwen_client.py           # Qwen API 调用
│   ├── rag_client.py            # RAG 查询（当前模拟）
│   ├── web_search.py            # WebSearch 工作流（Bocha 集成）
│   ├── bocha_client.py          # Bocha API 客户端（含重试逻辑）
│   ├── query_generator.py       # 搜索词生成（使用 Qwen）
│   └── question_generator.py    # 协调生成流程
└── utils/
    ├── file_handler.py          # 文件读写
    ├── validators.py            # 输入验证
    └── formatters.py            # 输出格式化
```

### 扩展点

1. **RAG 集成**: 在 `rag_client._query_from_rag_service()` 中接入真实 RAG 服务（当前为模拟）
2. **Bocha API 优化**: 
   - 调整 `max_workers` 以适应不同的 API 速率限制
   - 自定义 `freshness` 参数以获取最新内容
   - 在 `bocha_client.py` 中扩展响应解析逻辑
3. **搜索词生成优化**: 修改 `prompts.yaml` 中的 `generate_search_queries` 提示词以改进搜索质量
4. **多语言支持**: 扩展 prompts.yaml，添加多语言 prompt（英文、日文等）
5. **题目库管理**: 将生成的题目存储回 RAG 知识库
6. **失败降级**: 当 Bocha API 不可用时，自动回退到纯 RAG 方案

---

## 故障排除

### ALIYUN_API_KEY 未设置

```
[错误] ALIYUN_API_KEY not set in environment or config
```

**解决方案**:
```bash
export ALIYUN_API_KEY="your-key"
```

### BOCHA_API_KEY 未设置

```
[警告] BOCHA_API_KEY not set in environment or config
```

**解决方案**:
```bash
export BOCHA_API_KEY="sk-your-bocha-key"
```

若不设置，系统将自动跳过 WebSearch 阶段，仅使用 RAG 参考生成题目。

### Bocha API 返回 401

```
[错误] Bocha API Key 无效: ...
```

**解决方案**:
- 验证 `BOCHA_API_KEY` 是否正确
- 检查 API Key 是否已过期
- 确保 API Key 有 web-search 权限

### Bocha API 速率限制 (429)

```
[警告] Bocha API 速率限制，等待 2s 后重试...
```

**说明**: 系统会自动进行指数退避重试。如果频繁出现，可在 config.yaml 中减少 `max_results_per_query`。

### Bocha API 超时

```
[警告] Bocha API 超时，等待 2s 后重试...
```

**解决方案**:
- 增加 config.yaml 中的 `timeout` 值
- 检查网络连接质量
- 减少 `max_workers` 以降低并发

### 输入文件不存在

```
[错误] JD文件不存在: sample_jd.md
```

**解决方案**: 检查文件路径是否正确

### Qwen API 调用失败

检查 config.yaml 中的 API 配置是否正确，确保网络连接正常。

---

## 许可证

见项目 LICENSE 文件。
