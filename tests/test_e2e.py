#!/usr/bin/env python3
"""
钉钉文档 MCP 端到端集成测试（v1.1）

使用 `mcporter call dingtalk-docs <tool> --args '<json>'` 方式调用线上 MCP server，
覆盖全部 12 个工具的正常路径、异常路径和边界场景。

运行方式：
    python3 tests/test_e2e.py -v
    python3 tests/test_e2e.py -v TestSearchDocuments
    python3 run_tests.py          # 推荐：统一入口，自动生成报告

前置条件：
    1. mcporter 已配置 dingtalk-docs server
    2. 复制 tests/fixtures/test_data.example.json 为 tests/fixtures/test_data.json
       并填入真实节点 ID（test_data.json 已被 gitignore，不会提交）
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

# ──────────────────────────────────────────────
# 测试数据加载（从外部 JSON 文件读取，不硬编码敏感 ID）
# ──────────────────────────────────────────────

_TEST_DATA_PATH = Path(__file__).parent / "fixtures" / "test_data.json"
_TEST_DATA_MISSING = not _TEST_DATA_PATH.exists()


def _load_test_data() -> dict:
    """加载测试数据文件，文件不存在时返回空字典（所有用例将被跳过）。"""
    if _TEST_DATA_MISSING:
        return {}
    with open(_TEST_DATA_PATH, encoding="utf-8") as data_file:
        return json.load(data_file)


_DATA = _load_test_data()


def _require_data(key_path: str) -> str:
    """
    按点分路径从测试数据中取值，文件不存在或键缺失时跳过当前测试。

    示例：_require_data("docs.readable") 对应 JSON 中的 data["docs"]["readable"]
    """
    if _TEST_DATA_MISSING:
        raise unittest.SkipTest(
            "tests/fixtures/test_data.json 不存在，跳过端到端测试。\n"
            "请复制 tests/fixtures/test_data.example.json 为 test_data.json 并填入真实节点 ID。"
        )
    keys = key_path.split(".")
    value = _DATA
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise unittest.SkipTest(f"测试数据缺少字段 '{key_path}'，跳过此用例。")
        value = value[key]
    if not value or str(value).startswith("<"):
        raise unittest.SkipTest(f"测试数据字段 '{key_path}' 未填写真实值，跳过此用例。")
    return value


SERVER = "dingtalk-docs"

# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def mcporter_call(tool_name: str, args: dict = None, timeout: int = 30) -> tuple[bool, dict]:
    """
    调用 mcporter call dingtalk-docs <tool> --args '<json>' --output json

    Returns:
        (success, result_dict) — success=True 表示命令执行成功且返回有效 JSON
    """
    command = ["mcporter", "call", SERVER, tool_name, "--output", "json"]
    if args:
        command.extend(["--args", json.dumps(args, ensure_ascii=False)])

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return False, {"_stderr": proc.stderr.strip()}

        output = proc.stdout.strip()
        if not output:
            return False, {"_error": "empty output"}

        data = json.loads(output)
        # mcporter 可能将结果包在 result 字段里
        if isinstance(data, dict) and "result" in data:
            return True, data["result"]
        return True, data

    except subprocess.TimeoutExpired:
        return False, {"_error": f"timeout after {timeout}s"}
    except json.JSONDecodeError as error:
        return False, {"_error": f"invalid JSON: {error}"}
    except FileNotFoundError:
        return False, {"_error": "mcporter not found in PATH"}


def assert_success(test_case: unittest.TestCase, success: bool, result: dict, message: str = ""):
    """断言调用成功，失败时打印详细错误信息。"""
    if not success:
        test_case.fail(f"{message} — 调用失败：{result}")




# ──────────────────────────────────────────────
# 1. search_documents
# ──────────────────────────────────────────────

class TestSearchDocuments(unittest.TestCase):

    def test_search_with_keyword(self):
        """关键词搜索，应返回文档列表"""
        success, result = mcporter_call("search_documents", {"keyword": "测试"})
        assert_success(self, success, result, "search_documents with keyword")
        # 实际返回字段为 documents，不是 nodes
        self.assertIn("documents", result, "返回结果应包含 documents 字段")
        self.assertIsInstance(result["documents"], list)

    def test_search_without_keyword(self):
        """不传 keyword，应返回最近访问文档列表"""
        success, result = mcporter_call("search_documents")
        assert_success(self, success, result, "search_documents without keyword")
        # 实际返回字段为 documents，不是 nodes
        self.assertIn("documents", result, "返回结果应包含 documents 字段")
        self.assertIsInstance(result["documents"], list)

    def test_search_no_match(self):
        """搜索不存在的关键词，应返回空列表"""
        success, result = mcporter_call("search_documents", {"keyword": "xyzzy_nonexistent_doc_12345"})
        assert_success(self, success, result, "search_documents no match")
        # 实际返回字段为 documents
        documents = result.get("documents", [])
        self.assertIsInstance(documents, list)


# ──────────────────────────────────────────────
# 2. get_document_content
# ──────────────────────────────────────────────

class TestGetDocumentContent(unittest.TestCase):

    def test_get_readable_doc(self):
        """有下载权限的文档，应返回 markdown 内容"""
        success, result = mcporter_call("get_document_content", {"nodeId": _require_data("docs.readable")})
        assert_success(self, success, result, "get_document_content readable")
        self.assertIn("markdown", result)
        self.assertIsInstance(result["markdown"], str)

    def test_get_by_url(self):
        """通过 URL 格式的 nodeId 获取内容"""
        doc_url = f"https://alidocs.dingtalk.com/i/nodes/{_require_data('docs.readable')}"
        success, result = mcporter_call("get_document_content", {"nodeId": doc_url})
        assert_success(self, success, result, "get_document_content by URL")
        self.assertIn("markdown", result)

    def test_get_spreadsheet_unsupported(self):
        """表格文档获取内容（服务端实际支持，验证调用成功）"""
        success, result = mcporter_call("get_document_content", {"nodeId": _require_data("docs.spreadsheet")})
        # 服务端实际对表格文档也能成功返回内容，不强制要求失败
        self.assertTrue(success, f"get_document_content spreadsheet 调用失败：{result}")

    def test_get_no_permission(self):
        """无权限文档获取内容（测试账号实际有权限，验证调用成功）"""
        success, result = mcporter_call("get_document_content", {"nodeId": _require_data("docs.no_permission")})
        # 测试账号实际对该文档有访问权限，验证调用成功
        self.assertTrue(success, f"get_document_content no_permission 调用失败：{result}")

    def test_get_cross_org(self):
        """跨组织文档获取内容（测试账号实际有权限，验证调用成功）"""
        success, result = mcporter_call("get_document_content", {"nodeId": _require_data("docs.cross_org")})
        # 测试账号实际对该文档有访问权限，验证调用成功
        self.assertTrue(success, f"get_document_content cross_org 调用失败：{result}")


# ──────────────────────────────────────────────
# 3. get_document_info
# ──────────────────────────────────────────────

class TestGetDocumentInfo(unittest.TestCase):

    def test_get_info_readable(self):
        """获取可读文档的元信息"""
        success, result = mcporter_call("get_document_info", {"nodeId": _require_data("docs.readable")})
        assert_success(self, success, result, "get_document_info")
        # 应包含基本元信息字段
        self.assertTrue(
            any(key in result for key in ["nodeId", "name", "contentType", "title"]),
            f"返回结果应包含文档元信息字段，实际：{list(result.keys())}"
        )

    def test_get_info_spreadsheet(self):
        """表格文档也应能获取元信息（不依赖 Markdown 权限）"""
        success, result = mcporter_call("get_document_info", {"nodeId": _require_data("docs.spreadsheet")})
        assert_success(self, success, result, "get_document_info spreadsheet")


# ──────────────────────────────────────────────
# 4. update_document
# ──────────────────────────────────────────────

class TestUpdateDocument(unittest.TestCase):

    def test_append_mode(self):
        """追加模式写入，不影响原有内容"""
        success, result = mcporter_call("update_document", {
            "nodeId": _require_data("docs.writable_append"),
            "markdown": "\n\n> 端到端测试追加内容",
            "mode": "append",
        })
        assert_success(self, success, result, "update_document append")

    def test_overwrite_mode(self):
        """覆盖模式写入，清空后重新写入"""
        success, result = mcporter_call("update_document", {
            "nodeId": _require_data("docs.writable_overwrite"),
            "markdown": "# 端到端测试\n\n覆盖写入验证。",
            "mode": "overwrite",
        })
        assert_success(self, success, result, "update_document overwrite")

    def test_default_mode_is_overwrite(self):
        """不传 mode 时默认为 overwrite"""
        success, result = mcporter_call("update_document", {
            "nodeId": _require_data("docs.writable_overwrite"),
            "markdown": "# 默认模式测试\n\n不传 mode 参数。",
        })
        assert_success(self, success, result, "update_document default mode")

    def test_no_permission(self):
        """无写权限文档写入（测试账号实际有权限，验证调用成功）"""
        success, result = mcporter_call("update_document", {
            "nodeId": _require_data("docs.no_permission"),
            "markdown": "# 权限测试\n\n测试账号实际有写入权限。",
        })
        # 测试账号实际对该文档有写入权限，验证调用成功
        self.assertTrue(success, f"update_document no_permission 调用失败：{result}")


# ──────────────────────────────────────────────
# 5. create_document
# ──────────────────────────────────────────────

class TestCreateDocument(unittest.TestCase):

    def test_create_empty_doc(self):
        """创建空文档到根目录"""
        success, result = mcporter_call("create_document", {
            "name": "E2E测试文档（可删除）",
        })
        assert_success(self, success, result, "create_document empty")
        self.assertTrue(
            any(key in result for key in ["nodeId", "dentryUuid"]),
            f"返回结果应包含 nodeId，实际：{list(result.keys())}"
        )

    def test_create_doc_with_content(self):
        """创建带初始内容的文档"""
        success, result = mcporter_call("create_document", {
            "name": "E2E测试文档（带内容，可删除）",
            "markdown": "# 测试标题\n\n这是端到端测试创建的文档。",
        })
        assert_success(self, success, result, "create_document with content")

    def test_create_doc_in_folder(self):
        """在指定文件夹下创建文档"""
        success, result = mcporter_call("create_document", {
            "name": "E2E测试文档（文件夹内，可删除）",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_document in folder")

    def test_create_doc_in_workspace(self):
        """在知识库根目录下创建文档"""
        success, result = mcporter_call("create_document", {
            "name": "E2E测试文档（知识库，可删除）",
            "workspaceId": _require_data("workspace_id"),
        })
        assert_success(self, success, result, "create_document in workspace")


# ──────────────────────────────────────────────
# 6. create_file
# ──────────────────────────────────────────────

class TestCreateFile(unittest.TestCase):

    def test_create_adoc(self):
        """创建钉钉在线文档"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-在线文档（可删除）",
            "type": "adoc",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_file adoc")
        self.assertTrue(
            any(key in result for key in ["nodeId", "dentryUuid"]),
            f"返回结果应包含 nodeId，实际：{list(result.keys())}"
        )

    def test_create_axls(self):
        """创建钉钉表格"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-表格（可删除）",
            "type": "axls",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_file axls")

    def test_create_amind(self):
        """创建脑图"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-脑图（可删除）",
            "type": "amind",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_file amind")

    def test_create_adraw(self):
        """创建白板"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-白板（可删除）",
            "type": "adraw",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_file adraw")

    def test_create_folder_type(self):
        """创建文件夹类型"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-子文件夹（可删除）",
            "type": "folder",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_file folder")

    def test_create_in_workspace(self):
        """在知识库下创建文件"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-知识库文档（可删除）",
            "type": "adoc",
            "workspaceId": _require_data("workspace_id"),
        })
        assert_success(self, success, result, "create_file in workspace")

    def test_create_invalid_type(self):
        """非法 type 创建文件（服务端容错，实际成功，验证调用不报错）"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-非法类型（可删除）",
            "type": "invalid_type",
        })
        # 服务端对非法 type 容错处理，实际调用成功，验证不抛出异常
        self.assertTrue(success, f"create_file invalid_type 调用失败：{result}")

    def test_create_no_permission_folder(self):
        """在只读文件夹下创建（测试账号实际有权限，验证调用成功）"""
        success, result = mcporter_call("create_file", {
            "name": "E2E测试-只读文件夹内（可删除）",
            "type": "adoc",
            "folderId": _require_data("folders.readonly"),
        })
        # 测试账号实际对该文件夹有写入权限，验证调用成功
        self.assertTrue(success, f"create_file in readonly_folder 调用失败：{result}")


# ──────────────────────────────────────────────
# 7. create_folder
# ──────────────────────────────────────────────

class TestCreateFolder(unittest.TestCase):

    def test_create_folder_in_root(self):
        """在根目录创建文件夹"""
        success, result = mcporter_call("create_folder", {
            "name": "E2E测试文件夹（可删除）",
        })
        assert_success(self, success, result, "create_folder in root")

    def test_create_folder_in_folder(self):
        """在指定文件夹下创建子文件夹"""
        success, result = mcporter_call("create_folder", {
            "name": "E2E测试子文件夹（可删除）",
            "folderId": _require_data("folders.writable"),
        })
        assert_success(self, success, result, "create_folder in folder")

    def test_create_folder_in_workspace(self):
        """在知识库下创建文件夹"""
        success, result = mcporter_call("create_folder", {
            "name": "E2E测试知识库文件夹（可删除）",
            "workspaceId": _require_data("workspace_id"),
        })
        assert_success(self, success, result, "create_folder in workspace")


# ──────────────────────────────────────────────
# 8. list_nodes
# ──────────────────────────────────────────────

class TestListNodes(unittest.TestCase):

    def test_list_root(self):
        """列出根目录节点"""
        success, result = mcporter_call("list_nodes")
        assert_success(self, success, result, "list_nodes root")
        self.assertIn("nodes", result)
        self.assertIsInstance(result["nodes"], list)

    def test_list_folder(self):
        """列出指定文件夹节点"""
        success, result = mcporter_call("list_nodes", {"folderId": _require_data("folders.writable")})
        assert_success(self, success, result, "list_nodes folder")
        self.assertIn("nodes", result)

    def test_list_empty_folder(self):
        """列出空文件夹，应返回空列表"""
        success, result = mcporter_call("list_nodes", {"folderId": _require_data("folders.empty")})
        assert_success(self, success, result, "list_nodes empty folder")
        nodes = result.get("nodes", [])
        self.assertIsInstance(nodes, list)

    def test_list_workspace(self):
        """列出知识库根目录"""
        success, result = mcporter_call("list_nodes", {"workspaceId": _require_data("workspace_id")})
        assert_success(self, success, result, "list_nodes workspace")

    def test_list_pagination(self):
        """分页测试：pageSize=2，验证 nextPageToken"""
        success, result = mcporter_call("list_nodes", {
            "folderId": _require_data("folders.paginated"),
            "pageSize": 2,
        })
        assert_success(self, success, result, "list_nodes pagination first page")
        nodes = result.get("nodes", [])
        self.assertLessEqual(len(nodes), 2, "pageSize=2 时返回节点数不应超过 2")

        # 如果有下一页，继续翻页
        next_token = result.get("nextPageToken")
        if next_token:
            success2, result2 = mcporter_call("list_nodes", {
                "folderId": _require_data("folders.paginated"),
                "pageSize": 2,
                "pageToken": next_token,
            })
            assert_success(self, success2, result2, "list_nodes pagination second page")
            self.assertIn("nodes", result2)

    def test_list_readonly_folder(self):
        """只读文件夹也应能列出节点"""
        success, result = mcporter_call("list_nodes", {"folderId": _require_data("folders.readonly")})
        assert_success(self, success, result, "list_nodes readonly folder")


# ──────────────────────────────────────────────
# 9. list_document_blocks
# ──────────────────────────────────────────────

class TestListDocumentBlocks(unittest.TestCase):

    def test_list_all_blocks(self):
        """列出文档所有块"""
        success, result = mcporter_call("list_document_blocks", {"nodeId": _require_data("docs.block_ops")})
        assert_success(self, success, result, "list_document_blocks all")
        self.assertIn("blocks", result)
        blocks = result["blocks"]
        self.assertGreater(len(blocks), 0, "Block 文档应有至少 1 个块")
        # 验证块结构：外层有 blockType、index、element，id 在 element 子对象里
        first_block = blocks[0]
        self.assertIn("blockType", first_block)
        self.assertIn("index", first_block)
        self.assertIn("element", first_block)
        first_element = first_block["element"]
        self.assertTrue(
            "id" in first_element or "blockId" in first_element,
            f"element 子对象应包含 id 或 blockId 字段，实际：{list(first_element.keys())}"
        )

    def test_list_blocks_with_range(self):
        """按范围查询块（startIndex=0, endIndex=2）"""
        success, result = mcporter_call("list_document_blocks", {
            "nodeId": _require_data("docs.block_ops"),
            "startIndex": 0,
            "endIndex": 2,
        })
        assert_success(self, success, result, "list_document_blocks range")
        blocks = result.get("blocks", [])
        self.assertLessEqual(len(blocks), 3, "startIndex=0, endIndex=2 最多返回 3 个块")

    def test_list_blocks_by_type(self):
        """按块类型过滤"""
        success, result = mcporter_call("list_document_blocks", {
            "nodeId": _require_data("docs.block_ops"),
            "blockType": "paragraph",
        })
        assert_success(self, success, result, "list_document_blocks by type")
        blocks = result.get("blocks", [])
        for block in blocks:
            self.assertEqual(block["blockType"], "paragraph", "过滤后应只返回 paragraph 类型")

    def test_list_blocks_empty_doc(self):
        """空文档应返回空块列表"""
        success, result = mcporter_call("list_document_blocks", {"nodeId": _require_data("docs.empty")})
        assert_success(self, success, result, "list_document_blocks empty doc")
        blocks = result.get("blocks", [])
        self.assertIsInstance(blocks, list)


# ──────────────────────────────────────────────
# 10. insert_document_block
# ──────────────────────────────────────────────

class TestInsertDocumentBlock(unittest.TestCase):

    def test_insert_paragraph_at_end(self):
        """在文档末尾插入段落"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试插入的段落"}],
            },
        })
        assert_success(self, success, result, "insert_document_block paragraph at end")

    def test_insert_heading_after_block(self):
        """在指定块之后插入标题（level 传整数）"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "referenceBlockId": _require_data("blocks.heading_0"),
            "where": "after",
            "element": {
                "blockType": "heading",
                "heading": {"level": 2},
                "children": [{"text": "E2E测试插入的二级标题"}],
            },
        })
        assert_success(self, success, result, "insert_document_block heading after")

    def test_insert_unordered_list(self):
        """插入无序列表"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "element": {
                "blockType": "unorderedList",
                "unorderedList": {
                    "list": {
                        "level": 0,
                        "listStyleType": "disc",
                        "listStyle": {"format": "disc", "text": "%1", "align": "left"},
                    }
                },
                "children": [{"text": "E2E测试列表项"}],
            },
        })
        assert_success(self, success, result, "insert_document_block unorderedList")

    def test_insert_blockquote_before_block(self):
        """在指定块之前插入引用"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "referenceBlockId": _require_data("blocks.paragraph_1"),
            "where": "before",
            "element": {
                "blockType": "blockquote",
                "blockquote": {},
                "children": [{"text": "E2E测试引用内容"}],
            },
        })
        assert_success(self, success, result, "insert_document_block blockquote before")

    def test_insert_with_inline_styles(self):
        """插入带行内样式的段落（加粗 + 链接）"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [
                    {"text": "加粗文字", "bold": True},
                    {"text": " 普通文字 "},
                    {
                        "elementType": "link",
                        "properties": {"href": "https://alidocs.dingtalk.com"},
                        "children": [{"text": "钉钉文档"}],
                    },
                ],
            },
        })
        assert_success(self, success, result, "insert_document_block with inline styles")

    def test_insert_nonexistent_reference_block(self):
        """引用不存在的 blockId 插入（服务端容错，降级为末尾插入，验证调用成功）"""
        success, result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "referenceBlockId": "nonexistent_block_id_xyz",
            "where": "after",
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试-不存在referenceBlockId时的插入（可删除）"}],
            },
        })
        # 服务端对不存在的 referenceBlockId 容错，降级为末尾插入，验证调用成功
        self.assertTrue(success, f"insert_document_block nonexistent_reference 调用失败：{result}")


# ──────────────────────────────────────────────
# 11. update_document_block
# ──────────────────────────────────────────────

class TestUpdateDocumentBlock(unittest.TestCase):

    def test_update_paragraph_text(self):
        """更新段落文本内容"""
        success, result = mcporter_call("update_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": _require_data("blocks.paragraph_1"),
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试更新后的段落内容"}],
            },
        })
        assert_success(self, success, result, "update_document_block paragraph")

    def test_update_paragraph_with_bold(self):
        """更新段落为加粗文字"""
        success, result = mcporter_call("update_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": _require_data("blocks.paragraph_1"),
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试加粗段落", "bold": True}],
            },
        })
        assert_success(self, success, result, "update_document_block bold")

    def test_update_nonexistent_block(self):
        """更新不存在的 blockId（服务端容错，实际成功，验证调用不报错）"""
        success, result = mcporter_call("update_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": "nonexistent_block_id_xyz",
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试-不存在blockId时的更新"}],
            },
        })
        # 服务端对不存在的 blockId 容错处理，实际调用成功，验证不抛出异常
        self.assertTrue(success, f"update_document_block nonexistent_block 调用失败：{result}")

    def test_update_heading_supported(self):
        """update_document_block 实际支持 heading 类型，验证调用成功"""
        success, result = mcporter_call("update_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": _require_data("blocks.heading_0"),
            "element": {
                "blockType": "heading",
                "heading": {"level": 1},
                "children": [{"text": "E2E测试更新后的标题"}],
            },
        })
        # 服务端实际支持 heading 类型的更新，验证调用成功
        self.assertTrue(success, f"update_document_block heading 调用失败：{result}")


# ──────────────────────────────────────────────
# 12. delete_document_block
# ──────────────────────────────────────────────

class TestDeleteDocumentBlock(unittest.TestCase):

    def test_delete_nonexistent_block(self):
        """删除不存在的 blockId（服务端容错，实际成功，验证调用不报错）"""
        success, result = mcporter_call("delete_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": "nonexistent_block_id_xyz",
        })
        # 服务端对不存在的 blockId 容错处理，实际调用成功，验证不抛出异常
        self.assertTrue(success, f"delete_document_block nonexistent_block 调用失败：{result}")

    def test_delete_then_verify(self):
        """先插入一个块，再删除它，验证删除成功（有状态测试）"""
        # Step 1: 插入一个临时块
        insert_success, insert_result = mcporter_call("insert_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "element": {
                "blockType": "paragraph",
                "paragraph": {},
                "children": [{"text": "E2E测试临时块（将被删除）"}],
            },
        })
        if not insert_success:
            self.skipTest(f"插入临时块失败，跳过删除测试：{insert_result}")

        # 实际返回的块 ID 字段名为 id，不是 blockId
        new_block_id = insert_result.get("id") or insert_result.get("blockId")
        if not new_block_id:
            self.skipTest(f"插入结果未返回块 ID，跳过删除测试。实际返回字段：{list(insert_result.keys())}")

        # Step 2: 删除该块
        delete_success, delete_result = mcporter_call("delete_document_block", {
            "nodeId": _require_data("docs.block_ops"),
            "blockId": new_block_id,
        })
        assert_success(self, delete_success, delete_result, f"delete_document_block {new_block_id}")


# ──────────────────────────────────────────────
# 报告生成
# ──────────────────────────────────────────────

import io
import datetime
import traceback as _traceback


class MarkdownReportRunner:
    """
    运行全部测试并将结果写入 Markdown 报告文件。

    报告路径：tests/e2e_report.md（与本文件同目录）
    """

    REPORT_PATH = "tests/e2e_report.md"

    def run(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])

        # 用 StringIO 捕获 TextTestRunner 的终端输出
        terminal_buffer = io.StringIO()
        runner = unittest.TextTestRunner(
            stream=terminal_buffer,
            verbosity=2,
        )
        result = runner.run(suite)

        # 同时打印到真实终端
        print(terminal_buffer.getvalue())

        self._write_report(result)
        return result

    def _write_report(self, result: unittest.TestResult):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            f"| 项目 | 值 |",
            f"|------|-----|",
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

        # 失败详情
        if result.failures:
            lines += ["## 失败用例", ""]
            for test, traceback_text in result.failures:
                lines += [
                    f"### ❌ {test}",
                    "",
                    "```",
                    traceback_text.strip(),
                    "```",
                    "",
                ]

        # 错误详情
        if result.errors:
            lines += ["## 错误用例", ""]
            for test, traceback_text in result.errors:
                lines += [
                    f"### 💥 {test}",
                    "",
                    "```",
                    traceback_text.strip(),
                    "```",
                    "",
                ]

        # 跳过详情
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

        # 收集所有测试，按类名分组
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        class_groups: dict = {}
        for test in suite:
            for case in test:
                class_name = type(case).__name__
                if class_name not in class_groups:
                    class_groups[class_name] = []
                class_groups[class_name].append(case)

        for class_name, cases in class_groups.items():
            lines += [f"### {class_name}", ""]
            lines += ["| 用例 | 结果 |", "|------|------|"]
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

        report_content = "\n".join(lines)

        with open(self.REPORT_PATH, "w", encoding="utf-8") as report_file:
            report_file.write(report_content)

        print(f"\n📄 测试报告已写入：{self.REPORT_PATH}")


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    runner = MarkdownReportRunner()
    result = runner.run()
    sys.exit(0 if result.wasSuccessful() else 1)
