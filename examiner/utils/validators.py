import os
import sys
from pathlib import Path


def validate_inputs(jd: str, personality: str, company: str, position: str) -> None:
    for label, path in [("JD", jd), ("Personality", personality)]:
        if not os.path.exists(path):
            print(f"[错误] {label}文件不存在: {path}")
            sys.exit(1)
        if not Path(path).stat().st_size > 0:
            print(f"[错误] {label}文件为空: {path}")
            sys.exit(1)

    if not company or not company.strip():
        print("[错误] 公司名称不能为空")
        sys.exit(1)

    if not position or not position.strip():
        print("[错误] 岗位名称不能为空")
        sys.exit(1)
