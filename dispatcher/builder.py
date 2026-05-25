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
