#!/usr/bin/env python3
"""
mcporter 公共工具函数

提供 mcporter 命令执行、响应解析、路径安全校验等通用功能，
供 create_doc.py、import_docs.py、export_docs.py 共用。

新版 MCP 工具名对照（v1.0，共 12 个）：
  create_document        — 创建在线文档（支持直接传 markdown 初始内容，不传 folderId 默认到根目录）
  create_file            — 创建文件（adoc/axls/appt/adraw/amind/able/folder 七种类型）
  update_document        — 更新文档内容（mode: overwrite/append，默认 overwrite）
  get_document_content   — 获取文档内容（nodeId 支持 URL 或 ID 自动识别，需下载权限）
  search_documents       — 搜索文档（不传 keyword 返回最近访问列表）
  create_folder          — 创建文件夹（支持 folderId/workspaceId）
  list_nodes             — 遍历文件夹（支持 pageToken 分页）
  get_document_info      — 获取文档元信息
  list_document_blocks   — 查询文档块列表
  insert_document_block  — 插入块元素（heading.level 必须传整数）
  update_document_block  — 更新块元素（仅支持 paragraph）
  delete_document_block  — 删除块元素（不可恢复）
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def run_mcporter(server_name: str, tool_name: str, args: dict = None, timeout: int = 60) -> Tuple[bool, str]:
    """
    执行 mcporter 命令（使用 --args JSON 传参）

    Args:
        server_name: MCP 服务名称，如 dingtalk-docs
        tool_name: 工具名称，如 create_document
        args: 参数字典，传入 --args JSON
        timeout: 超时时间（秒）

    Returns:
        (success, output) 元组
    """
    command = ['mcporter', 'call', server_name, tool_name, '--output', 'json']
    if args:
        command.extend(['--args', json.dumps(args, ensure_ascii=False)])
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"命令执行超时（{timeout}秒）"
    except Exception as error:
        return False, str(error)


def parse_response(output: str) -> Optional[dict]:
    """解析 mcporter 响应，自动处理嵌套 result 结构"""
    try:
        data = json.loads(output)
        if isinstance(data, dict) and 'result' in data:
            return data['result']
        return data
    except json.JSONDecodeError:
        return None


def create_document_with_content(name: str, markdown: str = None, folder_id: str = None) -> Optional[dict]:
    """
    创建文档（新版 API）。

    新版 create_document 支持直接传 markdown 初始内容，一步完成创建+写入。
    不传 folder_id 时默认创建到用户"我的文档"根目录，无需提前获取根目录 ID。

    Args:
        name: 文档标题
        markdown: 文档初始内容（Markdown 格式），不传则创建空文档
        folder_id: 目标文件夹节点 ID（支持 URL 或 ID），不传则创建到根目录

    Returns:
        包含 nodeId、docUrl 等字段的结果字典，失败返回 None
    """
    args: dict = {'name': name}
    if markdown:
        args['markdown'] = markdown
    if folder_id:
        args['folderId'] = folder_id

    success, output = run_mcporter('dingtalk-docs', 'create_document', args)
    if not success:
        print(f"❌ 创建文档失败：{output}")
        return None

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        return None
    return result


def get_document_content(node_id: str) -> Optional[str]:
    """
    获取文档内容（新版 API）。

    node_id 支持两种格式，系统自动识别：
    - 文档 URL：https://alidocs.dingtalk.com/i/nodes/{dentryUuid}
    - 文档 ID（dentryUuid）：32 位字母数字字符串

    Args:
        node_id: 文档标识（URL 或 ID）

    Returns:
        文档 Markdown 内容字符串，失败返回 None
    """
    success, output = run_mcporter('dingtalk-docs', 'get_document_content', {'nodeId': node_id})
    if not success:
        print(f"❌ 获取文档内容失败：{output}")
        return None

    result = parse_response(output)
    if result is None:
        print(f"❌ 解析响应失败：{output}")
        return None
    return result.get('markdown', '')


def resolve_safe_path(path: str) -> Path:
    """解析路径并限制在工作目录内，防止路径遍历攻击"""
    allowed_root = os.environ.get('OPENCLAW_WORKSPACE', os.getcwd())
    allowed_root = Path(allowed_root).resolve()

    if Path(path).is_absolute():
        target_path = Path(path).resolve()
    else:
        target_path = (Path.cwd() / path).resolve()

    try:
        target_path.relative_to(allowed_root)
        return target_path
    except ValueError:
        raise ValueError(
            f"路径超出允许范围：{path}\n"
            f"允许根目录：{allowed_root}\n"
            f"提示：设置 OPENCLAW_WORKSPACE 环境变量"
        )
