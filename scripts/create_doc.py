#!/usr/bin/env python3
"""
在钉钉文档中创建新文档并写入内容

用法:
    python create_doc.py <title> [content]

参数:
    title: 文档标题
    content: 可选，文档内容（支持 Markdown 格式，默认空内容）

示例:
    python create_doc.py "项目计划" "# 项目计划\n\n## 目标\n完成 Q1 目标"
    python create_doc.py "会议纪要"
"""

import sys

from mcporter_utils import create_document_with_content

# ============== 安全常量 ==============
MAX_CONTENT_LENGTH = 50000  # 最大内容长度（字符）


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("错误：缺少文档标题参数")
        sys.exit(1)

    title = sys.argv[1].strip()
    content = sys.argv[2] if len(sys.argv) > 2 else ""

    if not title:
        print("错误：文档标题不能为空")
        sys.exit(1)

    # 处理转义字符（命令行传入的 \n 转为真实换行）
    if content:
        content = content.replace('\\n', '\n').replace('\\t', '\t')

    if content and len(content) > MAX_CONTENT_LENGTH:
        print(f"⚠️  内容过长（{len(content)} 字符），截断到 {MAX_CONTENT_LENGTH} 字符")
        content = content[:MAX_CONTENT_LENGTH]

    print(f"📝 创建文档：{title}")
    print("-" * 50)

    # 新版 create_document 支持直接传 markdown，一步完成创建+写入
    # 不传 folderId 时默认创建到"我的文档"根目录，无需提前获取根目录 ID
    result = create_document_with_content(name=title, markdown=content or None)
    if not result:
        sys.exit(1)

    node_id = result.get('nodeId', '')
    doc_url = result.get('docUrl') or f"https://alidocs.dingtalk.com/i/nodes/{node_id}"

    print(f"✅ 文档创建成功：{title}")
    print(f"   文档 ID: {node_id}")
    print("-" * 50)
    print(f"\n文档链接：{doc_url}")


if __name__ == '__main__':
    main()
