import pytest
from unittest.mock import patch
from dispatcher import cosine_similarity, route

def test_cosine_similarity_identical_vectors():
    a = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, a) == pytest.approx(1.0)

def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

def test_route_vector_path_high_confidence():
    index = {
        "write_code": {"centroid": [1.0, 0.0, 0.0], "description": "编写代码"},
        "translate":  {"centroid": [0.0, 1.0, 0.0], "description": "翻译文本"},
        "web_search": {"centroid": [0.0, 0.0, 1.0], "description": "搜索网络"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    with patch("dispatcher.embed", return_value=[[0.99, 0.05, 0.05]]):
        result = route("帮我写代码", index, config, api_key="test")
    assert result["skill"] == "write_code"
    assert result["route"] == "vector"
    assert result["confidence"] > 0

def test_route_unknown_when_all_scores_low():
    index = {
        "write_code": {"centroid": [1.0, 0.0], "description": "编写代码"},
        "translate":  {"centroid": [0.0, 1.0], "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    with patch("dispatcher.embed", return_value=[[-0.5, -0.5]]):
        result = route("xyzxyz", index, config, api_key="test")
    assert result["route"] == "unknown"
    assert result["skill"] is None

from unittest.mock import MagicMock
from dispatcher import llm_rerank

def test_llm_rerank_returns_skill_when_confident():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"skill": "debug_code", "confident": true, "reason": "用户提到报错"}'}}]
    }
    candidates = [
        {"name": "write_code", "description": "编写代码"},
        {"name": "debug_code", "description": "调试代码"},
    ]
    with patch("requests.post", return_value=mock_resp):
        result = llm_rerank("这段代码报错了", candidates, api_key="test", model="qwen-plus")
    assert result["skill"] == "debug_code"
    assert result["confident"] is True

def test_route_uses_llm_when_gap_small():
    index = {
        "write_code": {"centroid": [1.0, 0.01], "description": "编写代码"},
        "debug_code": {"centroid": [0.99, 0.0],  "description": "调试代码"},
        "translate":  {"centroid": [0.0,  1.0],  "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    llm_result = {"skill": "debug_code", "confident": True, "reason": "提到报错"}
    with patch("dispatcher.embed", return_value=[[0.99, 0.01]]), \
         patch("dispatcher.llm_rerank", return_value=llm_result):
        result = route("这段代码报错了", index, config, api_key="test")
    assert result["skill"] == "debug_code"
    assert result["route"] == "llm_fallback"

def test_route_returns_clarify_when_llm_not_confident():
    index = {
        "write_code": {"centroid": [1.0, 0.01], "description": "编写代码"},
        "debug_code": {"centroid": [0.99, 0.0],  "description": "调试代码"},
        "translate":  {"centroid": [0.0,  1.0],  "description": "翻译文本"},
    }
    config = {
        "embedding": {"model": "text-embedding-v3"},
        "routing": {"gap_threshold": 0.15, "min_score_threshold": 0.3, "top_k_for_llm": 3},
        "llm_fallback": {"model": "qwen-plus"},
    }
    llm_result = {"skill": "write_code", "confident": False, "reason": "不确定"}
    with patch("dispatcher.embed", return_value=[[0.99, 0.01]]), \
         patch("dispatcher.llm_rerank", return_value=llm_result):
        result = route("代码", index, config, api_key="test")
    assert result["route"] == "clarify"
    assert result["skill"] is None
    assert "write_code" in result["message"] or "debug_code" in result["message"]
