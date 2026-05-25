# tests/test_builder.py
import os
import yaml
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from builder import load_skills, generate_examples

def test_load_skills_reads_all_yaml_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["skill_a", "skill_b"]:
            with open(os.path.join(tmpdir, f"{name}.yaml"), "w") as f:
                yaml.dump({"name": name, "description": f"desc {name}", "parameters": {}, "examples": []}, f)
        skills = load_skills(tmpdir)
    assert len(skills) == 2
    names = {s["name"] for s in skills}
    assert names == {"skill_a", "skill_b"}

def test_load_skills_returns_examples_when_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "s.yaml"), "w") as f:
            yaml.dump({"name": "s", "description": "d", "parameters": {}, "examples": ["do x"]}, f)
        skills = load_skills(tmpdir)
    assert skills[0]["examples"] == ["do x"]

def test_generate_examples_calls_llm_and_parses_lines():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "示例一\n示例二\n示例三"}}]
    }
    with patch("requests.post", return_value=mock_resp):
        examples = generate_examples(
            {"name": "web_search", "description": "搜索网络"},
            api_key="test",
            model="qwen-plus",
            n=3,
        )
    assert examples == ["示例一", "示例二", "示例三"]


import numpy as np
from builder import compute_centroid, build_index

def test_compute_centroid_averages_vectors():
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    result = compute_centroid(vectors)
    assert result == pytest.approx([0.5, 0.5])

def test_compute_centroid_single_vector():
    assert compute_centroid([[0.3, 0.7]]) == pytest.approx([0.3, 0.7])

def test_build_index_returns_centroid_per_skill():
    skills = [
        {"name": "skill_a", "description": "do a", "parameters": {}, "examples": ["a1", "a2"]},
    ]
    fake_embeddings = [[1.0, 0.0], [0.0, 1.0]]
    with patch("builder._embed", return_value=fake_embeddings):
        index = build_index(skills, api_key="test", config={
            "embedding": {"model": "text-embedding-v3"},
            "llm_fallback": {"model": "qwen-plus"},
            "builder": {"examples_per_skill": 30},
        })
    assert "skill_a" in index
    assert index["skill_a"]["centroid"] == pytest.approx([0.5, 0.5])
    assert index["skill_a"]["description"] == "do a"
