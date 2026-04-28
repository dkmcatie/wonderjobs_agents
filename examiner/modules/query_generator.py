import json
from typing import List, Dict
from modules.qwen_client import call_api


def generate_search_queries(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict
) -> List[str]:
    """
    用 Qwen 生成 3-5 个搜索词

    Args:
        jd (str): 岗位描述
        company (str): 公司名称
        position (str): 岗位名称
        prompts (Dict): prompts.yaml 的全部内容
        config (Dict): 配置对象

    Returns:
        List[str]: 搜索词列表
    """
    if not prompts or "generate_search_queries" not in prompts:
        print("[警告] generate_search_queries prompt 未定义，返回空列表")
        return []

    system_prompt = prompts["generate_search_queries"]["system"]
    user_template = prompts["generate_search_queries"]["user"]

    user_prompt = user_template.format(
        company=company,
        position=position,
        jd=jd
    )

    try:
        response = call_api(system_prompt, user_prompt, config)

        # 解析 JSON 响应
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        queries = json.loads(json_str)

        if not isinstance(queries, list):
            print(f"[警告] 期望返回 JSON 数组，实际得到 {type(queries).__name__}")
            return []

        print(f"[流程] 生成 {len(queries)} 个搜索词: {queries}")
        return queries

    except json.JSONDecodeError as e:
        print(f"[警告] 搜索词生成 JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"[警告] 搜索词生成失败: {e}")
        return []
