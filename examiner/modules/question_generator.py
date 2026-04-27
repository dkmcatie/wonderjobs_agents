from typing import List, Dict, Tuple
from modules.rag_client import query_similar_questions
from modules.web_search import search_interview_questions
from modules.qwen_client import generate_questions


def generate_questions_pool(
    jd: str,
    personality: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> Tuple[List[Dict], str]:
    gen_config = config.get("generation", {})
    rag_count = gen_config.get("rag_reference_count", 10)
    web_count = gen_config.get("web_search_reference_count", 5)

    print("[流程] 步骤 1: RAG 查询")
    rag_questions = query_similar_questions(company, position, count=rag_count, prompts=prompts, config=config)
    print(f"[流程] 获取 {len(rag_questions)} 道 RAG 参考题")

    print("[流程] 步骤 2: WebSearch")
    web_questions = search_interview_questions(company, position, limit=web_count, config=config)
    print(f"[流程] 获取 {len(web_questions)} 道 WebSearch 参考题")

    print("[流程] 步骤 3: Qwen 生成")
    questions = generate_questions(
        jd=jd,
        personality=personality,
        rag_questions=rag_questions,
        web_questions=web_questions,
        company=company,
        position=position,
        prompts=prompts,
        config=config
    )
    print(f"[流程] 生成 {len(questions)} 道题目")

    summary = f"RAG 参考: {len(rag_questions)} 道\nWebSearch 参考: {len(web_questions)} 道\n最终生成: {len(questions)} 道"
    return questions, summary
