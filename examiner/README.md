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

```bash
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "字节跳动" \
  --position "广告大模型算法工程师" \
  --output outputs/questions.json
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

### WebSearch 配置（未来启用）

```yaml
web_search:
  enabled: false
  provider: "serpapi"
  api_key: "${WEB_SEARCH_API_KEY}"
```

### RAG 配置（未来启用）

```yaml
rag:
  enabled: false
```

---

## 开发指南

### 项目结构

```
examiner/
├── examiner.py              # 主入口
├── prompts.yaml             # Qwen prompt 模板
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖
├── README.md                # 本文档
├── modules/
│   ├── qwen_client.py       # Qwen API 调用
│   ├── rag_client.py        # RAG 查询（当前模拟）
│   ├── web_search.py        # WebSearch（当前禁用）
│   └── question_generator.py  # 协调生成流程
└── utils/
    ├── file_handler.py      # 文件读写
    ├── validators.py        # 输入验证
    └── formatters.py        # 输出格式化
```

### 扩展点

1. **RAG 集成**: 在 `rag_client._query_from_rag_service()` 中接入真实 RAG 服务
2. **WebSearch 集成**: 在 `web_search._search_with_api()` 中接入搜索 API
3. **多语言支持**: 扩展 prompts.yaml，添加多语言 prompt
4. **题目库管理**: 将生成的题目存储回 RAG 知识库

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
