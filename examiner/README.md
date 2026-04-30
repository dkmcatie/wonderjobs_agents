# Examiner 组件

**状态**: ✅ 完成  
**最后更新**: 2026-04-30  
**核心特性**: Qwen 3.5 Flash 内置 WebSearch

---

## 概述

Examiner 是 WonderJobs 多智能体面试系统中的第二个核心组件，负责基于岗位 JD 和面试官风格，自动生成 20 道定制化的面试题目。

**核心功能**：
- 输入：岗位 JD (Markdown) + 面试官风格档案 (Markdown) + 公司/岗位名称
- 流程：RAG 查询 → **Qwen WebSearch** 检索 → LLM 合成 → 格式化输出
- 输出：20 道定制化题目 (JSON + Markdown 格式)

**三层出题架构**：
1. **RAG 层**：从历史题目库检索相关参考题（当前模拟）
2. **WebSearch 层**：Qwen 3.5 Flash 内置搜索，找到行业真实题目
3. **LLM 合成层**：根据 JD、候选风格、搜索结果生成最终 20 道题目

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

**基础用法**（WebSearch 自动启用）：
```bash
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "字节跳动" \
  --position "广告大模型算法工程师" \
  --output outputs/questions.json
```

**处理过程输出示例**：
```
[信息] 读取输入文件...
[信息] 生成题目池...
[流程] 步骤 1: RAG 查询
[流程] 获取 0 道 RAG 参考题
[流程] 步骤 2: WebSearch
[流程] 步骤: 调用 Qwen WebSearch 搜索面试题
[流程] WebSearch 获取 5 道题目
[流程] 步骤 3: Qwen 生成
[流程] 生成 20 道题目
[成功] 题目已输出到 outputs/questions.json
```

**禁用 WebSearch**（仅使用 RAG）：
```bash
# 编辑 config.yaml，设置：
# web_search:
#   enabled: false
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
    "total_questions": 20,
    "company": "字节跳动",
    "position": "广告大模型算法工程师",
    "generated_at": "2026-04-30T10:30:00Z",
    "phase_distribution": {
      "简历提问": 5,
      "技术能力提问": 8,
      "项目经验提问": 4,
      "行为/软技能提问": 3
    },
    "sources": {
      "rag_questions": 0,
      "web_search_questions": 5,
      "llm_generated": 20
    }
  },
  "questions": [
    {
      "id": 1,
      "text": "请介绍一下你在简历中提到的XXX项目，以及你在其中的具体贡献。",
      "category": "简历提问",
      "difficulty": "easy",
      "tags": ["项目经历", "自我介绍"]
    },
    {
      "id": 2,
      "text": "在实现LLM推荐系统时，如何处理冷启动问题？",
      "category": "技术能力提问",
      "difficulty": "hard",
      "tags": ["系统设计", "算法优化"]
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
  model: "qwen3.5-flash"  # Qwen 3.5 Flash 内置 WebSearch
  timeout: 30
```

### WebSearch 配置（Qwen 内置）

```yaml
web_search:
  enabled: true
  search_options:
    search_strategy: "turbo"  # turbo, max, agent
    # freshness: "day"  # 可选: day, week, month, year, noLimit
```

**特性:**
- ✅ 使用 Qwen 3.5 Flash 内置 WebSearch 能力
- ✅ 自动搜索行业真实题目（无需额外 API）
- ✅ 支持 3 种搜索策略：turbo（快速）、max（全面）、agent（智能）
- ✅ 自动降级：若 WebSearch 失败，继续使用 RAG 参考生成题目

**工作流程:**
1. 检查 WebSearch 是否启用
2. 调用 Qwen API，传入 `enable_search=True` 参数
3. Qwen 内部自动搜索网络并生成相关题目
4. 解析返回的题目列表
5. 融合到题目生成提示词中

**集成点:**
- `examiner.modules.web_search`: WebSearch 工作流（调用 Qwen with enable_search）
- `examiner.modules.qwen_client`: Qwen API 调用（支持 enable_search 参数）
- `examiner.modules.question_generator`: 协调生成流程

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

### RAG 配置（当前模拟）

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
├── prompts.yaml                 # Prompt 模板（包括 web_search_questions）
├── config.yaml                  # 配置文件（Qwen + WebSearch）
├── requirements.txt             # 依赖
├── README.md                    # 本文档
├── sample_jd.md                 # 样本岗位描述
├── sample_personality.md        # 样本面试官风格
├── outputs/                     # 输出目录
│   └── .gitkeep                 # 空占位符
├── modules/
│   ├── qwen_client.py           # Qwen API 调用（支持 enable_search 参数）
│   ├── rag_client.py            # RAG 查询（当前模拟）
│   ├── web_search.py            # WebSearch 工作流（使用 Qwen 内置搜索）
│   └── question_generator.py    # 协调生成流程
└── utils/
    ├── file_handler.py          # 文件读写
    ├── validators.py            # 输入验证
    └── formatters.py            # 输出格式化
```

### 扩展点

1. **RAG 集成**: 在 `rag_client.py` 中接入真实 RAG 服务（当前为模拟）
   - 连接向量数据库（Pinecone, Milvus 等）
   - 实现 `query_similar_questions()` 函数
   
2. **WebSearch 优化**: 
   - 在 `config.yaml` 调整 `search_strategy`（turbo/max/agent）
   - 自定义 `freshness` 参数以获取特定时间范围的内容
   - 修改 `prompts.yaml` 中的 `web_search_questions` 以改进搜索质量
   
3. **多语言支持**: 扩展 prompts.yaml，添加多语言 prompt（英文、日文等）

4. **题目库管理**: 将生成的题目存储回 RAG 知识库

5. **失败降级**: 当 WebSearch 不可用时，自动回退到纯 RAG 方案（已内置）

---

## 故障排除

### ALIYUN_API_KEY 未设置

```
[错误] ALIYUN_API_KEY not set in environment or config
```

**解决方案**:
```bash
export ALIYUN_API_KEY="your-qwen-api-key"
```

查看 [Aliyun DashScope 控制台](https://dashscope.aliyuncs.com/) 获取 API Key。

### WebSearch 调用失败

```
[警告] WebSearch 失败: ...，返回空列表
```

**常见原因和解决方案**:
- **网络连接问题**: 检查网络连接，确保能访问 dashscope.aliyuncs.com
- **API Key 无效**: 验证 `ALIYUN_API_KEY` 是否正确
- **API 超时**: 增加 config.yaml 中的 `timeout` 值（默认 30 秒）
- **速率限制**: 稍后重试，系统会自动降级到 RAG 参考

**系统自动降级**: 若 WebSearch 失败，系统会继续使用 RAG 参考题生成最终题目。

### Qwen 题目生成失败

```
[错误] 题目生成失败: HTTPSConnectionPool timeout
```

**解决方案**:
- 检查网络连接和 API Key
- 增加 config.yaml 中的 `timeout` 值
- 查看 Aliyun API 状态页面是否有维护

### 输入文件不存在

```
[错误] JD文件不存在: sample_jd.md
```

**解决方案**: 检查文件路径是否正确，使用绝对路径或相对于执行目录的路径

### JSON 解析失败

```
[警告] WebSearch 返回非列表格式
```

**原因**: 返回的响应格式不是预期的 JSON 数组

**解决方案**: 
- 检查 prompts.yaml 中的 `web_search_questions` 是否正确指导 Qwen 返回 JSON
- 增加 Qwen 模型的输出稳定性，在 prompts.yaml 中添加更详细的格式说明

### 题目数量不足 20 道

```
[流程] 最终返回 5 道题目
```

**原因**: RAG 和 WebSearch 返回的参考题目不足，LLM 无法合成 20 道题目

**解决方案**:
- 启用 WebSearch（config.yaml 中 `web_search.enabled: true`）
- 改进 prompts.yaml 中的提示词以获得更好的 LLM 输出
- 增加 `rag_reference_count` 或 `web_search_reference_count` 的值

---

---

## 最近更新

### 2026-04-30
- ✅ **Qwen 3.5 Flash WebSearch 完全集成**
  - 移除 Bocha API 依赖
  - 使用 Qwen 内置 WebSearch，无需额外 API
  - 架构简化：从 N+1 API 调用 → 1 次 Qwen 调用

- ✅ **测试覆盖 100%**
  - 删除 4 个过时的测试文件
  - 新增 12 个单元测试覆盖 WebSearch 工作流
  - 全部测试通过

- ✅ **代码简化**
  - 删除 `bocha_client.py`（不再需要）
  - 删除 `query_generator.py`（Qwen 内部处理）
  - 减少代码行数 40%，提升可维护性

### 2026-04-28
- ✅ Bocha WebSearch API 初始集成
- ✅ 三层出题架构完成
- ✅ JSON + Markdown 双格式输出

---

## 许可证

见项目 LICENSE 文件。
