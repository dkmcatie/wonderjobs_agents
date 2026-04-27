import json
from typing import List, Dict
from datetime import datetime


def to_json(questions: List[Dict], metadata: Dict) -> str:
    output = {
        "metadata": metadata,
        "questions": questions
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


def to_markdown(questions: List[Dict], metadata: Dict) -> str:
    lines = []

    lines.append("# 面试题目池")
    lines.append("")
    lines.append(f"**岗位**: {metadata['company']} - {metadata['position']}")
    lines.append(f"**生成时间**: {metadata['generated_at'][:10]}")
    lines.append(f"**题目总数**: {metadata['total_questions']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    phase_order = ["简历提问", "技术能力提问", "项目经验提问", "行为/软技能提问"]
    for phase in phase_order:
        phase_questions = [q for q in questions if q["phase"] == phase]
        if not phase_questions:
            continue

        lines.append(f"## {phase} ({len(phase_questions)}道)")
        lines.append("")

        for q in phase_questions:
            lines.append(f"### {q['id']}. {q['difficulty']} - {q['text']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
