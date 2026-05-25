# builder.py
import glob
import json
import numpy as np
import os
import sys
import requests
import yaml
from embed import embed as _embed

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
