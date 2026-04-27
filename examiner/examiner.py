import os
import sys
import argparse
import yaml
from datetime import datetime
from pathlib import Path

from modules.question_generator import generate_questions_pool
from utils.file_handler import read_markdown, write_json, write_markdown
from utils.validators import validate_inputs
from utils.formatters import to_json, to_markdown


# ── 配置区 ────────────────────────────────────────
CONFIG_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
PROMPTS_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "prompts.yaml")


# ── 配置加载 ────────────────────────────────────────
def load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts(prompts_path: str) -> dict:
    with open(prompts_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 主流程 ────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Examiner: 基于 JD 自动生成面试题目"
    )
    parser.add_argument("--jd", required=True, help="岗位描述 (Markdown)")
    parser.add_argument("--personality", required=True, help="面试官风格档案 (Markdown)")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--position", required=True, help="岗位名称")
    parser.add_argument("--output", default="questions.json", help="输出文件路径")
    parser.add_argument("--config", default=CONFIG_DEFAULT_PATH, help="配置文件路径")

    args = parser.parse_args()

    validate_inputs(args.jd, args.personality, args.company, args.position)

    config = load_config(args.config)
    prompts_path = config.get("prompts", {}).get("path", PROMPTS_DEFAULT_PATH)
    if not os.path.isabs(prompts_path):
        prompts_path = os.path.join(os.path.dirname(__file__), prompts_path)
    prompts = load_prompts(prompts_path)

    print("[信息] 读取输入文件...")
    jd = read_markdown(args.jd)
    personality = read_markdown(args.personality)

    print("[信息] 生成题目池...")
    questions, summary = generate_questions_pool(
        jd=jd,
        personality=personality,
        company=args.company,
        position=args.position,
        prompts=prompts,
        config=config
    )

    metadata = {
        "company": args.company,
        "position": args.position,
        "total_questions": len(questions),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": config.get("qwen", {}).get("model", "qwen-omni-mini")
    }

    print("[信息] 格式化输出...")
    output_dir = config.get("output", {}).get("directory", "./outputs")
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(__file__), output_dir)
    os.makedirs(output_dir, exist_ok=True)

    formats = config.get("output", {}).get("format", ["json", "markdown"])

    if "json" in formats:
        json_output = args.output if args.output.endswith(".json") else args.output.replace(".md", ".json")
        if not os.path.isabs(json_output):
            json_output = os.path.join(output_dir, json_output)
        write_json(json_output, {
            "metadata": metadata,
            "questions": questions
        })
        print(f"✅ JSON 文件已生成: {json_output}")

    if "markdown" in formats:
        md_output = args.output if args.output.endswith(".md") else args.output.replace(".json", ".md")
        if not os.path.isabs(md_output):
            md_output = os.path.join(output_dir, md_output)
        md_content = to_markdown(questions, metadata)
        write_markdown(md_output, md_content)
        print(f"✅ Markdown 文件已生成: {md_output}")

    print("\n[总结]")
    print(summary)


if __name__ == "__main__":
    main()
