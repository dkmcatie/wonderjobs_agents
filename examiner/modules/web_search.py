import json
from typing import List, Dict
from modules.qwen_client import call_api


def search_interview_questions(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict,
    limit: int = 10
) -> List[str]:
    """
    使用 Qwen 3.5 Flash 内置 WebSearch 功能搜索面试题目

    Args:
        jd (str): 岗位描述
        company (str): 公司名称
        position (str): 岗位名称
        prompts (Dict): Prompt 模板
        config (Dict): 配置对象
        limit (int): 目标返回数量

    Returns:
        List[str]: 最多 limit 条的题目文本列表
    """
    web_search_config = config.get("web_search", {})

    if not web_search_config.get("enabled", False):
        print("[信息] WebSearch 未启用，返回空列表")
        return []

    try:
        print("[流程] 步骤: 调用 Qwen WebSearch 搜索面试题")
        system_prompt = prompts["web_search_questions"]["system"]
        user_template = prompts["web_search_questions"]["user"]

        user_prompt = user_template.format(
            jd=jd,
            company=company,
            position=position,
            limit=limit
        )

        # 获取搜索选项配置
        search_options = web_search_config.get("search_options", {})

        # 调用 Qwen API 并启用 WebSearch
        response = call_api(
            system_prompt,
            user_prompt,
            config,
            enable_search=True,
            search_options=search_options
        )

        # 解析响应中的 JSON 数组
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        questions = json.loads(json_str)

        if not isinstance(questions, list):
            print("[警告] WebSearch 返回非列表格式，返回空列表")
            return []

        # 转换为字符串列表（如果是对象的话）
        result = []
        for q in questions:
            if isinstance(q, dict):
                result.append(q.get("text", str(q)))
            else:
                result.append(str(q))

        final_result = result[:limit]
        print(f"[流程] WebSearch 获取 {len(final_result)} 道题目")
        return final_result

    except Exception as e:
        print(f"[警告] WebSearch 失败: {e}，返回空列表")
        return []
