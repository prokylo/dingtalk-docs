#!/usr/bin/env python3
"""
钉钉文档技能统一测试入口（run_tests.py）

用法：
    python3 run_tests.py              # 运行全部测试（单元 + 端到端）
    python3 run_tests.py --unit       # 仅运行单元测试（test_security.py）
    python3 run_tests.py --e2e        # 仅运行端到端测试（test_e2e.py）
    python3 run_tests.py --no-report  # 不生成 Markdown 报告

前置条件（端到端测试）：
    复制 tests/fixtures/test_data.example.json 为 tests/fixtures/test_data.json
    并填入真实节点 ID，然后确保 mcporter 已配置 dingtalk-docs server。

报告输出：
    tests/e2e_report.md  — 端到端测试报告（gitignore，不提交）
"""

import argparse
import io
import json
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path

TESTS_DIR = Path(__file__).parent / "tests"
E2E_REPORT_PATH = TESTS_DIR / "e2e_report.md"
TEST_DATA_PATH = TESTS_DIR / "fixtures" / "test_data.json"
TEST_DATA_EXAMPLE_PATH = TESTS_DIR / "fixtures" / "test_data.example.json"


def check_prerequisites() -> list[str]:
    """检查前置条件，返回警告信息列表。"""
    warnings = []
    if not TEST_DATA_PATH.exists():
        warnings.append(
            f"⚠️  端到端测试数据文件不存在：{TEST_DATA_PATH}\n"
            f"   请复制 {TEST_DATA_EXAMPLE_PATH.name} 为 test_data.json 并填入真实节点 ID。\n"
            f"   端到端测试用例将全部跳过。"
        )
    return warnings


def run_unit_tests(verbosity: int = 2) -> unittest.TestResult:
    """运行单元测试（test_security.py）。"""
    print("\n" + "=" * 60)
    print("📋 单元测试（test_security.py）")
    print("=" * 60)

    sys.path.insert(0, str(TESTS_DIR.parent / "scripts"))
    loader = unittest.TestLoader()
    suite = loader.discover(str(TESTS_DIR), pattern="test_security.py")
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def run_e2e_tests(verbosity: int = 2, generate_report: bool = True) -> unittest.TestResult:
    """运行端到端测试（test_e2e.py），可选生成 Markdown 报告。"""
    print("\n" + "=" * 60)
    print("🌐 端到端集成测试（test_e2e.py）")
    print("=" * 60)

    # 动态导入 test_e2e 模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_e2e", TESTS_DIR / "test_e2e.py")
    test_e2e_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_e2e_module)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_e2e_module)

    if generate_report:
        # 捕获输出并生成 Markdown 报告
        terminal_buffer = io.StringIO()
        runner = unittest.TextTestRunner(stream=terminal_buffer, verbosity=verbosity)
        result = runner.run(suite)
        print(terminal_buffer.getvalue())
        _write_e2e_report(result, test_e2e_module)
    else:
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

    return result


def _write_e2e_report(result: unittest.TestResult, module) -> None:
    """将端到端测试结果写入 Markdown 报告文件。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped
    status_icon = "✅" if result.wasSuccessful() else "❌"

    lines = [
        "# 钉钉文档 MCP 端到端测试报告",
        "",
        "## 概览",
        "",
        "| 项目 | 值 |",
        "|------|-----|",
        f"| 运行时间 | {now} |",
        f"| 总用例数 | {total} |",
        f"| 通过 | {passed} |",
        f"| 失败 | {failures} |",
        f"| 错误 | {errors} |",
        f"| 跳过 | {skipped} |",
        f"| 整体结果 | {status_icon} {'全部通过' if result.wasSuccessful() else '存在失败'} |",
        "",
        "---",
        "",
    ]

    if result.failures:
        lines += ["## 失败用例", ""]
        for test, traceback_text in result.failures:
            lines += [f"### ❌ {test}", "", "```", traceback_text.strip(), "```", ""]

    if result.errors:
        lines += ["## 错误用例", ""]
        for test, traceback_text in result.errors:
            lines += [f"### 💥 {test}", "", "```", traceback_text.strip(), "```", ""]

    if result.skipped:
        lines += ["## 跳过用例", ""]
        for test, reason in result.skipped:
            lines += [f"- ⏭️ `{test}` — {reason}"]
        lines.append("")

    # 全量用例列表（按测试类分组）
    lines += ["## 全量用例结果", ""]
    failed_ids = {str(t) for t, _ in result.failures}
    error_ids = {str(t) for t, _ in result.errors}
    skipped_ids = {str(t) for t, _ in result.skipped}

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)
    class_groups: dict = {}
    for test_suite in suite:
        for case in test_suite:
            class_name = type(case).__name__
            if class_name not in class_groups:
                class_groups[class_name] = []
            class_groups[class_name].append(case)

    for class_name, cases in class_groups.items():
        lines += [f"### {class_name}", "", "| 用例 | 结果 |", "|------|------|"]
        for case in cases:
            case_id = str(case)
            method_doc = getattr(case, case._testMethodName).__doc__ or case._testMethodName
            method_doc = method_doc.strip().split("\n")[0]
            if case_id in failed_ids:
                icon = "❌ 失败"
            elif case_id in error_ids:
                icon = "💥 错误"
            elif case_id in skipped_ids:
                icon = "⏭️ 跳过"
            else:
                icon = "✅ 通过"
            lines.append(f"| {method_doc} | {icon} |")
        lines.append("")

    E2E_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 端到端测试报告已写入：{E2E_REPORT_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description="钉钉文档技能统一测试入口")
    parser.add_argument("--unit", action="store_true", help="仅运行单元测试")
    parser.add_argument("--e2e", action="store_true", help="仅运行端到端测试")
    parser.add_argument("--no-report", action="store_true", help="不生成 Markdown 报告")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1
    run_unit = not args.e2e
    run_e2e = not args.unit
    generate_report = not args.no_report

    print(f"🚀 钉钉文档技能测试 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查前置条件
    for warning in check_prerequisites():
        print(warning)

    all_passed = True

    if run_unit:
        unit_result = run_unit_tests(verbosity=verbosity)
        if not unit_result.wasSuccessful():
            all_passed = False

    if run_e2e:
        e2e_result = run_e2e_tests(verbosity=verbosity, generate_report=generate_report)
        if not e2e_result.wasSuccessful():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 全部测试通过")
    else:
        print("❌ 存在失败用例，请查看上方输出")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
