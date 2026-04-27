import json
from pathlib import Path


def read_markdown(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_json(path: str, data: dict) -> None:
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def write_markdown(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")
