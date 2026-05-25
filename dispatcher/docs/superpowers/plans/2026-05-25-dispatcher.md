# Dispatcher 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 MoE-inspired 的 skill 路由系统，接收用户自然语言输入，通过向量路由 + LLM fallback 两级架构决定调用哪个 skill。

**Architecture:** 离线阶段（builder.py）读取 skill YAML、生成示例 query、计算 embedding 质心并保存索引；在线阶段（dispatcher.py）embed 用户输入后与所有质心算 cosine similarity，gap 大则直接路由，gap 小则调 LLM 精排，scores 全低则返回 unknown。

**Tech Stack:** Python 3.8+, requests, numpy, pyyaml, pytest（测试），DashScope API（embedding + LLM）

---

## 文件结构

```
dispatcher/
├── skills/                      # Skill 定义
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
├── index/                       # 离线构建的向量索引（gitignore）
│   └── skill_index.json
├── tests/
│   ├── test_embed.py
│   ├── test_builder.py
│   └── test_dispatcher.py
├── embed.py                     # DashScope embedding 封装
├── builder.py                   # 离线索引构建
├── dispatcher.py                # 在线路由逻辑
├── config.yaml                  # 配置
└── requirements.txt
```

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `skills/` 目录（空）
- Create: `index/` 目录（空，加 .gitkeep）
- Create: `tests/` 目录（空）

- [ ] **Step 1: 创建 requirements.txt**

```
requests>=2.28.0
numpy>=1.24.0
pyyaml>=6.0
pytest>=7.0.0
```

- [ ] **Step 2: 创建 config.yaml**

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

builder:
  examples_per_skill: 30
  skills_dir: skills
  index_path: index/skill_index.json
```

- [ ] **Step 3: 创建目录和占位文件**

```bash
mkdir -p skills index tests
touch index/.gitkeep tests/__init__.py
```

- [ ] **Step 4: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.yaml index/.gitkeep tests/__init__.py
git commit -m "feat: scaffold dispatcher project structure"
```

---

### Task 2: 10 个 Skill YAML Manifests

**Files:**
- Create: `skills/web_search.yaml`
- Create: `skills/write_email.yaml`
- Create: `skills/translate.yaml`
- Create: `skills/summarize.yaml`
- Create: `skills/write_code.yaml`
- Create: `skills/debug_code.yaml`
- Create: `skills/create_image.yaml`
- Create: `skills/schedule_meeting.yaml`
- Create: `skills/analyze_data.yaml`
- Create: `skills/answer_question.yaml`

- [ ] **Step 1: 创建 skills/web_search.yaml**

```yaml
name: web_search
description: 搜索网络信息，查询实时数据、新闻、天气等
parameters:
  query: "搜索关键词"
examples:
  - "帮我查一下今天北京的天气"
  - "搜一下最新的 iPhone 价格"
  - "查询一下今天的 A 股行情"
  - "帮我找一下附近的咖啡店"
  - "搜索一下 Python 最新版本"
```

- [ ] **Step 2: 创建 skills/write_email.yaml**

```yaml
name: write_email
description: 撰写各类邮件，包括工作邮件、请假邮件、感谢信等
parameters:
  purpose: "邮件用途"
  recipient: "收件人（可选）"
  tone: "语气，如正式/轻松（可选）"
examples:
  - "帮我写一封请假邮件"
  - "写一封感谢客户的邮件"
  - "帮我起草一封项目进展汇报邮件"
  - "写一封拒绝 offer 的邮件"
  - "帮我写一封催款邮件"
```

- [ ] **Step 3: 创建 skills/translate.yaml**

```yaml
name: translate
description: 翻译文本，支持中英文及其他主流语言互译
parameters:
  text: "需要翻译的文本"
  target_language: "目标语言（可选，默认英文）"
examples:
  - "把这段话翻译成英文"
  - "帮我翻译一下这个英文合同"
  - "这句日语是什么意思"
  - "用中文解释一下这段英文"
  - "翻译成法语：你好世界"
```

- [ ] **Step 4: 创建 skills/summarize.yaml**

```yaml
name: summarize
description: 总结文章、文档或长文本的核心内容，提炼要点
parameters:
  text: "需要总结的内容"
  length: "摘要长度，如简短/详细（可选）"
examples:
  - "帮我总结一下这篇文章"
  - "把这份报告提炼成三个要点"
  - "这段话太长了，帮我压缩一下"
  - "给我一个这本书的内容概要"
  - "把会议记录总结成行动项"
```

- [ ] **Step 5: 创建 skills/write_code.yaml**

```yaml
name: write_code
description: 编写新的代码片段、函数、脚本或完整程序
parameters:
  task: "需要实现的功能描述"
  language: "编程语言（可选）"
examples:
  - "帮我写一个快速排序算法"
  - "用 Python 实现一个文件读取脚本"
  - "写一个 React 登录表单组件"
  - "帮我写一个爬虫抓取商品价格"
  - "实现一个二分查找函数"
```

- [ ] **Step 6: 创建 skills/debug_code.yaml**

```yaml
name: debug_code
description: 调试已有代码，定位错误原因并给出修复方案
parameters:
  code: "有问题的代码"
  error: "报错信息（可选）"
examples:
  - "这段代码为什么报错"
  - "帮我看看这个 bug 在哪"
  - "IndexError 是什么原因"
  - "我的代码跑不起来，帮我检查一下"
  - "这个函数返回了错误的结果，帮我 debug"
```

- [ ] **Step 7: 创建 skills/create_image.yaml**

```yaml
name: create_image
description: 根据描述生成图片，支持各类风格和主题
parameters:
  prompt: "图片描述"
  style: "图片风格（可选）"
examples:
  - "帮我生成一张日落海边的风景图"
  - "画一只可爱的卡通猫"
  - "生成一张科技感的背景图"
  - "创作一幅水墨风格的山水画"
  - "帮我做一张简约风格的 PPT 封面图"
```

- [ ] **Step 8: 创建 skills/schedule_meeting.yaml**

```yaml
name: schedule_meeting
description: 安排会议、日程提醒或日历事件
parameters:
  title: "会议主题"
  time: "时间"
  participants: "参与者（可选）"
examples:
  - "帮我安排明天下午三点的周会"
  - "约一个下周五的项目评审会议"
  - "设置一个每天早上九点的提醒"
  - "帮我把这个会议推迟到下周"
  - "安排一个和客户的视频会议"
```

- [ ] **Step 9: 创建 skills/analyze_data.yaml**

```yaml
name: analyze_data
description: 分析表格数据、统计数据或数据集，提供洞察和可视化建议
parameters:
  data: "数据内容或描述"
  question: "分析目标（可选）"
examples:
  - "帮我分析一下这份销售数据表格"
  - "这些数字有什么规律"
  - "计算一下这组数据的平均值和方差"
  - "帮我做一个月度趋势分析"
  - "这份 CSV 文件里哪个产品卖得最好"
```

- [ ] **Step 10: 创建 skills/answer_question.yaml**

```yaml
name: answer_question
description: 回答知识性问题，解释概念、原理或历史事件
parameters:
  question: "问题内容"
examples:
  - "量子计算是什么原理"
  - "法国大革命是什么时候发生的"
  - "解释一下什么是机器学习"
  - "黑洞是怎么形成的"
  - "相对论是什么意思"
```

- [ ] **Step 11: Commit**

```bash
git add skills/
git commit -m "feat: add 10 skill manifests"
```

---

### Task 3: Embedding 工具模块

**Files:**
- Create: `embed.py`
- Create: `tests/test_embed.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_embed.py
from unittest.mock import patch, MagicMock
from embed import embed

def test_embed_single_text():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]
    }
    with patch("requests.post", return_value=mock_resp):
        result = embed(["hello"], api_key="test-key")
    assert result == [[0.1, 0.2, 0.3]]

def test_embed_multiple_texts_preserves_order():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]
    }
    with patch("requests.post", return_value=mock_resp):
        result = embed(["foo", "bar"], api_key="test-key")
    assert result[0] == [1.0, 0.0]
    assert result[1] == [0.0, 1.0]
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_embed.py -v
```

Expected: `ModuleNotFoundError: No module named 'embed'`

- [ ] **Step 3: 实现 embed.py**

```python
import requests

API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def embed(texts: list, api_key: str, model: str = "text-embedding-v3") -> list:
    response = requests.post(
        f"{API_BASE}/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "input": texts},
    )
    response.raise_for_status()
    data = response.json()["data"]
    ordered = sorted(data, key=lambda x: x["index"])
    return [item["embedding"] for item in ordered]
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_embed.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add embed.py tests/test_embed.py
git commit -m "feat: add DashScope embedding utility"
```

---

### Task 4: Builder — 读取 Skills 并生成 Examples

**Files:**
- Create: `builder.py`
- Create: `tests/test_builder.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_builder.py
import os
import yaml
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from builder import load_skills, generate_examples

def test_load_skills_reads_all_yaml_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["skill_a", "skill_b"]:
            with open(os.path.join(tmpdir, f"{name}.yaml"), "w") as f:
                yaml.dump({"name": name, "description": f"desc {name}", "parameters": {}, "examples": []}, f)
        skills = load_skills(tmpdir)
    assert len(skills) == 2
    names = {s["name"] for s in skills}
    assert names == {"skill_a", "skill_b"}

def test_load_skills_returns_examples_when_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "s.yaml"), "w") as f:
            yaml.dump({"name": "s", "description": "d", "parameters": {}, "examples": ["do x"]}, f)
        skills = load_skills(tmpdir)
    assert skills[0]["examples"] == ["do x"]

def test_generate_examples_calls_llm_and_parses_lines():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "示例一\n示例二\n示例三"}}]
    }
    with patch("requests.post", return_value=mock_resp):
        examples = generate_examples(
            {"name": "web_search", "description": "搜索网络"},
            api_key="test",
            model="qwen-plus",
            n=3,
        )
    assert examples == ["示例一", "示例二", "示例三"]
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_builder.py -v
```

Expected: `ModuleNotFoundError: No module named 'builder'`

- [ ] **Step 3: 实现 load_skills 和 generate_examples**

```python
# builder.py
import glob
import json
import os
import requests
import yaml

API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def load_skills(skills_dir: str) -> list:
    skills = []
    for path in sorted(glob.glob(os.path.join(skills_dir, "*.yaml"))):
        with open(path) as f:
            skills.append(yaml.safe_load(f))
    return skills


def generate_examples(skill: dict, api_key: str, model: str, n: int = 30) -> list:
    prompt = (
        f'你是一个普通用户，想使用名为 "{skill["name"]}" 的功能，'
        f'它的描述是："{skill["description"]}"。\n'
        f"请生成 {n} 条不同的用户输入句子来触发这个功能。每行一条，不要编号，不要解释。"
    )
    response = requests.post(
        f"{API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return [line.strip() for line in content.strip().splitlines() if line.strip()]
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_builder.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add builder.py tests/test_builder.py
git commit -m "feat: add skill loader and example generator"
```

---

### Task 5: Builder — 计算质心并保存索引

**Files:**
- Modify: `builder.py`（新增 `compute_centroid`, `build_index`, `main`）
- Modify: `tests/test_builder.py`（新增测试）

- [ ] **Step 1: 追加失败测试**

在 `tests/test_builder.py` 末尾追加：

```python
import numpy as np
from builder import compute_centroid, build_index

def test_compute_centroid_averages_vectors():
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    result = compute_centroid(vectors)
    assert result == pytest.approx([0.5, 0.5])

def test_compute_centroid_single_vector():
    assert compute_centroid([[0.3, 0.7]]) == pytest.approx([0.3, 0.7])

def test_build_index_returns_centroid_per_skill():
    skills = [
        {"name": "skill_a", "description": "do a", "parameters": {}, "examples": ["a1", "a2"]},
    ]
    fake_embeddings = [[1.0, 0.0], [0.0, 1.0]]
    with patch("builder._embed", return_value=fake_embeddings):
        index = build_index(skills, api_key="test", config={
            "embedding": {"model": "text-embedding-v3"},
            "llm_fallback": {"model": "qwen-plus"},
            "builder": {"examples_per_skill": 30},
        })
    assert "skill_a" in index
    assert index["skill_a"]["centroid"] == pytest.approx([0.5, 0.5])
    assert index["skill_a"]["description"] == "do a"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_builder.py::test_compute_centroid_averages_vectors -v
```

Expected: `ImportError: cannot import name 'compute_centroid'`

- [ ] **Step 3: 实现 compute_centroid, build_index, main**

在 `builder.py` 末尾追加：

```python
import numpy as np
import sys
from embed import embed as _embed


def compute_centroid(vectors: list) -> list:
    return np.array(vectors).mean(axis=0).tolist()


def build_index(skills: list, api_key: str, config: dict) -> dict:
    emb_model = config["embedding"]["model"]
    llm_model = config["llm_fallback"]["model"]
    n = config["builder"]["examples_per_skill"]
    index = {}
    for skill in skills:
        examples = skill.get("examples") or []
        if not examples:
            examples = generate_examples(skill, api_key=api_key, model=llm_model, n=n)
        vectors = _embed(examples, api_key=api_key, model=emb_model)
        index[skill["name"]] = {
            "centroid": compute_centroid(vectors),
            "description": skill.get("description", ""),
            "examples": examples,
        }
    return index


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    api_key = os.environ[config["embedding"]["api_key_env"]]
    skills = load_skills(config["builder"]["skills_dir"])
    print(f"Building index for {len(skills)} skills...")
    index = build_index(skills, api_key=api_key, config=config)

    index_path = config["builder"]["index_path"]
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Index saved to {index_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行所有 builder 测试**

```bash
pytest tests/test_builder.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add builder.py tests/test_builder.py
git commit -m "feat: add centroid computation and index builder"
```

---

### Task 6: Dispatcher — 向量路由

**Files:**
- Create: `dispatcher.py`
- Create: `tests/test_dispatcher.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dispatcher.py
import pytest
from unittest.mock import patch
from dispatcher import cosine_similarity, route

def test_cosine_similarity_identical_vectors():
    a = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, a) == pytest.approx(1.0)

def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

def test_route_vector_path_high_confidence():
    index = {
        "write_code": {"centroid": [1.0, 0.0, 0.0], "description": "编写代码"},
        "translate":  {"centroid": [0.0, 1.0, 0.0], "description": "翻译文本"},
        "web_search": {"centroid": [0.0, 0.0, 1.0], "description": "搜索网络"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    with patch("dispatcher.embed", return_value=[[0.99, 0.05, 0.05]]):
        result = route("帮我写代码", index, config, api_key="test")
    assert result["skill"] == "write_code"
    assert result["route"] == "vector"
    assert result["confidence"] > 0

def test_route_unknown_when_all_scores_low():
    index = {
        "write_code": {"centroid": [1.0, 0.0], "description": "编写代码"},
        "translate":  {"centroid": [0.0, 1.0], "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    with patch("dispatcher.embed", return_value=[[0.1, 0.1]]):
        result = route("xyzxyz", index, config, api_key="test")
    assert result["route"] == "unknown"
    assert result["skill"] is None
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_dispatcher.py -v
```

Expected: `ModuleNotFoundError: No module named 'dispatcher'`

- [ ] **Step 3: 实现 cosine_similarity 和向量路由**

```python
# dispatcher.py
import json
import os
import sys
import numpy as np
import requests
import yaml
from embed import embed

API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def cosine_similarity(a: list, b: list) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def route(user_input: str, index: dict, config: dict, api_key: str) -> dict:
    query_vec = embed([user_input], api_key=api_key, model=config["embedding"]["model"])[0]

    scores = {
        name: cosine_similarity(query_vec, data["centroid"])
        for name, data in index.items()
    }
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1_name, top1_score = ranked[0]
    top2_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if top1_score < config["routing"]["min_score_threshold"]:
        return {
            "skill": None,
            "confidence": round(top1_score, 4),
            "route": "unknown",
            "params": {},
            "message": "我不确定你想做什么，能描述得更具体吗？",
        }

    gap = top1_score - top2_score
    if gap >= config["routing"]["gap_threshold"]:
        return {
            "skill": top1_name,
            "confidence": round(gap, 4),
            "route": "vector",
            "params": {},
            "message": "",
        }

    # LLM fallback — implemented in Task 7
    top_k = config["routing"]["top_k_for_llm"]
    candidates = [
        {"name": name, "description": index[name].get("description", "")}
        for name, _ in ranked[:top_k]
    ]
    return _llm_fallback(user_input, candidates, gap, config, api_key)


def _llm_fallback(user_input, candidates, gap, config, api_key):
    # placeholder replaced in Task 7
    return {"skill": None, "confidence": round(gap, 4), "route": "clarify", "params": {}, "message": ""}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_dispatcher.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add dispatcher.py tests/test_dispatcher.py
git commit -m "feat: add cosine similarity and vector routing"
```

---

### Task 7: Dispatcher — LLM Fallback

**Files:**
- Modify: `dispatcher.py`（实现 `llm_rerank`，替换 `_llm_fallback` placeholder）
- Modify: `tests/test_dispatcher.py`（追加 fallback 测试）

- [ ] **Step 1: 追加失败测试**

在 `tests/test_dispatcher.py` 末尾追加：

```python
from dispatcher import llm_rerank

def test_llm_rerank_returns_skill_when_confident():
    mock_resp = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"skill": "debug_code", "confident": true, "reason": "用户提到报错"}'}}]
    }
    candidates = [
        {"name": "write_code", "description": "编写代码"},
        {"name": "debug_code", "description": "调试代码"},
    ]
    with patch("requests.post", return_value=mock_resp):
        result = llm_rerank("这段代码报错了", candidates, api_key="test", model="qwen-plus")
    assert result["skill"] == "debug_code"
    assert result["confident"] is True

def test_route_uses_llm_when_gap_small():
    index = {
        "write_code": {"centroid": [1.0, 0.01], "description": "编写代码"},
        "debug_code": {"centroid": [0.99, 0.0],  "description": "调试代码"},
        "translate":  {"centroid": [0.0,  1.0],  "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    llm_result = {"skill": "debug_code", "confident": True, "reason": "提到报错"}
    with patch("dispatcher.embed", return_value=[[0.99, 0.01]]), \
         patch("dispatcher.llm_rerank", return_value=llm_result):
        result = route("这段代码报错了", index, config, api_key="test")
    assert result["skill"] == "debug_code"
    assert result["route"] == "llm_fallback"

def test_route_returns_clarify_when_llm_not_confident():
    index = {
        "write_code": {"centroid": [1.0, 0.01], "description": "编写代码"},
        "debug_code": {"centroid": [0.99, 0.0],  "description": "调试代码"},
        "translate":  {"centroid": [0.0,  1.0],  "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    llm_result = {"skill": "write_code", "confident": False, "reason": "不确定"}
    with patch("dispatcher.embed", return_value=[[0.99, 0.01]]), \
         patch("dispatcher.llm_rerank", return_value=llm_result):
        result = route("代码", index, config, api_key="test")
    assert result["route"] == "clarify"
    assert result["skill"] is None
    assert "write_code" in result["message"] or "debug_code" in result["message"]
```

- [ ] **Step 2: 运行新测试，确认失败**

```bash
pytest tests/test_dispatcher.py::test_llm_rerank_returns_skill_when_confident -v
```

Expected: `ImportError: cannot import name 'llm_rerank'`

- [ ] **Step 3: 实现 llm_rerank 并替换 _llm_fallback**

将 `dispatcher.py` 中的 `_llm_fallback` 函数替换为：

```python
def llm_rerank(user_input: str, candidates: list, api_key: str, model: str) -> dict:
    lines = "\n".join(
        f"{i+1}. {c['name']}: {c['description']}" for i, c in enumerate(candidates)
    )
    prompt = (
        f'用户说："{user_input}"\n\n'
        f"以下是候选功能：\n{lines}\n\n"
        '请选择最合适的一个，只输出 JSON，格式：\n'
        '{"skill": "<name>", "confident": true/false, "reason": "<原因>"}\n'
        "如无法确定，将 confident 设为 false。"
    )
    response = requests.post(
        f"{API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def _llm_fallback(user_input: str, candidates: list, gap: float, config: dict, api_key: str) -> dict:
    result = llm_rerank(
        user_input,
        candidates,
        api_key=api_key,
        model=config["llm_fallback"]["model"],
    )
    if result.get("confident", False):
        return {
            "skill": result["skill"],
            "confidence": round(gap, 4),
            "route": "llm_fallback",
            "params": {},
            "message": "",
        }
    options = " / ".join(c["name"] for c in candidates)
    return {
        "skill": None,
        "confidence": round(gap, 4),
        "route": "clarify",
        "params": {},
        "message": f"你是想要：{options}？",
    }
```

- [ ] **Step 4: 运行全部 dispatcher 测试**

```bash
pytest tests/test_dispatcher.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add dispatcher.py tests/test_dispatcher.py
git commit -m "feat: add LLM fallback and clarify routing"
```

---

### Task 8: CLI 入口

**Files:**
- Modify: `dispatcher.py`（追加 `main` 函数）

- [ ] **Step 1: 在 dispatcher.py 末尾追加 main**

```python
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Dispatcher: route user input to a skill")
    parser.add_argument("input", help="用户输入")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--index", default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    index_path = args.index or config["builder"]["index_path"]
    if not os.path.exists(index_path):
        print(f"Error: index not found at {index_path}. Run: python builder.py", file=sys.stderr)
        sys.exit(1)

    with open(index_path) as f:
        index = json.load(f)

    api_key = os.environ[config["embedding"]["api_key_env"]]
    result = route(args.input, index, config, api_key=api_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 构建索引（需要真实 API key）**

```bash
export DASHSCOPE_API_KEY="your-key-here"
python builder.py
```

Expected: `Building index for 10 skills... Index saved to index/skill_index.json`

- [ ] **Step 3: 测试几个典型输入**

```bash
python dispatcher.py "帮我写一个排序算法"
# Expected: skill=write_code, route=vector

python dispatcher.py "这段代码报错了"
# Expected: skill=debug_code, route=vector or llm_fallback

python dispatcher.py "量子计算是什么原理"
# Expected: skill=answer_question, route=vector

python dispatcher.py "帮我查一下今天天气"
# Expected: skill=web_search, route=vector
```

- [ ] **Step 4: 运行全部测试确认无回归**

```bash
pytest tests/ -v
```

Expected: `13 passed`

- [ ] **Step 5: Commit**

```bash
git add dispatcher.py
git commit -m "feat: add CLI entry point for dispatcher"
```
