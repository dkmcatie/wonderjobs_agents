import os
import json
import requests
from typing import List, Dict


def call_api(system_prompt: str, user_prompt: str, config: Dict) -> str:
    qwen_config = config.get("qwen", {})
    api_base = qwen_config.get("api_base")
    api_key = os.getenv("ALIYUN_API_KEY") or qwen_config.get("api_key", "").replace("${ALIYUN_API_KEY}", "")
    model = qwen_config.get("model", "qwen-omni-mini")
    timeout = qwen_config.get("timeout", 30)

    if not api_key or api_key.startswith("${"):
        raise ValueError("ALIYUN_API_KEY not set in environment or config")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    resp = requests.post(f"{api_base}/chat/completions", headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate_questions(
    jd: str,
    personality: str,
    rag_questions: List[Dict],
    web_questions: List[str],
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> List[Dict]:
    system_prompt = prompts["generate_questions"]["system"]
    user_template = prompts["generate_questions"]["user"]

    rag_questions_text = json.dumps(rag_questions, ensure_ascii=False, indent=2)
    web_questions_text = json.dumps(web_questions, ensure_ascii=False, indent=2) if web_questions else "[]"

    user_prompt = user_template.format(
        jd=jd,
        personality=personality,
        company=company,
        position=position,
        rag_questions=rag_questions_text,
        web_questions=web_questions_text
    )

    response = call_api(system_prompt, user_prompt, config)

    try:
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()
        questions = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse Qwen response as JSON: {e}") from e

    if not isinstance(questions, list) or len(questions) != 20:
        raise ValueError(f"Expected exactly 20 questions, got {len(questions) if isinstance(questions, list) else 'non-list'}")

    return questions
