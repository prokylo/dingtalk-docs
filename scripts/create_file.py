#!/usr/bin/env python3
"""
在钉钉文档中创建指定类型的文件

用法:
    python create_file.py <name> <type> [folder_id]

参数:
    name:      文件名称（必填）
    type:      文件类型（必填），支持以下值：
                 adoc   — 钉钉在线文档
                 axls   — 钉钉表格
                 appt   — 钉钉演示（PPT）
                 adraw  — 钉钉白板
                 amind  — 钉钉脑图
                 able   — 钉钉多维表
                 folder — 文件夹
    folder_id: 可选，目标文件夹节点 ID（dentryUuid）或文件夹 URL。
               不传则创建到用户"我的文档"根目录。

示例:
    python create_file.py "数据统计" axls
    python create_file.py "架构设计" amind dpYLaezmVNd76KezTmDMX9bz8rMqPxX6
    python create_file.py "2026 项目" folder
"""

import json
import sys

from mcporter_utils import run_mcporter

SUPPORTED_TYPES = {
    "adoc": "钉钉在线文档",
    "axls": "钉钉表格",
    "appt": "钉钉演示（PPT）",
    "adraw": "钉钉白板",
    "amind": "钉钉脑图",
    "able": "钉钉多维表",
    "folder": "文件夹",
}

TYPE_EMOJI = {
    "adoc": "📄",
    "axls": "📊",
    "appt": "📽️",
    "adraw": "🎨",
    "amind": "🧠",
    "able": "🗂️",
    "folder": "📁",
}


def create_file(name: str, file_type: str, folder_id: str = None) -> dict:
    """调用 create_file 工具创建文件，返回结果 dict，失败时返回 None。"""
    args = {"name": name, "type": file_type}
    if folder_id:
        args["folderId"] = folder_id

    result = run_mcporter("create_file", args)
    return result


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("错误：缺少必要参数 name 或 type")
        sys.exit(1)

    name = sys.argv[1].strip()
    file_type = sys.argv[2].strip().lower()
    folder_id = sys.argv[3].strip() if len(sys.argv) > 3 else None

    if not name:
        print("错误：文件名称不能为空")
        sys.exit(1)

    if file_type not in SUPPORTED_TYPES:
        supported_list = "、".join(f"{k}（{v}）" for k, v in SUPPORTED_TYPES.items())
        print(f"错误：不支持的文件类型 \"{file_type}\"")
        print(f"支持的类型：{supported_list}")
        sys.exit(1)

    emoji = TYPE_EMOJI.get(file_type, "📄")
    type_label = SUPPORTED_TYPES[file_type]
    location_hint = f"文件夹 {folder_id}" if folder_id else "我的文档根目录"

    print(f"{emoji} 创建{type_label}：{name}")
    print(f"   目标位置：{location_hint}")
    print("-" * 50)

    result = create_file(name=name, file_type=file_type, folder_id=folder_id)
    if not result:
        sys.exit(1)

    node_id = result.get("nodeId", "")
    doc_url = result.get("docUrl") or f"https://alidocs.dingtalk.com/i/nodes/{node_id}"
    content_type = result.get("contentType", "")

    print(f"✅ 创建成功：{name}")
    print(f"   类型：{type_label}（contentType={content_type}）")
    print(f"   文件 ID：{node_id}")
    print("-" * 50)
    print(f"\n访问链接：{doc_url}")


if __name__ == "__main__":
    main()
