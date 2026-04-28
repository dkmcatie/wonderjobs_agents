import os
import time
import requests
from typing import List, Dict
import json


def call_bocha_api(
    query: str,
    config: Dict,
    max_retries: int = 3
) -> List[str]:
    """
    调用 Bocha API 搜索面试题目

    Args:
        query (str): 搜索关键词
        config (Dict): 配置字典，包含：
            - bocha_api_endpoint: API 端点
            - bocha_api_key: API Key
            - bocha_timeout: 超时时间
            - bocha_max_retries: 重试次数
            - bocha_freshness: 时间范围过滤
            - bocha_max_results_per_query: 每个查询最多返回条数
        max_retries (int): 失败重试次数

    Returns:
        List[str]: 搜索到的题目文本列表

    Raises:
        ValueError: API Key 无效时抛出
    """
    bocha_config = config.get("bocha", {})
    api_endpoint = bocha_config.get("api_endpoint")
    api_key = os.getenv("BOCHA_API_KEY") or bocha_config.get("api_key", "").replace("${BOCHA_API_KEY}", "")
    timeout = bocha_config.get("timeout", 30)
    freshness = bocha_config.get("freshness", "noLimit")
    max_results = bocha_config.get("max_results_per_query", 5)

    if not api_key or api_key.startswith("${"):
        raise ValueError("BOCHA_API_KEY not set in environment or config")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "freshness": freshness,
        "count": max_results
    }

    # 重试逻辑
    for attempt in range(max_retries):
        try:
            print(f"[流程] Bocha API 调用: '{query}' (尝试 {attempt + 1}/{max_retries})")
            resp = requests.post(
                f"{api_endpoint}",
                headers=headers,
                json=payload,
                timeout=timeout
            )

            # 处理特定状态码
            if resp.status_code == 401:
                raise ValueError(f"Bocha API Key 无效: {resp.text}")

            if resp.status_code == 429:
                # 速率限制，重试
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                    print(f"[警告] Bocha API 速率限制，等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[警告] Bocha API 重试次数已用尽")
                    return []

            resp.raise_for_status()

            # 解析响应
            result = resp.json()
            questions = _extract_questions_from_response(result)
            print(f"[流程] 获取 {len(questions)} 道题目")
            return questions

        except (requests.Timeout, TimeoutError):
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[警告] Bocha API 超时，等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[警告] Bocha API 超时，已重试 {max_retries} 次，返回空列表")
                return []

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Only catch ValueError if it's from parsing, not from 401 check
            if isinstance(e, ValueError) and "API Key" in str(e):
                raise
            print(f"[警告] Bocha API 响应解析失败: {e}")
            return []

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[警告] Bocha API 调用失败: {e}，等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[警告] Bocha API 调用失败，已重试 {max_retries} 次，返回空列表")
                return []

        except Exception as e:
            # Catch all other exceptions and retry
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[警告] Bocha API 调用失败: {e}，等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[警告] Bocha API 调用失败，已重试 {max_retries} 次，返回空列表")
                return []

    return []


def _extract_questions_from_response(response: Dict) -> List[str]:
    """
    从 Bocha API 响应中提取题目文本

    Args:
        response (Dict): Bocha API 返回的 JSON 响应

    Returns:
        List[str]: 题目文本列表
    """
    questions = []

    # Bocha API 的响应格式通常是 {"results": [...]}
    results = response.get("results", [])

    for item in results:
        # 优先使用 title，如果没有则尝试 snippet
        text = item.get("title") or item.get("snippet", "")
        if text and len(text.strip()) > 0:
            questions.append(text.strip())

    return questions
