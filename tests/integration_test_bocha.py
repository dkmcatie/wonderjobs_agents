"""
Integration test for Bocha WebSearch integration
Run: export BOCHA_API_KEY="sk-..."; export ALIYUN_API_KEY="..."; python3 -m unittest tests.integration_test_bocha -v
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import unittest


class TestExaminerBochaIntegration(unittest.TestCase):
    """End-to-end integration tests for examiner with Bocha API"""

    def setUp(self):
        """Set up test fixtures"""
        self.examiner_dir = Path(__file__).parent.parent / "examiner"
        self.bocha_key = os.getenv("BOCHA_API_KEY")
        self.aliyun_key = os.getenv("ALIYUN_API_KEY")

    def test_examiner_with_bocha_integration(self):
        """端到端测试：使用 Bocha API 生成面试题"""

        # 检查环境变量
        if not self.bocha_key or self.bocha_key == "test-key":
            self.skipTest("BOCHA_API_KEY 未设置或无效，跳过真实 API 测试")

        if not self.aliyun_key or self.aliyun_key == "test-key":
            self.skipTest("ALIYUN_API_KEY 未设置或无效，跳过真实 API 测试")

        # 运行 examiner.py
        cmd = [
            sys.executable, "examiner.py",
            "--jd", "sample_jd.md",
            "--personality", "sample_personality.md",
            "--company", "测试公司",
            "--position", "测试岗位",
            "--output", "test_integration_output.json"
        ]

        # 设置环境变量
        env = os.environ.copy()
        env["BOCHA_API_KEY"] = self.bocha_key
        env["ALIYUN_API_KEY"] = self.aliyun_key

        result = subprocess.run(cmd, cwd=self.examiner_dir, capture_output=True, text=True, env=env)

        # 调试输出
        print("\n[STDOUT]:", result.stdout)
        print("[STDERR]:", result.stderr)

        # 检查命令是否成功
        self.assertEqual(result.returncode, 0, f"examiner.py 失败: {result.stderr}")

        # 检查输出文件
        output_file = self.examiner_dir / "outputs" / "test_integration_output.json"
        self.assertTrue(output_file.exists(), f"输出文件不存在: {output_file}")

        # 验证 JSON 格式
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn("metadata", data, "缺少 metadata 字段")
        self.assertIn("questions", data, "缺少 questions 字段")
        self.assertEqual(data["metadata"]["total_questions"], 20,
                        f"期望 20 道题目，实际 {data['metadata']['total_questions']}")
        self.assertEqual(len(data["questions"]), 20,
                        f"期望 20 道题目，实际 {len(data['questions'])}")

        # 验证题目结构
        for i, question in enumerate(data["questions"]):
            self.assertIn("id", question, f"题目 {i} 缺少 id")
            self.assertIn("text", question, f"题目 {i} 缺少 text")
            self.assertIn("category", question, f"题目 {i} 缺少 category")
            self.assertIn("difficulty", question, f"题目 {i} 缺少 difficulty")

    def tearDown(self):
        """Clean up test files"""
        output_file = self.examiner_dir / "outputs" / "test_integration_output.json"
        if output_file.exists():
            output_file.unlink()

        # 也清理 markdown 文件
        md_file = self.examiner_dir / "outputs" / "test_integration_output.md"
        if md_file.exists():
            md_file.unlink()


if __name__ == "__main__":
    unittest.main()
