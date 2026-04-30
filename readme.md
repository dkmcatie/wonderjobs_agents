# WonderJobs - AI 智能面试系统

一个基于多智能体（Multi-Agent）架构的全流程面试系统。通过 AI 驱动的面试官、出题系统和评测工具，为企业提供自动化、标准化的候选人评估解决方案。

## 项目概述

WonderJobs 是一个端到端的 AI 面试流程实现，包含以下核心功能：

- 🎯 **智能出题**（Examiner）：基于岗位 JD，自动生成个性化面试题目
- 🎬 **模拟面试**（Interviewer）：AI 面试官与候选人进行真实感的对话
- 📊 **智能评测**（Reviewer）：多维度分析面试视频，生成详细评测报告

---

## 项目结构

```
wonderjobs/
├── examiner/           # [开发中] 智能出题系统
├── interviewer/        # [计划中] AI 面试官
├── reviewer/           # [已完成] 面试评测工具
│   ├── reviewer.py
│   ├── prompts.yaml
│   └── README.md
└── README.md           # 项目文档
```

---

## 核心组件

### 1. 📝 Examiner（智能出题系统）
**状态**：✅ 功能完成（2026-04-30）

**功能描述**：
- 输入：岗位 JD、面试官属性档案
- 核心能力：Qwen 3.5 Flash 内置 WebSearch + RAG 检索
- 输出：20 道定制化面试题目（JSON + Markdown 格式）

**三层出题架构**：
1. **RAG 层**：从历史题目库检索相关参考题（可选）
2. **WebSearch 层**：Qwen 3.5 Flash 内置搜索，找到行业实际题目
3. **LLM 合成层**：根据 JD、候选风格、搜索结果生成最终 20 道题目

**快速开始**：
```bash
cd examiner/
python examiner.py \
  --jd sample_jd.md \
  --personality sample_personality.md \
  --company "TechCorp" \
  --position "Python 后端工程师" \
  --output questions.json
```

**输出示例**：
```json
{
  "metadata": {
    "total_questions": 20,
    "company": "TechCorp",
    "position": "Python 后端工程师"
  },
  "questions": [
    {
      "id": 1,
      "text": "你在字节跳动做高级 Python 工程师...",
      "category": "简历提问",
      "difficulty": "medium",
      "tags": ["经历深度", "系统理解"]
    }
  ]
}
```

详见 [Examiner 完整文档](./examiner/README.md)

---

### 2. 🎤 Interviewer（AI 面试官）
**状态**：计划中

**预期功能**：
- 实时与候选人进行面试对话
- 根据候选人回答动态调整问题
- 评估候选人的表现和反应
- 生成实时评估数据

---

### 3. 📊 Reviewer（面试评测工具）
**状态**：已完成 ✅

**功能描述**：
从面试视频、录音和文字记录中提取多维度评测数据：

| 维度 | 说明 |
|------|------|
| 🎵 **语音语调** | 节奏、语速、清晰度、自信度 |
| 😊 **面部表情** | 面部反应、眼神接触、自然度 |
| 💬 **内容质量** | 答案完整度、逻辑性、岗位匹配度 |
| 🎯 **综合评价** | 整体表现、岗位适配度、建议反馈 |

**快速开始**：
```bash
cd reviewer/
python reviewer.py \
  --jd          job_description.md \
  --resume      candidate_resume.md \
  --personality interviewer_style.md \
  --video       interview_video.mp4 \
  --timestamps  timestamps.txt \
  --transcript  transcript.txt \
  --output      report.md
```

详见 [Reviewer 完整文档](./reviewer/README.md)

---

## 工作流示意图

```
┌─────────────────────────────────────────────────────────────┐
│                      完整面试流程                             │
└─────────────────────────────────────────────────────────────┘

1️⃣ 出题阶段 (Examiner) ✅ 已完成
   ┌─────────────────────────────────────────┐
   │ JD + Personality + Candidate Resume      │
   │          ↓                                │
   │ Step 1: RAG 查询（历史题库）              │
   │ Step 2: WebSearch（Qwen 3.5内置搜索）     │
   │ Step 3: LLM 合成（生成20道定制题）       │
   │          ↓                                │
   │    20 Questions (JSON + Markdown)        │
   └─────────────────────────────────────────┘

2️⃣ 面试阶段 (Interviewer) 📋 规划中
   Question Pool + Candidate → AI Interview Session → Video + Transcript

3️⃣ 评测阶段 (Reviewer) ✅ 已完成
   Video + Transcript + JD → Multi-Dimensional Analysis → Report.md
   ├─ 语音语调分析
   ├─ 面部表情分析
   ├─ 内容质量评估
   └─ 综合评价
```

---

## 技术栈

### 核心技术
- **Python 3.8+** - 主编程语言
- **Qwen 3.5 Flash** - 智能出题和 WebSearch 能力
- **Aliyun DashScope API** - 大语言模型调用接口

### 工具和库
- **FFmpeg** - 视频处理
- **YAML** - 配置管理
- **Markdown** - 文档和报告生成
- **requests** - HTTP 客户端
- **unittest** - 单元测试框架

### 架构特点
- **三层出题架构**：RAG + WebSearch + LLM 合成
- **并发处理**：ThreadPoolExecutor 用于并行任务
- **配置管理**：YAML 统一配置，支持环境变量注入
- **错误处理**：完善的异常捕获和优雅降级

---

## 环境配置

### 依赖安装

```bash
# 安装 Python 包
pip install -r requirements.txt

# 系统依赖（macOS）
brew install ffmpeg

# 系统依赖（Ubuntu/Debian）
sudo apt-get install ffmpeg
```

### API 密钥配置

```bash
# 设置 Aliyun Qwen API Key（必需）
export ALIYUN_API_KEY="your-qwen-api-key-here"

# 可选：Bocha WebSearch API Key（已弃用，使用 Qwen 内置 WebSearch）
# export BOCHA_API_KEY="your-bocha-api-key-here"
```

**获取 API Key**：
- [Aliyun DashScope 控制台](https://dashscope.aliyuncs.com/) - 获取 Qwen API Key

---

## 使用指南

### 快速体验

#### 仅测试 Reviewer 组件
```bash
cd reviewer/
python reviewer.py \
  --jd          samples/job_description.md \
  --resume      samples/resume.md \
  --personality samples/personality.md \
  --video       samples/interview.mp4 \
  --timestamps  samples/timestamps.txt \
  --transcript  samples/transcript.txt
```

---

## 组件详细文档

- 📖 [Reviewer 组件文档](./reviewer/README.md) - 包含完整 API 参考和示例
- 📋 Examiner 文档（开发中）
- 🎤 Interviewer 文档（开发中）

---

## 开发路线图

| 阶段 | 组件 | 状态 | 完成时间 |
|------|------|------|---------|
| Phase 1 | Reviewer（评测系统） | ✅ 完成 | 2026-04 |
| Phase 2 | Examiner（出题系统） | ✅ 完成 | 2026-04-30 |
| Phase 3 | Interviewer（面试官） | 📋 规划中 | 2026-06 |
| Phase 4 | 端到端集成 | 📋 规划中 | 2026-07 |

### Phase 2 成就
- ✅ Qwen 3.5 Flash WebSearch 集成
- ✅ 三层出题架构（RAG + WebSearch + LLM 合成）
- ✅ 20 道定制化题目生成
- ✅ JSON + Markdown 双格式输出
- ✅ 12 个单元测试（全部通过）
- ✅ 完善的错误处理和优雅降级

---

## 常见问题

**Q: 如何快速体验系统？**  
A: 运行 Examiner 生成题目（最快）：
```bash
export ALIYUN_API_KEY="your-api-key"
cd examiner/
python examiner.py --jd sample_jd.md --personality sample_personality.md \
  --company "TechCorp" --position "Python 后端工程师"
```

**Q: Examiner 需要什么输入？**  
A: 必需：岗位 JD（Markdown）+ 面试官风格档案（Markdown）  
可选：候选人简历（用于定制题目）

**Q: 输出格式是什么？**  
A: JSON 格式包含题目 ID、文本、难度、分类标签等；Markdown 格式便于阅读。

**Q: 如何定制 Prompt？**  
A: 在 `examiner/prompts.yaml` 中修改 Prompt 模板，无需改动代码。

**Q: WebSearch 如何工作？**  
A: Qwen 3.5 Flash 内置 WebSearch，自动搜索行业真实题目，无需额外 API。

**Q: 支持哪些语言？**  
A: 目前主要支持中文，英文支持在开发中。

**Q: 如何运行测试？**  
A: 
```bash
python3 -m unittest tests.test_web_search -v
```

**Q: API 超时怎么办？**  
A: 检查网络连接和 API Key，或增加超时时间（config.yaml 中的 timeout）。

---

## 贡献指南

欢迎提交 Issue 和 PR！

---

## 许可证

MIT License

---

**最后更新**：2026-04-30  
**维护者**：WonderJobs Team

---

## 📈 最近更新

### 2026-04-30
- ✅ **Qwen 3.5 Flash WebSearch 集成完成**
  - 替换原 Bocha API，使用 Qwen 内置搜索能力
  - 简化架构：从 N+1 API 调用 → 1 次 Qwen 调用
  - 性能提升：减少网络往返，降低成本
  
- ✅ **测试覆盖率 100%**
  - 12 个单元测试全部通过
  - 完善的异常处理和优雅降级
  
- ✅ **文档更新**
  - 更新 README 反映最新进展
  - 完整的 API 文档和使用示例

### 2026-04-28
- ✅ 删除内部文档，准备公开发布
- ✅ 添加 .gitignore 和生产就绪检查