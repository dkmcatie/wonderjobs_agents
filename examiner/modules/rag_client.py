import json
from typing import List, Dict
from modules.qwen_client import call_api


def query_similar_questions(
    company: str,
    position: str,
    phase: str = None,
    count: int = 10,
    prompts: Dict = None,
    config: Dict = None
) -> List[Dict]:
    rag_config = config.get("rag", {}) if config else {}

    if rag_config.get("enabled"):
        return _query_from_rag_service(company, position, phase, count)
    else:
        return _simulate_rag_with_llm(company, position, count, prompts, config)


def _query_from_rag_service(company: str, position: str, phase: str, count: int) -> List[Dict]:
    raise NotImplementedError("RAG service not yet implemented")


def _simulate_rag_with_llm(company: str, position: str, count: int, prompts: Dict, config: Dict) -> List[Dict]:
    if not prompts or "rag_simulate" not in prompts:
        return []

    system_prompt = prompts["rag_simulate"]["system"]
    user_template = prompts["rag_simulate"]["user"]

    user_prompt = user_template.format(company=company, position=position, count=count)

    try:
        response = call_api(system_prompt, user_prompt, config)

        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        questions = json.loads(json_str)

        if not isinstance(questions, list):
            questions = [questions] if isinstance(questions, dict) else []

        return questions[:count]

    except Exception as e:
        print(f"[警告] RAG 模拟失败: {e}，将使用空列表")
        return []
