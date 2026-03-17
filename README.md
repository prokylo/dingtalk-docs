# 钉钉文档操作技能 (dingtalk-docs) v1.0

管理钉钉云文档中的文档、文件夹和内容。支持文档搜索、创建、内容读写、文件夹遍历和块元素精细编辑。

## ⚠️ 版本兼容提醒

**本 Skill v1.0 需要新版钉钉文档 MCP URL。**

如果你之前配置的是旧版 URL（工具名为 `list_accessible_documents`、`write_content_to_document` 等），需要重新配置：

1. 访问 [钉钉文档 MCP 广场](https://mcp.dingtalk.com/#/detail?mcpId=9629) 获取新版 StreamableHttp URL
2. 重新配置：`mcporter config add dingtalk-docs --url "<新版URL>"`

## 功能特性

- ✅ 文档搜索 — 搜索有权限访问的文档（`search_documents`）
- ✅ 文档创建 — 支持同时写入初始内容，默认创建到根目录（`create_document`）
- ✅ 内容读取 — 获取文档 Markdown 内容（`get_document_content`）
- ✅ 内容更新 — 覆盖或追加模式（`update_document`）
- ✅ 文档元信息 — 获取文档类型、创建时间等（`get_document_info`）
- ✅ 文件夹管理 — 创建文件夹（`create_folder`）
- ✅ 文件夹遍历 — 列出子节点，支持分页和递归（`list_nodes`）
- ✅ Block 精细编辑 — 插入/更新/删除文档块元素（`insert/update/delete_document_block`）
- ✅ 文件创建 — 创建在线文档、表格、演示、白板、脑图、多维表、文件夹（`create_file`）

## 快速开始

### 1. 安装技能

```bash
clawhub install dingtalk-docs
```

### 2. 安装依赖

```bash
npm install -g mcporter
```

### 3. 配置凭证

访问 [钉钉文档 MCP 广场](https://mcp.dingtalk.com/#/detail?mcpId=9629) 获取新版 StreamableHttp URL：

```bash
mcporter config add dingtalk-docs --url "<你的新版URL>"
```

也可以使用环境变量：

```bash
export DINGTALK_MCP_DOCS_URL="<你的新版URL>"
```

> 这个 URL 含访问令牌，属于敏感凭证。推荐优先用 `mcporter config` 保存，避免泄露到 shell 历史。

### 4. 使用示例

```bash
# 创建文档（带初始内容，一步完成）
mcporter call dingtalk-docs create_document --args '{"name": "项目计划", "markdown": "# 项目计划\n\n## 目标"}'

# 搜索文档
mcporter call dingtalk-docs search_documents --args '{"keyword": "项目"}'

# 获取文档内容（支持 URL 或 nodeId）
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "https://alidocs.dingtalk.com/i/nodes/xxx"}'

# 追加内容到文档
mcporter call dingtalk-docs update_document --args '{"nodeId": "doc_nodeId", "markdown": "\n\n## 新章节", "mode": "append"}'

# 列出文件夹内容
mcporter call dingtalk-docs list_nodes --args '{"folderId": "folder_nodeId"}'

# 创建文件夹
mcporter call dingtalk-docs create_folder --args '{"name": "2026 项目"}'
```

## 工具列表

### 核心工具

| 工具 | 说明 | 必填参数 |
|------|------|---------|
| `search_documents` | 搜索文档 | 无（keyword 选填） |
| `create_document` | 创建在线文档（可含初始 Markdown 内容） | name |
| `create_file` | 创建文件（在线文档/表格/演示/白板/脑图/多维表/文件夹） | name, type |
| `get_document_content` | 获取文档 Markdown 内容 | nodeId |
| `update_document` | 更新文档内容（覆盖或追加） | nodeId, markdown |
| `get_document_info` | 获取文档元信息 | nodeId |
| `create_folder` | 创建文件夹 | name |
| `list_nodes` | 遍历文件夹/知识库子节点 | 无（folderId 选填） |

### Block 精细编辑工具

| 工具 | 说明 | 必填参数 |
|------|------|---------|
| `list_document_blocks` | 查询文档块列表（获取 blockId） | nodeId |
| `insert_document_block` | 在指定位置插入块元素 | nodeId, element |
| `update_document_block` | 更新指定块元素（仅支持 paragraph） | nodeId, blockId, element |
| `delete_document_block` | 删除指定块元素（不可恢复） | nodeId, blockId |

完整参数说明请查看 [references/api-reference.md](references/api-reference.md)

Block 元素数据结构请查看：
- 中文版：[dingtalk_document_struct.md](dingtalk_document_struct.md)
- English：[dingtalk_document_struct_en.md](dingtalk_document_struct_en.md)

## 注意事项

- **nodeId 支持 URL 或 ID 自动识别**，无需手动拼接 URL
- **`update_document(mode="overwrite")` 会清空全部内容**，操作前请确认
- **`delete_document_block` 不可恢复**，删除前先用 `list_document_blocks` 确认 blockId
- 仅支持 contentType=ALIDOC 的文档读写内容，表格/PPT/PDF 不支持 Markdown 读写
- **`get_document_content` 需要对目标文档有「下载」权限**，仅有查看权限时无法获取内容
- **`get_document_content` 不支持跨组织文档**，跨组织文档会返回 `forbidden.accessDenied` 错误
- 凭证 URL 包含访问令牌，请妥善保管

## 目录结构

```
dingtalk-docs/
├── SKILL.md                 # AI 技能入口（≤150 行）
├── package.json             # 元数据
├── README.md                # 人类可读说明
├── CHANGELOG.md             # 变更日志
├── references/
│   ├── api-reference.md     # 12 个工具完整参数 Schema
│   ├── block-api.md         # Block 工具完整 Schema + 块元素数据结构
│   └── error-codes.md       # 错误码说明 + 调试流程
├── scripts/
│   ├── mcporter_utils.py    # mcporter 公共工具函数
│   ├── create_doc.py        # 创建在线文档脚本
│   ├── create_file.py       # 创建文件脚本（支持7种类型）
│   ├── block_ops.py         # Block 精细编辑脚本
│   ├── import_docs.py       # 导入文档脚本
│   └── export_docs.py       # 导出文档脚本
└── tests/
    ├── test_security.py     # 安全功能测试
    ├── testcases.json       # 评测用例
    └── TEST_REPORT.md       # 测试报告
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/aliramw/dingtalk-docs.git

# 运行测试
python3 tests/test_security.py -v
```

## 许可证

MIT License

## 作者

Marila@Dingtalk
