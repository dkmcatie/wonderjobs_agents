from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.query_generator import generate_search_queries
from modules.bocha_client import call_bocha_api


def search_interview_questions(
    jd: str,
    company: str,
    position: str,
    prompts: Dict,
    config: Dict,
    limit: int = 10
) -> List[str]:
    """
    完整的 WebSearch 工作流：生成搜索词 → 并行调用 Bocha → 合并去重

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
    bocha_config = config.get("bocha", {})

    if not bocha_config.get("enabled", False):
        print("[信息] Bocha WebSearch 未启用，返回空列表")
        return []

    # 步骤 1: 生成搜索词
    print("[流程] 步骤 1: 生成搜索词")
    search_queries = generate_search_queries(
        jd=jd,
        company=company,
        position=position,
        prompts=prompts,
        config=config
    )

    if not search_queries:
        print("[警告] 搜索词生成失败，返回空列表")
        return []

    print(f"[流程] 生成 {len(search_queries)} 个搜索词")

    # 步骤 2: 并行调用 Bocha
    print("[流程] 步骤 2: 并行调用 Bocha 搜索")
    all_results = []

    # 使用 ThreadPoolExecutor 并行调用
    max_workers = min(3, len(search_queries))  # 最多 3 个并发

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有搜索任务
        future_to_query = {
            executor.submit(call_bocha_api, query, config): query
            for query in search_queries
        }

        # 处理完成的任务
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results = future.result()
                all_results.extend(results)
                print(f"[流程] 搜索词 '{query}' 获取 {len(results)} 道题目")
            except Exception as e:
                print(f"[警告] 搜索词 '{query}' 调用失败: {e}")
                # 继续处理其他搜索词
                continue

    # 步骤 3: 去重并截断
    print("[流程] 步骤 3: 去重并截断结果")
    # 保持顺序的去重
    unique_results = list(dict.fromkeys(all_results))
    final_results = unique_results[:limit]

    print(f"[流程] 最终返回 {len(final_results)} 道题目")
    return final_results
