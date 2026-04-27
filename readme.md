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
**状态**：开发中

**功能描述**：
- 输入：岗位 JD、面试官属性档案
- 工具调用：WebSearch、RAG 检索
- 输出：面试题目候选集合（Markdown 格式）

**工作流程**：
1. 分析岗位 JD，提取关键技能和经验要求
2. 调用 WebSearch 搜索行业标准题目
3. 从 RAG 知识库查询历史题目库
4. 根据面试官风格生成定制化题目
5. 输出题目候选 MD 文件

**示例用途**：
```
输入：字节跳动算法岗 JD + 面试官档案
输出：包含 15-20 道算法题目的候选列表
```

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

1️⃣ 出题阶段 (Examiner)
   JD + Personality → WebSearch/RAG → Question Pool

2️⃣ 面试阶段 (Interviewer)
   Question Pool + Candidate → AI Interview Session → Video + Transcript

3️⃣ 评测阶段 (Reviewer)
   Video + Transcript + JD → Multi-Dimensional Analysis → Report.md
   ├─ 语音语调分析
   ├─ 面部表情分析
   ├─ 内容质量评估
   └─ 综合评价
```

---

## 技术栈

- **Python 3.8+**
- **Claude AI API**（通过 Anthropic SDK）
- **FFmpeg**（视频处理）
- **YAML**（配置管理）
- **Markdown**（文档和报告生成）

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
# 设置 Anthropic API Key
export ANTHROPIC_API_KEY="your-api-key-here"
```

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

| 阶段 | 组件 | 状态 | 预计完成 |
|------|------|------|---------|
| Phase 1 | Reviewer（评测系统） | ✅ 完成 | 2026-04 |
| Phase 2 | Examiner（出题系统） | 🔄 进行中 | 2026-05 |
| Phase 3 | Interviewer（面试官） | 📋 规划中 | 2026-06 |
| Phase 4 | 端到端集成 | 📋 规划中 | 2026-07 |

---

## 常见问题

**Q: 如何开始使用？**  
A: 先从 Reviewer 组件开始，按照 [Reviewer 文档](./reviewer/README.md) 的示例运行。

**Q: 需要什么输入文件？**  
A: 所有组件都需要岗位 JD、候选人简历和面试官风格档案。Reviewer 还需要视频和文字记录。

**Q: 如何定制 Prompt？**  
A: 在 `reviewer/prompts.yaml` 中修改 Prompt 模板，无需改动代码。

**Q: 支持哪些语言？**  
A: 目前主要支持中文，英文支持在开发中。

---

## 贡献指南

欢迎提交 Issue 和 PR！

---

## 许可证

MIT License

---

**最后更新**：2026-04-27  
**维护者**：WonderJobs Team