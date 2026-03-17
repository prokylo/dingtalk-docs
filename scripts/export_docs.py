#!/usr/bin/env python3
"""
导出钉钉文档到本地文件

用法:
    python export_docs.py <node_id> [output.md]

参数:
    node_id: 文档标识，支持两种格式：
             - 文档 URL：https://alidocs.dingtalk.com/i/nodes/{dentryUuid}
             - 文档 ID（dentryUuid）：32 位字母数字字符串
    output.md: 可选，输出文件路径（默认：<doc_id>.md）

示例:
    python export_docs.py https://alidocs.dingtalk.com/i/nodes/abc123
    python export_docs.py abc123def456ghi789jkl012mno345pq
    python export_docs.py https://alidocs.dingtalk.com/i/nodes/abc123 output.md
"""

import os
import re
import sys
from pathlib import Path

from mcporter_utils import get_document_content, resolve_safe_path

# ============== 安全常量 ==============
MAX_CONTENT_LENGTH = 100000  # 最大内容长度（字符）
ALLOWED_ROOT = os.environ.get('OPENCLAW_WORKSPACE', os.getcwd())

# 支持 URL 或纯 ID 两种格式
DOC_URL_PATTERN = re.compile(
    r'^https://alidocs\.dingtalk\.com/i/nodes/([a-zA-Z0-9]+)$',
    re.IGNORECASE
)
DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{16,}$')


def extract_doc_id(node_id: str) -> str:
    """
    从 node_id 提取文档 ID（用于生成默认文件名）。
    支持 URL 格式和纯 ID 格式。
    """
    url_match = DOC_URL_PATTERN.match(node_id.strip())
    if url_match:
        return url_match.group(1)
    if DOC_ID_PATTERN.match(node_id.strip()):
        return node_id.strip()
    return None


def save_content(content: str, path: Path) -> bool:
    """保存内容到文件"""
    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as error:
        print(f"❌ 保存文件失败：{error}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("错误：缺少文档标识参数")
        sys.exit(1)

    node_id = sys.argv[1].strip()
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 提取文档 ID（用于生成默认文件名）
    doc_id = extract_doc_id(node_id)
    if not doc_id:
        print("❌ 无效的文档标识格式")
        print("支持格式：")
        print("  URL：https://alidocs.dingtalk.com/i/nodes/{dentryUuid}")
        print("  ID：32 位字母数字字符串")
        sys.exit(1)

    # 确定输出文件路径
    if not output_path:
        output_path = f"{doc_id}.md"

    # 解析并验证输出路径（防止目录遍历）
    try:
        safe_output = resolve_safe_path(output_path)
    except ValueError as error:
        print(f"❌ {error}")
        sys.exit(1)

    safe_output = safe_output.resolve()
    if not str(safe_output).startswith(ALLOWED_ROOT):
        safe_output = Path(ALLOWED_ROOT) / safe_output.name

    print(f"📥 导出文档")
    print(f"   文档标识：{node_id}")
    print(f"   目标文件：{safe_output}")
    print("-" * 50)

    # 步骤 1：获取文档内容（新版 API，nodeId 支持 URL 或 ID 自动识别）
    print("步骤 1: 获取文档内容...")
    content = get_document_content(node_id)
    if content is None:
        sys.exit(1)

    print(f"   内容长度：{len(content)} 字符")

    if len(content) > MAX_CONTENT_LENGTH:
        print(f"⚠️  内容过长，截断到 {MAX_CONTENT_LENGTH} 字符")
        content = content[:MAX_CONTENT_LENGTH]

    # 步骤 2：保存文件
    print("\n步骤 2: 保存文件...")
    if not save_content(content, safe_output):
        sys.exit(1)

    print("-" * 50)
    print("✅ 导出完成！")
    print(f"\n文件路径：{safe_output}")


if __name__ == '__main__':
    main()
