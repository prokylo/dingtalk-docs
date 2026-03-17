#!/usr/bin/env python3
"""
钉钉文档 Block 精细编辑工具

支持对钉钉在线文档（ALIDOC）的块元素进行查询、插入、更新、删除操作。

用法:
    python block_ops.py list   <node_id>
    python block_ops.py insert <node_id> <block_type> [--text TEXT] [--level LEVEL]
                               [--after BLOCK_ID | --before BLOCK_ID]
    python block_ops.py update <node_id> <block_id> <text>
    python block_ops.py delete <node_id> <block_id>

子命令说明:
    list    列出文档所有块元素（含 blockId、index、blockType）
    insert  在文档中插入新块，不指定位置时追加到末尾
    update  更新指定块的文本内容（仅支持 paragraph 类型）
    delete  删除指定块（不可恢复，操作前请确认）

参数:
    node_id    文档节点 ID（dentryUuid）或文档 URL
    block_id   块元素 ID（blockId），从 list 子命令结果中获取
    block_type 块类型，支持：paragraph / heading / blockquote /
               unorderedList / orderedList / table
    text       块的文本内容
    level      标题级别（1~6），仅 heading 类型有效，默认 1

示例:
    # 查看文档所有块
    python block_ops.py list YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA

    # 在文档末尾追加一个段落
    python block_ops.py insert YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA paragraph --text "新增段落内容"

    # 在指定块后面插入一个二级标题
    python block_ops.py insert YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA heading --text "二级标题" --level 2 --after mmpzx96vb8asm77jil

    # 在指定块前面插入一个引用
    python block_ops.py insert YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA blockquote --text "引用内容" --before mmpzx96vb8asm77jil

    # 更新段落内容
    python block_ops.py update YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA mmpzx96ve10038tufl "更新后的段落文字"

    # 删除指定块
    python block_ops.py delete YndMj49yWjnbjwX0uDoKKMA9W3pmz5aA mmpzx96ve10038tufl
"""

import argparse
import json
import sys

from mcporter_utils import parse_response, run_mcporter

SERVER_NAME = "dingtalk-docs"

SUPPORTED_INSERT_TYPES = ["paragraph", "heading", "blockquote", "unorderedList", "orderedList", "table"]


# ──────────────────────────────────────────────
# element 构造函数
# ──────────────────────────────────────────────

def build_paragraph_element(text: str) -> dict:
    return {
        "blockType": "paragraph",
        "paragraph": {},
        "children": [{"text": text}],
    }


def build_heading_element(text: str, level: int) -> dict:
    if not 1 <= level <= 6:
        raise ValueError(f"heading level 必须在 1~6 之间，当前值：{level}")
    return {
        "blockType": "heading",
        "heading": {"level": level},
        "children": [{"text": text}],
    }


def build_blockquote_element(text: str) -> dict:
    return {
        "blockType": "blockquote",
        "blockquote": {},
        "children": [{"text": text}],
    }


def build_unordered_list_element(text: str) -> dict:
    return {
        "blockType": "unorderedList",
        "unorderedList": {
            "list": {
                "level": 0,
                "listStyleType": "disc",
                "listStyle": {"format": "disc", "text": "%1", "align": "left"},
            }
        },
        "children": [{"text": text}],
    }


def build_ordered_list_element(text: str) -> dict:
    return {
        "blockType": "orderedList",
        "orderedList": {
            "list": {
                "listId": "list-001",
                "level": 0,
                "listStyleType": "decimal",
                "listStyle": {"format": "decimal", "text": "%1.", "align": "left"},
            }
        },
        "children": [{"text": text}],
    }


def build_table_element(rows: int = 2, cols: int = 3) -> dict:
    cells = [[""] * cols for _ in range(rows)]
    return {
        "blockType": "table",
        "table": {"rolSize": rows, "colSize": cols, "cells": cells},
    }


def build_element(block_type: str, text: str, level: int) -> dict:
    builders = {
        "paragraph": lambda: build_paragraph_element(text),
        "heading": lambda: build_heading_element(text, level),
        "blockquote": lambda: build_blockquote_element(text),
        "unorderedList": lambda: build_unordered_list_element(text),
        "orderedList": lambda: build_ordered_list_element(text),
        "table": lambda: build_table_element(),
    }
    if block_type not in builders:
        raise ValueError(f"不支持的块类型：{block_type}，支持：{', '.join(SUPPORTED_INSERT_TYPES)}")
    return builders[block_type]()


# ──────────────────────────────────────────────
# 子命令实现
# ──────────────────────────────────────────────

def cmd_list(node_id: str):
    """列出文档所有块元素。"""
    print(f"📋 查询文档块列表：{node_id}")
    print("-" * 60)

    success, output = run_mcporter(SERVER_NAME, "list_document_blocks", {"nodeId": node_id})
    if not success:
        print(f"❌ 查询失败：{output}")
        sys.exit(1)

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        sys.exit(1)

    blocks = result.get("blocks", [])
    if not blocks:
        print("（文档暂无块元素）")
        return

    print(f"共 {len(blocks)} 个块：\n")
    for block in blocks:
        index = block.get("index", "?")
        block_id = block.get("blockId", "")
        block_type = block.get("blockType", "")
        # 尝试提取文本预览
        text_preview = _extract_text_preview(block)
        print(f"  [{index:>3}] {block_type:<16} {block_id}  {text_preview}")


def _extract_text_preview(block: dict, max_length: int = 30) -> str:
    """从块元素中提取文本预览。"""
    children = block.get("children", [])
    texts = []
    for child in children:
        if isinstance(child, dict) and "text" in child:
            texts.append(child["text"])
    preview = "".join(texts)
    if len(preview) > max_length:
        preview = preview[:max_length] + "…"
    return f'"{preview}"' if preview else ""


def cmd_insert(node_id: str, block_type: str, text: str, level: int,
               after_block_id: str, before_block_id: str):
    """在文档中插入新块。"""
    try:
        element = build_element(block_type, text, level)
    except ValueError as error:
        print(f"❌ {error}")
        sys.exit(1)

    args = {"nodeId": node_id, "element": element}

    position_hint = "文档末尾"
    if after_block_id:
        args["referenceBlockId"] = after_block_id
        args["where"] = "after"
        position_hint = f"块 {after_block_id} 之后"
    elif before_block_id:
        args["referenceBlockId"] = before_block_id
        args["where"] = "before"
        position_hint = f"块 {before_block_id} 之前"

    print(f"➕ 插入 {block_type} 块到 {position_hint}")
    print(f"   文档：{node_id}")
    if text:
        print(f"   内容：{text[:50]}{'…' if len(text) > 50 else ''}")
    print("-" * 60)

    success, output = run_mcporter(SERVER_NAME, "insert_document_block", args)
    if not success:
        print(f"❌ 插入失败：{output}")
        sys.exit(1)

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        sys.exit(1)

    new_block_id = result.get("blockId", "")
    print(f"✅ 插入成功")
    print(f"   新块 ID：{new_block_id}")


def cmd_update(node_id: str, block_id: str, text: str):
    """更新指定块的文本内容（仅支持 paragraph）。"""
    element = build_paragraph_element(text)
    args = {"nodeId": node_id, "blockId": block_id, "element": element}

    print(f"✏️  更新块：{block_id}")
    print(f"   文档：{node_id}")
    print(f"   新内容：{text[:50]}{'…' if len(text) > 50 else ''}")
    print("-" * 60)

    success, output = run_mcporter(SERVER_NAME, "update_document_block", args)
    if not success:
        print(f"❌ 更新失败：{output}")
        sys.exit(1)

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        sys.exit(1)

    print(f"✅ 更新成功")


def cmd_delete(node_id: str, block_id: str):
    """删除指定块（不可恢复）。"""
    print(f"🗑️  删除块：{block_id}")
    print(f"   文档：{node_id}")
    print("   ⚠️  此操作不可恢复！")
    print("-" * 60)

    confirm = input("确认删除？输入 yes 继续：").strip().lower()
    if confirm != "yes":
        print("已取消删除。")
        return

    args = {"nodeId": node_id, "blockId": block_id}
    success, output = run_mcporter(SERVER_NAME, "delete_document_block", args)
    if not success:
        print(f"❌ 删除失败：{output}")
        sys.exit(1)

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        sys.exit(1)

    print(f"✅ 删除成功")


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="钉钉文档 Block 精细编辑工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # list 子命令
    list_parser = subparsers.add_parser("list", help="列出文档所有块元素")
    list_parser.add_argument("node_id", help="文档节点 ID 或 URL")

    # insert 子命令
    insert_parser = subparsers.add_parser("insert", help="插入新块元素")
    insert_parser.add_argument("node_id", help="文档节点 ID 或 URL")
    insert_parser.add_argument(
        "block_type",
        choices=SUPPORTED_INSERT_TYPES,
        help="块类型",
    )
    insert_parser.add_argument("--text", default="", help="块的文本内容")
    insert_parser.add_argument("--level", type=int, default=1, help="标题级别（1~6，仅 heading 有效）")
    position_group = insert_parser.add_mutually_exclusive_group()
    position_group.add_argument("--after", metavar="BLOCK_ID", help="插入到指定块之后")
    position_group.add_argument("--before", metavar="BLOCK_ID", help="插入到指定块之前")

    # update 子命令
    update_parser = subparsers.add_parser("update", help="更新块文本内容（仅支持 paragraph）")
    update_parser.add_argument("node_id", help="文档节点 ID 或 URL")
    update_parser.add_argument("block_id", help="块 ID（从 list 结果中获取）")
    update_parser.add_argument("text", help="新的文本内容")

    # delete 子命令
    delete_parser = subparsers.add_parser("delete", help="删除块元素（不可恢复）")
    delete_parser.add_argument("node_id", help="文档节点 ID 或 URL")
    delete_parser.add_argument("block_id", help="块 ID（从 list 结果中获取）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "list":
        cmd_list(args.node_id)
    elif args.command == "insert":
        cmd_insert(
            node_id=args.node_id,
            block_type=args.block_type,
            text=args.text,
            level=args.level,
            after_block_id=args.after or "",
            before_block_id=args.before or "",
        )
    elif args.command == "update":
        cmd_update(args.node_id, args.block_id, args.text)
    elif args.command == "delete":
        cmd_delete(args.node_id, args.block_id)


if __name__ == "__main__":
    main()
