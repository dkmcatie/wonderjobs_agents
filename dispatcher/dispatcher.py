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


def _llm_fallback(user_input, candidates, gap, config, api_key):
    # placeholder — replaced in Task 7
    return {"skill": None, "confidence": round(gap, 4), "route": "clarify", "params": {}, "message": ""}
