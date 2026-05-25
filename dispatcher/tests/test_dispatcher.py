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
    with patch("dispatcher.embed", return_value=[[0.1, 0.1]]):
        result = route("xyzxyz", index, config, api_key="test")
    assert result["route"] == "unknown"
    assert result["skill"] is None
