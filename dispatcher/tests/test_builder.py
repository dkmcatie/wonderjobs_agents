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
