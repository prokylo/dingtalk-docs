# 钉钉云文档 API 参考（v1.0）

> 新版 MCP 工具完整参数 Schema、返回值格式和调用示例。
> 需要新版 MCP URL：[钉钉文档 MCP 广场](https://mcp.dingtalk.com/#/detail?mcpId=9629)

## 公共说明

### nodeId 格式

所有接受 `nodeId` / `folderId` 的参数均支持两种格式，系统自动识别：
- **文档 URL**：`https://alidocs.dingtalk.com/i/nodes/{dentryUuid}`
- **文档 ID**：32 位字母数字字符串（dentryUuid）

### 公共返回字段

每个工具的返回值都包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `logId` | string | 请求追踪 ID，遇到问题时提供给钉钉官方排查 |
| `errorCode` | string | 错误码（仅失败时） |
| `errorMessage` | string | 错误描述（仅失败时） |

---

## 1. search_documents — 搜索文档

根据关键词搜索当前用户有权限访问的文档列表。不传 keyword 时返回最近访问的文档（最多 10 条）。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `keyword` | string | 否 | 搜索关键词，匹配文档标题和内容。不传则返回最近访问的文档列表 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `documents` | array | 文档列表（最多 10 条） |
| `documents[].nodeId` | string | 节点 ID，可直接用于其他工具的 nodeId 参数 |
| `documents[].name` | string | 文档标题（已剔除文件后缀） |
| `documents[].nodeType` | string | 节点结构类型：`folder` 或 `file` |
| `documents[].contentType` | string | 内容类型（nodeType=file 时）：`ALIDOC`/`DOCUMENT`/`IMAGE`/`VIDEO`/`AUDIO`/`ARCHIVE`/`OTHER` |
| `documents[].extension` | string | 文件后缀（不含点号，如 adoc、xlsx、pdf） |
| `documents[].docUrl` | string | 文档访问链接 |
| `documents[].lastEditTime` | integer | 最后编辑时间（毫秒时间戳） |
| `documents[].updateTime` | integer | 最后变更时间（毫秒时间戳） |

**调用示例:**

```bash
# 搜索包含"项目"的文档
mcporter call dingtalk-docs search_documents --args '{"keyword": "项目"}'

# 返回最近访问的文档
mcporter call dingtalk-docs search_documents
```

---

## 2. get_document_content — 获取文档内容

获取钉钉文档的内容，以 Markdown 格式返回。仅支持 contentType=ALIDOC 的在线文档，表格/PPT/PDF 等不支持。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 文档标题 |
| `markdown` | string | 文档内容（Markdown 格式） |
| `nodeId` | string | 文档节点 ID |
| `docUrl` | string | 文档访问链接 |

**调用示例:**

```bash
# 通过 nodeId 获取
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "DnRL6jAJMNX9kAgycoLy2vOo8yMoPYe1"}'

# 通过 URL 获取（自动识别）
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "https://alidocs.dingtalk.com/i/nodes/DnRL6jAJMNX9kAgycoLy2vOo8yMoPYe1"}'
```

---

## 3. create_document — 创建文档

创建一篇新的钉钉在线文档，支持同时写入初始内容。不传 folderId 时默认创建到用户"我的文档"根目录。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `name` | string | 是 | 新文档的标题 |
| `folderId` | string | 否 | 目标文件夹节点 ID，支持 URL 或 ID。不传则创建到根目录（或 workspaceId 的根目录） |
| `workspaceId` | string | 否 | 目标知识库 ID。同时传了 folderId 时以 folderId 为准 |
| `markdown` | string | 否 | 文档初始内容（Markdown 格式）。不传则创建空文档 |

**入参优先级：** `folderId` > `workspaceId` > 默认（我的文档根目录）

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodeId` | string | 新文档的节点 ID |
| `name` | string | 文档名称 |
| `folderId` | string | 实际创建位置的父文件夹节点 ID |
| `docUrl` | string | 文档访问链接 |
| `createTime` | integer | 创建时间（毫秒时间戳） |

**调用示例:**

```bash
# 创建空文档到根目录
mcporter call dingtalk-docs create_document --args '{"name": "项目计划"}'

# 创建带初始内容的文档（一步完成）
mcporter call dingtalk-docs create_document --args '{"name": "项目计划", "markdown": "# 项目计划\n\n## 目标\n完成 Q1 目标"}'

# 在指定文件夹下创建
mcporter call dingtalk-docs create_document --args '{"name": "子文档", "folderId": "folder_nodeId"}'

# 在知识库根目录下创建
mcporter call dingtalk-docs create_document --args '{"name": "知识库文档", "workspaceId": "workspace_id"}'
```

---

## 4. update_document — 更新文档内容

更新钉钉文档的内容，支持覆盖和追加两种模式。

**⚠️ overwrite 模式会清空文档全部内容（包括图片、评论等），操作前请先确认用户意图，建议先用 get_document_content 备份。**

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 目标文档标识，支持 URL 或 ID 自动识别 |
| `markdown` | string | 是 | 要写入的 Markdown 内容 |
| `mode` | string | 否 | 更新模式，默认 `overwrite`。可选：`overwrite`（覆盖全文）、`append`（追加到末尾） |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodeId` | string | 文档节点 ID |
| `mode` | string | 使用的更新模式 |
| `suggestion` | string | 修复建议（仅失败时） |

**调用示例:**

```bash
# 覆盖写入（⚠️ 会清空原内容）
mcporter call dingtalk-docs update_document --args '{"nodeId": "doc_nodeId", "markdown": "# 新内容\n\n全量替换", "mode": "overwrite"}'

# 追加内容（安全，不影响现有内容）
mcporter call dingtalk-docs update_document --args '{"nodeId": "doc_nodeId", "markdown": "\n\n## 新章节\n追加的内容", "mode": "append"}'
```

---

## 5. get_document_info — 获取文档元信息

获取文档的元信息（标题、类型、创建时间等），不返回文档正文内容。适合在读取内容前先确认文档类型（contentType=ALIDOC 才支持 Markdown 读写）。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodeId` | string | 节点 ID |
| `workspaceId` | string | 所属知识库 ID |
| `name` | string | 文档标题（已剔除文件后缀） |
| `docUrl` | string | 文档访问链接 |
| `nodeType` | string | 节点类型：`folder` 或 `file` |
| `contentType` | string | 内容类型（nodeType=file 时）：`ALIDOC`/`DOCUMENT`/`IMAGE`/`VIDEO`/`AUDIO`/`ARCHIVE`/`OTHER` |
| `extension` | string | 文件后缀（不含点号） |
| `folderId` | string | 父文件夹节点 ID |
| `createTime` | integer | 创建时间（毫秒时间戳） |
| `updateTime` | integer | 最后变更时间（毫秒时间戳） |

**调用示例:**

```bash
mcporter call dingtalk-docs get_document_info --args '{"nodeId": "doc_nodeId"}'
```

---

## 6. create_folder — 创建文件夹

在指定位置创建一个新的文件夹。不传 folderId 时默认创建到用户"我的文档"根目录。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `name` | string | 是 | 新文件夹的名称 |
| `folderId` | string | 否 | 父文件夹节点 ID，支持 URL 或 ID。不传则创建到根目录 |
| `workspaceId` | string | 否 | 目标知识库 ID。同时传了 folderId 时以 folderId 为准 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodeId` | string | 新文件夹的节点 ID，可作为后续创建操作的 folderId |
| `name` | string | 文件夹名称 |
| `folderId` | string | 父文件夹节点 ID |
| `docUrl` | string | 文件夹访问链接 |
| `createTime` | integer | 创建时间（毫秒时间戳） |

**调用示例:**

```bash
# 在根目录创建文件夹
mcporter call dingtalk-docs create_folder --args '{"name": "2026 项目"}'

# 在指定文件夹下创建子文件夹
mcporter call dingtalk-docs create_folder --args '{"name": "子文件夹", "folderId": "parent_folder_nodeId"}'
```

---

## 7. list_nodes — 遍历文件列表

列出指定文件夹或知识库下的直接子节点列表，支持分页。返回结果基于当前用户的可访问权限过滤。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `folderId` | string | 否 | 要遍历的文件夹节点 ID，支持 URL 或 ID |
| `workspaceId` | string | 否 | 知识库 ID。同时传了 folderId 时以 folderId 为准 |
| `pageSize` | integer | 否 | 每页数量，默认 50，最大 50 |
| `pageToken` | string | 否 | 分页游标，从上一次返回的 nextPageToken 获取 |

**入参优先级：** `folderId` > `workspaceId` > 默认（我的文档根目录）

| 场景 | folderId | workspaceId | 遍历位置 |
|------|:--------:|:-----------:|---------|
| 指定文件夹 | ✅ 传入 | 可传可不传 | folderId 对应的文件夹 |
| 知识库根目录 | ❌ 不传 | ✅ 传入 | workspaceId 对应的知识库根目录 |
| 我的文档 | ❌ 不传 | ❌ 不传 | 用户"我的文档"根目录 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodes` | array | 子节点列表 |
| `nodes[].nodeId` | string | 节点 ID，可直接用于其他工具的 nodeId/folderId 参数 |
| `nodes[].workspaceId` | string | 所属知识库 ID |
| `nodes[].name` | string | 节点名称（已剔除文件后缀） |
| `nodes[].nodeType` | string | 节点类型：`folder`（目录）或 `file`（文件） |
| `nodes[].contentType` | string | 内容类型（nodeType=file 时）：`ALIDOC`/`DOCUMENT`/`IMAGE`/`VIDEO`/`AUDIO`/`ARCHIVE`/`OTHER` |
| `nodes[].extension` | string | 文件后缀（不含点号） |
| `nodes[].docUrl` | string | 访问链接 |
| `nodes[].createTime` | integer | 创建时间（毫秒时间戳） |
| `nodes[].updateTime` | integer | 最后变更时间（毫秒时间戳） |
| `nodes[].hasChildren` | boolean | 是否存在子节点（主要对 folder 有意义） |
| `hasMore` | boolean | 是否还有更多节点 |
| `nextPageToken` | string | 下一页游标（仅 hasMore=true 时返回） |

**nodeType 与 contentType 关系：**

| nodeType | contentType | 说明 |
|----------|------------|------|
| `folder` | —（不返回） | 文件夹，可递归遍历（hasChildren=true 时） |
| `file` | `ALIDOC` | 钉钉在线文档，可用 get_document_content 获取内容 |
| `file` | `DOCUMENT` | 本地文档（docx、xlsx、pptx、pdf 等） |
| `file` | `IMAGE` | 图片 |
| `file` | `VIDEO` | 视频 |
| `file` | `AUDIO` | 音频 |
| `file` | `ARCHIVE` | 压缩包 |
| `file` | `OTHER` | 其他文件 |

**调用示例:**

```bash
# 列出根目录
mcporter call dingtalk-docs list_nodes

# 列出指定文件夹
mcporter call dingtalk-docs list_nodes --args '{"folderId": "folder_nodeId"}'

# 分页获取
mcporter call dingtalk-docs list_nodes --args '{"folderId": "folder_nodeId", "pageSize": 10, "pageToken": "next_page_token"}'
```

---

## 完整工作流示例

### 创建文档并写入内容（一步完成）

```bash
# 直接创建带内容的文档，无需先获取根目录 ID
mcporter call dingtalk-docs create_document --args '{"name": "项目计划", "markdown": "# 项目计划\n\n## 目标\n完成 Q1 目标"}'
```

### 搜索并读取文档

```bash
# 1. 搜索文档，获取 nodeId
mcporter call dingtalk-docs search_documents --args '{"keyword": "项目"}'

# 2. 获取文档内容（直接用 nodeId，无需拼接 URL）
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "<step1返回的nodeId>"}'
```

### 遍历文件夹并读取 ALIDOC 文档

```bash
# 1. 列出文件夹内容
mcporter call dingtalk-docs list_nodes --args '{"folderId": "folder_nodeId"}'

# 2. 对 contentType=ALIDOC 的节点读取内容
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "<nodes[].nodeId>"}'
```

### 创建文件夹并在其中创建文档

```bash
# 1. 创建文件夹
mcporter call dingtalk-docs create_folder --args '{"name": "2026 项目"}'
# 返回 nodeId: "folder_abc123"

# 2. 在文件夹中创建文档
mcporter call dingtalk-docs create_document --args '{"name": "Q1 计划", "folderId": "folder_abc123"}'
```

### 追加内容到已有文档

```bash
# 1. 搜索文档
mcporter call dingtalk-docs search_documents --args '{"keyword": "周报"}'

# 2. 追加内容（不影响现有内容）
mcporter call dingtalk-docs update_document --args '{"nodeId": "<nodeId>", "markdown": "\n\n## 2026-W11\n本周完成了...", "mode": "append"}'
```

### 覆盖更新前先备份

```bash
# 1. 先读取现有内容作为备份
mcporter call dingtalk-docs get_document_content --args '{"nodeId": "doc_nodeId"}'

# 2. 确认用户意图后再覆盖
mcporter call dingtalk-docs update_document --args '{"nodeId": "doc_nodeId", "markdown": "# 全新内容", "mode": "overwrite"}'
```

### Block 精细编辑工作流

```bash
# 1. 查询文档块列表，获取 blockId
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "doc_nodeId"}'

# 2. 在指定块之后插入一个段落
mcporter call dingtalk-docs insert_document_block --args '{"nodeId": "doc_nodeId", "element": {"blockType": "paragraph", "paragraph": {"text": "新段落内容"}}, "referenceBlockId": "block_id", "where": "after"}'

# 3. 更新某个段落块的内容
mcporter call dingtalk-docs update_document_block --args '{"nodeId": "doc_nodeId", "blockId": "block_id", "element": {"paragraph": {"elements": [{"textRun": {"content": "更新后的内容"}}]}}}'

# 4. 删除指定块（不可恢复）
mcporter call dingtalk-docs delete_document_block --args '{"nodeId": "doc_nodeId", "blockId": "block_id"}'
```

---

## Block 精细编辑工具

> Block 工具用于对文档进行块级精细操作。块元素的完整数据结构请参考 [dingtalk_document_struct.md](../dingtalk_document_struct.md)。

### 公共说明

- **blockId**：块元素的唯一标识，通过 `list_document_blocks` 获取
- **element**：块元素数据对象，必须包含 `blockType` 字段及对应类型的属性对象
- 所有写操作（insert/update/delete）均需要对文档有**编辑权限**

---

## 8. list_document_blocks — 查询文档块列表

查询指定文档下的一级块元素列表（根节点下第一级 BlockElement），支持按起始/终止位置范围及块类型过滤。返回每个块的 `blockId`、`index` 和完整数据结构。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |
| `startIndex` | integer | 否 | 起始位置（≥0），从第 startIndex 个块开始查询，不传则从头开始 |
| `endIndex` | integer | 否 | 终止位置（≥0），查询到第 endIndex 个块为止（含），不传则查询到末尾 |
| `blockType` | string | 否 | 按块类型过滤，不传返回所有类型。枚举值见下表 |

**blockType 枚举值:**

| 值 | 说明 |
|---|---|
| `paragraph` | 段落块 |
| `heading` | 标题块 |
| `blockquote` | 引用块 |
| `callout` | 高亮块 |
| `columns` | 分栏块 |
| `orderedList` | 有序列表块 |
| `unorderedList` | 无序列表块 |
| `table` | 表格块 |
| `tableRow` | 表格行块 |
| `tableCell` | 表格单元格块 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `blocks` | array | 块元素列表 |
| `blocks[].blockId` | string | 块元素唯一标识，可用于 insert/update/delete 操作 |
| `blocks[].index` | integer | 块在文档根节点中的位置（从 0 开始） |
| `blocks[].blockType` | string | 块类型 |
| `blocks[].element` | object | 块的完整数据结构 |

**调用示例:**

```bash
# 查询所有块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "doc_nodeId"}'

# 查询第 0-5 个块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "doc_nodeId", "startIndex": 0, "endIndex": 5}'

# 只查询 heading 类型的块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "doc_nodeId", "blockType": "heading"}'
```

---

## 9. insert_document_block — 插入块元素

在指定文档的根目录中插入 1 个块元素，可指定插入位置和方向（之前/之后）。两者均不传时默认插入到文档末尾。目前仅支持插入到根目录（一级节点）。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |
| `element` | object | 是 | 块元素数据，必须包含 `blockType` 字段及对应类型的属性对象 |
| `referenceBlockId` | string | 否 | 参考块的 blockId，新块将插入到该块的前面或后面 |
| `index` | integer | 否 | 插入位置（≥0），与 referenceBlockId 二选一，同时传时以 referenceBlockId 为准 |
| `where` | string | 否 | 插入方向，默认 `after`。可选：`before`（之前）、`after`（之后） |

> ⚠️ **注意**：`heading.level` 参数必须传**字符串类型**（如 `"1"`），传整数会导致后端报错。

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `blockId` | string | 新插入块的 blockId |
| `blockType` | string | 新插入块的类型 |
| `index` | integer | 新块在文档中的位置 |
| `message` | string | 操作结果描述 |

**调用示例:**

```bash
# 插入段落到文档末尾
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "doc_nodeId",
  "element": {
    "blockType": "paragraph",
    "paragraph": {"text": "新段落内容"},
    "children": [{"text": "新段落内容"}]
  }
}'

# 在指定块之后插入标题（注意 level 必须是字符串）
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "doc_nodeId",
  "element": {
    "blockType": "heading",
    "heading": {"level": "2", "text": "二级标题"}
  },
  "referenceBlockId": "block_id",
  "where": "after"
}'

# 在指定块之前插入引用块
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "doc_nodeId",
  "element": {
    "blockType": "blockquote",
    "blockquote": {"indent": {"left": 32}},
    "children": [{"text": "引用内容"}]
  },
  "referenceBlockId": "block_id",
  "where": "before"
}'

# 插入表格（使用 dingtalk_document_struct.md 中的 table 结构）
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "doc_nodeId",
  "element": {
    "blockType": "table",
    "table": {
      "rolSize": 2,
      "colSize": 3,
      "cells": [["表头1", "表头2", "表头3"], ["数据1", "数据2", "数据3"]]
    }
  }
}'

# 插入高亮块（callout）
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "doc_nodeId",
  "element": {
    "blockType": "callout",
    "callout": {"sticker": "灯泡", "showstk": true, "bgcolor": "#FFF9C4", "border": "#FFD700"},
    "children": [{"blockType": "paragraph", "paragraph": {"text": "高亮内容"}}]
  }
}'
```

---

## 10. update_document_block — 更新块元素

更新指定文档中某一个块元素的属性。本操作为 **PATCH（局部更新）** 语义，只修改 `element` 中传入的字段，未传入的字段保持原值不变。

**⚠️ 目前仅支持更新 `paragraph`（段落）类型的块，其他类型会返回 `UNSUPPORTED_BLOCK_TYPE` 错误。**

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |
| `blockId` | string | 是 | 要更新的块的 blockId，通过 `list_document_blocks` 获取 |
| `element` | object | 是 | 要更新的块属性，PATCH 语义，只更新传入的字段 |

> ⚠️ **注意**：`indent` 参数类型为**对象**（如 `{"indentFirstLine": {"unit": "pt", "value": 24}}`），传入整数会报错。

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `blockId` | string | 被更新块的 blockId |
| `message` | string | 操作结果描述 |

**调用示例:**

```bash
# 更新段落文字内容
mcporter call dingtalk-docs update_document_block --args '{
  "nodeId": "doc_nodeId",
  "blockId": "block_id",
  "element": {
    "paragraph": {
      "elements": [{"textRun": {"content": "更新后的文字内容"}}]
    }
  }
}'

# 仅更新折叠状态（不影响文字）
mcporter call dingtalk-docs update_document_block --args '{
  "nodeId": "doc_nodeId",
  "blockId": "block_id",
  "element": {
    "paragraph": {"collapsed": true}
  }
}'

# 同时更新文字和缩进
mcporter call dingtalk-docs update_document_block --args '{
  "nodeId": "doc_nodeId",
  "blockId": "block_id",
  "element": {
    "paragraph": {
      "elements": [{"textRun": {"content": "更新后的文字"}}],
      "indent": {"indentFirstLine": {"unit": "pt", "value": 24}}
    }
  }
}'
```

---

## 11. delete_document_block — 删除块元素

删除指定文档中的某一个块元素。**此操作不可恢复**，删除前请先用 `list_document_blocks` 确认 blockId。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID 自动识别 |
| `blockId` | string | 是 | 要删除的块的 blockId，通过 `list_document_blocks` 获取 |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `blockId` | string | 被删除块的 blockId |
| `message` | string | 操作结果描述 |

**调用示例:**

```bash
# 删除指定块
mcporter call dingtalk-docs delete_document_block --args '{"nodeId": "doc_nodeId", "blockId": "block_id"}'
```

> **批量删除建议**：批量删除多个块时，建议**从后向前**按 index 倒序删除，避免删除后 index 位移导致定位错误。

---

## Block 工具错误码汇总

| 错误码 | 说明 |
|---|---|
| `ARGUMENT_ILLEGAL` | 参数非法：nodeId/blockId 为空、文档不存在、无访问权限、跨组织文档 |
| `BLOCK_NOT_FOUND` | 指定的 blockId 在文档中不存在 |
| `UNSUPPORTED_BLOCK_TYPE` | 不支持的块类型（update_document_block 目前仅支持 paragraph） |
| `invalidRequest.inputArgs.invalid` | 输入参数校验失败（如 startIndex > endIndex、blockType 枚举值非法） |

---

## 12. create_file — 创建文件

在指定位置创建一个新文件，支持钉钉在线文档、表格、演示、白板、脑图、多维表和文件夹七种类型。

**入参:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `name` | string | 是 | 新文件的名称 |
| `type` | string | 是 | 文件类型，枚举值见下表 |
| `folderId` | string | 否 | 目标文件夹节点 ID，支持 URL 或 ID。不传时：有 workspaceId 则创建在知识库根目录，否则创建在"我的文档"根目录 |
| `workspaceId` | string | 否 | 目标知识库 ID，支持知识库 ID 或知识库 URL。同时传了 folderId 时以 folderId 为准 |

**入参优先级：** `folderId` > `workspaceId` > 默认（我的文档根目录）

**`type` 枚举值:**

| type 值 | 兼容数字值 | 含义 | 返回 contentType |
|---------|:---------:|------|:---------------:|
| `adoc` | `"0"` | 钉钉在线文档 | `ALIDOC` |
| `axls` | `"1"` | 钉钉表格 | `WORKBOOK` |
| `appt` | `"2"` | 钉钉演示（PPT） | `PPT` |
| `adraw` | `"3"` | 钉钉白板 | `WBD` |
| `amind` | `"6"` | 钉钉脑图 | `MIND` |
| `able` | `"7"` | 钉钉多维表 | `NOTABLE` |
| `folder` | `"13"` | 文件夹 | `FOLDER` |

**出参:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodeId` | string | 新建节点的 ID（dentryUuid） |
| `name` | string | 节点名称 |
| `folderId` | string | 实际创建位置的父文件夹节点 ID |
| `nodeType` | string | 节点结构类型：`folder` 或 `file` |
| `contentType` | string | 内容类型（见 type 枚举表） |
| `extension` | string | 文件后缀（不含点号，如 `adoc`、`axls`） |
| `docUrl` | string | 节点访问链接 |
| `createTime` | integer | 创建时间（毫秒时间戳） |
| `lastEditTime` | integer | 最后编辑时间（毫秒时间戳） |
| `message` | string | 操作结果描述 |

**调用示例:**

```bash
# 创建钉钉在线文档到"我的文档"根目录
mcporter call dingtalk-docs create_file --args '{"name": "2026 Q2 计划", "type": "adoc"}'

# 在指定文件夹下创建表格
mcporter call dingtalk-docs create_file --args '{"name": "数据统计", "type": "axls", "folderId": "folder_nodeId"}'

# 在知识库根目录下创建多维表
mcporter call dingtalk-docs create_file --args '{"name": "项目看板", "type": "able", "workspaceId": "workspace_id"}'

# 在指定文件夹下创建子文件夹
mcporter call dingtalk-docs create_file --args '{"name": "2026 项目", "type": "folder", "folderId": "folder_nodeId"}'

# 创建脑图
mcporter call dingtalk-docs create_file --args '{"name": "架构设计", "type": "amind"}'

# 创建白板
mcporter call dingtalk-docs create_file --args '{"name": "头脑风暴", "type": "adraw"}'

# 创建演示文稿
mcporter call dingtalk-docs create_file --args '{"name": "季度汇报", "type": "appt"}'
```

**错误码:**

| 错误码 | 说明 |
|---|---|
| `invalidRequest.inputArgs.invalid` | 参数非法：name 为空、type 不在枚举范围、folderId 格式不合法（非 32 位字母数字字符串或 URL） |
| `ARGUMENT_ILLEGAL` | 目标位置不存在或无写入权限 |
