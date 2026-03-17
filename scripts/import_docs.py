#!/usr/bin/env python3
"""
从本地文件导入文档到钉钉文档

用法:
    python import_docs.py <file.md> [title]

参数:
    file.md: Markdown 文件路径
    title: 可选，文档标题（默认使用文件名）

示例:
    python import_docs.py README.md
    python import_docs.py notes.md "项目笔记"
"""

import sys
from pathlib import Path

from mcporter_utils import create_document_with_content, resolve_safe_path

# ============== 安全常量 ==============
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CONTENT_LENGTH = 50000  # 最大内容长度（字符）
ALLOWED_EXTENSIONS = ['.md', '.txt', '.markdown']


def validate_file_extension(filename: str) -> bool:
    """验证文件扩展名"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(path: Path) -> bool:
    """验证文件大小"""
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        print(f"❌ 文件过大：{size / 1024 / 1024:.2f}MB（最大 {MAX_FILE_SIZE / 1024 / 1024}MB）")
        return False
    return True


def read_local_file(path: Path) -> str:
    """读取本地文件内容，自动处理编码"""
    if not validate_file_size(path):
        sys.exit(1)
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk') as file:
            return file.read()
    except Exception as error:
        print(f"❌ 读取文件失败：{error}")
        sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("错误：缺少文件参数")
        sys.exit(1)

    file_path = sys.argv[1]
    title = sys.argv[2].strip() if len(sys.argv) > 2 else None

    # 验证文件扩展名
    if not validate_file_extension(file_path):
        print(f"❌ 不支持的文件类型：{Path(file_path).suffix}")
        print(f"支持的类型：{', '.join(ALLOWED_EXTENSIONS)}")
        sys.exit(1)

    # 解析并验证路径（防止目录遍历）
    try:
        safe_path = resolve_safe_path(file_path)
    except ValueError as error:
        print(f"❌ {error}")
        sys.exit(1)

    if not safe_path.exists():
        print(f"❌ 文件不存在：{safe_path}")
        sys.exit(1)

    if not title:
        title = safe_path.stem

    print(f"📝 导入文档：{title}")
    print(f"   源文件：{safe_path}")
    print("-" * 50)

    # 步骤 1：读取文件内容
    print("步骤 1: 读取文件内容...")
    content = read_local_file(safe_path)
    print(f"   内容长度：{len(content)} 字符")

    if len(content) > MAX_CONTENT_LENGTH:
        print(f"⚠️  内容过长，截断到 {MAX_CONTENT_LENGTH} 字符")
        content = content[:MAX_CONTENT_LENGTH]

    # 步骤 2：创建文档并写入内容（新版 API 一步完成，无需先获取根目录 ID）
    print("\n步骤 2: 创建文档并写入内容...")
    result = create_document_with_content(name=title, markdown=content)
    if not result:
        sys.exit(1)

    node_id = result.get('nodeId', '')
    doc_url = result.get('docUrl') or f"https://alidocs.dingtalk.com/i/nodes/{node_id}"

    print("-" * 50)
    print("✅ 导入完成！")
    print(f"\n文档链接：{doc_url}")


if __name__ == '__main__':
    main()
