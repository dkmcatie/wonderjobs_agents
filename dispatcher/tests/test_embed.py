from unittest.mock import patch, MagicMock
from embed import embed

def test_embed_single_text():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]
    }
    with patch("requests.post", return_value=mock_resp):
        result = embed(["hello"], api_key="test-key")
    assert result == [[0.1, 0.2, 0.3]]

def test_embed_multiple_texts_preserves_order():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]
    }
    with patch("requests.post", return_value=mock_resp):
        result = embed(["foo", "bar"], api_key="test-key")
    assert result[0] == [1.0, 0.0]
    assert result[1] == [0.0, 1.0]
