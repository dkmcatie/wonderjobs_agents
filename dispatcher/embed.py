import requests

API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def embed(texts: list, api_key: str, model: str = "text-embedding-v3") -> list:
    response = requests.post(
        f"{API_BASE}/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "input": texts},
    )
    response.raise_for_status()
    data = response.json()["data"]
    ordered = sorted(data, key=lambda x: x["index"])
    return [item["embedding"] for item in ordered]
