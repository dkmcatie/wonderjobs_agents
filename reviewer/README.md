# 面试视频评测工具 接口文档

## 目录结构

```
reviewer/
├── reviewer.py     # 主程序
├── prompts.yaml    # Prompt 模板配置
└── README.md       # 本文档
```

---

## 环境依赖

```bash
pip install pyyaml requests
# 系统需安装 ffmpeg
```

---

## 命令行接口

```bash
python reviewer.py \
  --jd          <path>  \
  --resume      <path>  \
  --personality <path>  \
  --video       <path>  \
  --timestamps  <path>  \
  --transcript  <path>  \
  [--output     <path>]
```

### 参数说明

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `--jd` | ✅ | `.md` 文件路径 | 岗位 JD |
| `--resume` | ✅ | `.md` 文件路径 | 候选人简历 |
| `--personality` | ✅ | `.md` 文件路径 | 面试官性格与风格描述 |
| `--video` | ✅ | `.mp4` 文件路径 | 面试录像 |
| `--timestamps` | ✅ | `.txt` 文件路径 | 对话时间戳，每行一段（见下方格式） |
| `--transcript` | ✅ | `.txt` 文件路径 | 面试全程文字记录 |
| `--output` | ❌ | `.md` 文件路径 | 输出报告路径，默认 `review_output.md` |

---

## 输入文件格式

### `--timestamps` 时间戳文件

每行代表一段对话，格式为 `HHMMSS HHMMSS`（起始时间 结束时间），以空格分隔。

```
000010 000130
000130 000320
000320 000510
001200 001545
```

> `000130` = 00:01:30，即第 1 分 30 秒

以 `#` 开头的行视为注释，空行自动跳过。

---

### `--jd` 岗位JD（md格式）

```markdown
# 岗位名称：产品经理

## 职责
- 负责产品规划与需求分析
- ...

## 要求
- 3年以上产品经验
- ...
```

---

### `--personality` 面试官性格（md格式）

```markdown
# 面试官风格

- 偏好直接简洁的回答，不喜欢绕弯子
- 重视候选人的数据思维和结构化表达
- 对紧张情绪接受度较低，期望候选人表现稳定
```

---

### `--transcript` 面试全文（txt格式）

```
面试官：请先做一个自我介绍。
候选人：您好，我叫...
面试官：你之前在XX公司负责什么项目？
候选人：我主要负责...
```

---

## 输出文件格式

输出为 `.md` 文件，包含四个章节：

```
# 面试评测报告
生成时间：2026-04-25 14:30:00

## 一、各片段评测详情
  ### segment_000（00:00:10 ~ 00:01:30）
    #### 语音语调评测 (tone_res_part)
    #### 面部表情评测 (facial_res_part)
  ### segment_001 ...

## 二、非语言维度综合评估 (tone_facial_res)

## 三、内容维度评估 (content_res)

## 四、最终综合评价
```

---

## 内部数据流

```
输入
 ├── video.mp4 + timestamps.txt
 │     └─ ffmpeg 切分 → N 个视频片段
 │           └─ 每段并行:
 │                ├─ voice_tone(视频 + JD)      → tone_res_part
 │                └─ facial_expression(视频 + JD) → facial_res_part
 │
 ├── [所有 tone_res_part + facial_res_part] + JD
 │     └─ final_evaluation                    → tone_facial_res  ┐ 并行
 │                                                                │
 └── transcript.txt + JD                                         │
       └─ text_content                        → content_res      ┘
 
 [tone_facial_res + content_res + JD + personality]
       └─ final_eval                          → 最终综合报告 → output.md
```

---

## Prompt 配置（prompts.yaml）

共 5 个 Prompt，均可在 `prompts.yaml` 中修改，无需改动代码。

| Prompt Key | 输入变量 | 输出变量 | 说明 |
|---|---|---|---|
| `voice_tone` | `{jd}` `{segment_id}` `{time_range}` | `tone_res_part` | 单片段语音语调评测，含 JSON 评分 |
| `facial_expression` | `{jd}` `{segment_id}` `{time_range}` | `facial_res_part` | 单片段面部表情评测，含 JSON 评分 |
| `final_evaluation` | `{jd}` `{tone_results}` `{facial_results}` | `tone_facial_res` | 汇总所有片段非语言评测 |
| `text_content` | `{jd}` `{transcript}` | `content_res` | 全文内容质量评测 |
| `final_eval` | `{jd}` `{personality}` `{tone_facial_res}` `{content_res}` | 最终报告 | 综合四维度出最终评价 |

---

## 错误处理

| 情况 | 行为 |
|------|------|
| 输入文件不存在 | 打印错误信息并退出 |
| ffmpeg 切分失败 | 打印警告，跳过该片段，继续处理剩余片段 |
| API 请求失败（HTTP 非200） | 抛出异常，终止流程 |
| 时间戳行格式错误 | 打印警告，跳过该行 |
| 所有片段均切分失败 | 打印错误并退出 |

---

## 完整调用示例

```bash
python reviewer.py \
  --jd          inputs/job_description.md \
  --resume      inputs/candidate_resume.md \
  --personality inputs/interviewer_style.md \
  --video       inputs/interview_recording.mp4 \
  --timestamps  inputs/timestamps.txt \
  --transcript  inputs/full_transcript.txt \
  --output      outputs/review_report.md
```
