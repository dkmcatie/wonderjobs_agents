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

    top_k = config["routing"]["top_k_for_llm"]
    candidates = [
        {"name": name, "description": index[name].get("description", "")}
        for name, _ in ranked[:top_k]
    ]
    return _llm_fallback(user_input, candidates, gap, config, api_key)


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
