"""
面试视频综合评测工具

输入接口:
    --jd          岗位JD，md格式文件路径
    --resume      简历，md格式文件路径
    --personality 面试官性格，md格式文件路径
    --video       面试视频，mp4格式文件路径
    --timestamps  对话时间戳文件，每行格式: HHMMSS HHMMSS (起始 结束)
    --transcript  面试整体文字内容，txt格式文件路径
    --output      输出评价报告路径，md格式（默认: review_output.md）

用法示例:
    python reviewer.py \
        --jd job.md \
        --resume resume.md \
        --personality interviewer.md \
        --video interview.mp4 \
        --timestamps timestamps.txt \
        --transcript transcript.txt \
        --output report.md

时间戳文件格式示例 (timestamps.txt):
    000010 000130
    000130 000320
    000320 000510
"""

import os
import sys
import json
import base64
import argparse
import subprocess
import tempfile
import requests
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


# ── 配置 ────────────────────────────────────────────────────────────────────
API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY = "sk-0808fa5018754ac28df073b3500fa6e6"
MODEL = "qwen-omni-mini"
PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "prompts.yaml")


# ── Prompt 加载 ──────────────────────────────────────────────────────────────
def load_prompts() -> dict:
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 时间工具 ─────────────────────────────────────────────────────────────────
def parse_hhmmss(s: str) -> float:
    """将 HHMMSS 字符串转换为秒数"""
    s = s.strip().zfill(6)
    hh, mm, ss = int(s[0:2]), int(s[2:4]), int(s[4:6])
    return hh * 3600 + mm * 60 + ss


def seconds_to_hhmmss(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}{(sec % 3600) // 60:02d}{sec % 60:02d}"


def format_time_range(start: float, end: float) -> str:
    def fmt(s):
        s = int(s)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{fmt(start)} ~ {fmt(end)}"


# ── 时间戳文件解析 ────────────────────────────────────────────────────────────
def parse_timestamps(filepath: str) -> list[dict]:
    """
    解析时间戳文件，每行格式: HHMMSS HHMMSS
    返回 [{"start": float秒, "end": float秒}, ...]
    """
    segments = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f"[警告] 第{i+1}行格式错误，跳过: {line}")
                continue
            start = parse_hhmmss(parts[0])
            end = parse_hhmmss(parts[1])
            segments.append({
                "index": i,
                "start": start,
                "end": end,
                "time_range": format_time_range(start, end),
                "segment_id": f"segment_{i:03d}"
            })
    return segments


# ── 视频切分 ─────────────────────────────────────────────────────────────────
def cut_segment(video_path: str, start: float, end: float, output_path: str) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(start),
        "-to", str(end),
        "-i", video_path,
        "-c", "copy",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[错误] ffmpeg 切分失败: {result.stderr[-300:]}")
        return False
    return True


def video_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── API 调用 ─────────────────────────────────────────────────────────────────
def call_model_text(system_prompt: str, user_prompt: str) -> str:
    """纯文字请求"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    resp = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_model_video(system_prompt: str, user_prompt: str, video_b64: str) -> str:
    """视频+文字请求"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}
                    },
                    {"type": "text", "text": user_prompt}
                ]
            }
        ],
        "modalities": ["text"],
        "stream": False
    }
    resp = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── 单片段评测 ───────────────────────────────────────────────────────────────
def evaluate_segment(seg: dict, video_b64: str, jd: str, prompts: dict) -> dict:
    """
    对单个视频片段并行执行 voice_tone + facial_expression 评测
    返回 {"segment_id", "time_range", "tone_res_part", "facial_res_part"}
    """
    seg_id = seg["segment_id"]
    time_range = seg["time_range"]

    def run_tone():
        user_prompt = prompts["voice_tone"]["user"].format(
            jd=jd, segment_id=seg_id, time_range=time_range
        )
        return call_model_video(prompts["voice_tone"]["system"], user_prompt, video_b64)

    def run_facial():
        user_prompt = prompts["facial_expression"]["user"].format(
            jd=jd, segment_id=seg_id, time_range=time_range
        )
        return call_model_video(prompts["facial_expression"]["system"], user_prompt, video_b64)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_tone = ex.submit(run_tone)
        f_facial = ex.submit(run_facial)
        tone_res = f_tone.result()
        facial_res = f_facial.result()

    return {
        "segment_id": seg_id,
        "time_range": time_range,
        "tone_res_part": tone_res,
        "facial_res_part": facial_res
    }


# ── 中间层评测 ───────────────────────────────────────────────────────────────
def evaluate_tone_facial(all_segment_results: list[dict], jd: str, prompts: dict) -> str:
    """
    汇总所有片段的 tone + facial 结果 → tone_facial_res
    """
    tone_block = "\n\n".join(
        f"=== {r['segment_id']} ({r['time_range']}) ===\n{r['tone_res_part']}"
        for r in all_segment_results
    )
    facial_block = "\n\n".join(
        f"=== {r['segment_id']} ({r['time_range']}) ===\n{r['facial_res_part']}"
        for r in all_segment_results
    )
    user_prompt = prompts["final_evaluation"]["user"].format(
        jd=jd,
        tone_results=tone_block,
        facial_results=facial_block
    )
    return call_model_text(prompts["final_evaluation"]["system"], user_prompt)


def evaluate_text_content(transcript: str, jd: str, prompts: dict) -> str:
    """
    全文文字 + JD → content_res
    """
    user_prompt = prompts["text_content"]["user"].format(jd=jd, transcript=transcript)
    return call_model_text(prompts["text_content"]["system"], user_prompt)


# ── 最终评测 ─────────────────────────────────────────────────────────────────
def evaluate_final(tone_facial_res: str, content_res: str, jd: str, personality: str, prompts: dict) -> str:
    """
    tone_facial_res + content_res + JD + 面试官性格 → 最终报告
    """
    user_prompt = prompts["final_eval"]["user"].format(
        jd=jd,
        personality=personality,
        tone_facial_res=tone_facial_res,
        content_res=content_res
    )
    return call_model_text(prompts["final_eval"]["system"], user_prompt)


# ── 输出报告 ─────────────────────────────────────────────────────────────────
def build_report(
    segments: list[dict],
    segment_results: list[dict],
    tone_facial_res: str,
    content_res: str,
    final_report: str,
    output_path: str
):
    lines = [
        f"# 面试评测报告",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 一、各片段评测详情",
        ""
    ]

    for res in segment_results:
        lines += [
            f"### {res['segment_id']}（{res['time_range']}）",
            "",
            "#### 语音语调评测 (tone_res_part)",
            "",
            res["tone_res_part"],
            "",
            "#### 面部表情评测 (facial_res_part)",
            "",
            res["facial_res_part"],
            "",
            "---",
            ""
        ]

    lines += [
        "## 二、非语言维度综合评估 (tone_facial_res)",
        "",
        tone_facial_res,
        "",
        "---",
        "",
        "## 三、内容维度评估 (content_res)",
        "",
        content_res,
        "",
        "---",
        "",
        "## 四、最终综合评价",
        "",
        final_report,
        ""
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[完成] 报告已写入: {output_path}")


# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="面试视频综合评测工具")
    parser.add_argument("--jd",          required=True, help="岗位JD，md文件路径")
    parser.add_argument("--resume",      required=True, help="简历，md文件路径")
    parser.add_argument("--personality", required=True, help="面试官性格，md文件路径")
    parser.add_argument("--video",       required=True, help="面试视频，mp4文件路径")
    parser.add_argument("--timestamps",  required=True, help="时间戳文件，每行: HHMMSS HHMMSS")
    parser.add_argument("--transcript",  required=True, help="面试全文文字，txt文件路径")
    parser.add_argument("--output",      default="review_output.md", help="输出报告路径（默认: review_output.md）")
    args = parser.parse_args()

    # ── 读取输入文件 ──
    for label, path in [
        ("JD", args.jd), ("简历", args.resume), ("面试官性格", args.personality),
        ("视频", args.video), ("时间戳", args.timestamps), ("文字稿", args.transcript)
    ]:
        if not os.path.exists(path):
            print(f"[错误] {label}文件不存在: {path}")
            sys.exit(1)

    jd          = Path(args.jd).read_text(encoding="utf-8")
    personality = Path(args.personality).read_text(encoding="utf-8")
    transcript  = Path(args.transcript).read_text(encoding="utf-8")
    prompts     = load_prompts()

    # ── 解析时间戳 ──
    segments = parse_timestamps(args.timestamps)
    print(f"[解析] 共 {len(segments)} 个对话片段")

    # ── 切分视频并评测 ──
    segment_results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for seg in segments:
            seg_path = os.path.join(tmp_dir, f"{seg['segment_id']}.mp4")
            print(f"\n[切分] {seg['segment_id']} {seg['time_range']}")
            ok = cut_segment(args.video, seg["start"], seg["end"], seg_path)
            if not ok:
                print(f"[跳过] {seg['segment_id']} 切分失败")
                continue

            file_size_mb = os.path.getsize(seg_path) / 1024 / 1024
            print(f"[评测] {seg['segment_id']} ({file_size_mb:.1f}MB) 并行发送 voice_tone + facial_expression ...")
            video_b64 = video_to_base64(seg_path)

            result = evaluate_segment(seg, video_b64, jd, prompts)
            segment_results.append(result)
            print(f"[完成] {seg['segment_id']} 评测完毕")

    if not segment_results:
        print("[错误] 无任何片段评测成功，退出")
        sys.exit(1)

    # ── 中间层：并行执行 final_evaluation + text_content ──
    print(f"\n[汇总] 并行执行非语言综合评估 + 内容评估 ...")
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_tf = ex.submit(evaluate_tone_facial, segment_results, jd, prompts)
        f_tc = ex.submit(evaluate_text_content, transcript, jd, prompts)
        tone_facial_res = f_tf.result()
        content_res     = f_tc.result()
    print("[完成] 非语言综合评估 + 内容评估完成")

    # ── 最终评测 ──
    print("\n[最终] 生成综合面试评价报告 ...")
    final_report = evaluate_final(tone_facial_res, content_res, jd, personality, prompts)
    print("[完成] 综合报告生成完毕")

    # ── 写入报告 ──
    build_report(segments, segment_results, tone_facial_res, content_res, final_report, args.output)


if __name__ == "__main__":
    main()
