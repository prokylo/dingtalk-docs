# 钉钉云文档 Block API 参考 (v1.0)

> Block 精细编辑工具的完整参数 Schema 和块元素数据结构。
> 适用于需要精确控制文档结构的场景（在指定位置插入、修改、删除块元素）。
> 常规的文档内容读写请使用 `update_document` / `get_document_content`，无需使用 Block API。

---

## Block 工具概览

| 工具 | 用途 | 必填参数 |
|------|------|---------|
| `list_document_blocks` | 查询文档一级块列表，获取 blockId | nodeId |
| `insert_document_block` | 在指定位置插入一个块元素 | nodeId, element |
| `update_document_block` | 更新指定块元素（PATCH 语义，仅支持 paragraph） | nodeId, blockId, element |
| `delete_document_block` | 删除指定块元素（不可恢复） | nodeId, blockId |

**重要限制：**
- 所有 Block 工具仅操作**一级块元素**（根节点直接子节点），不支持嵌套层级
- `update_document_block` 当前仅支持 `paragraph` 类型
- `delete_document_block` 不可恢复，删除含子块的块（callout/columns/table）时子块一并删除

---

## 1. list_document_blocks — 查询块列表

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID |
| `startIndex` | integer | 否 | 起始位置（≥0），不传则从头开始 |
| `endIndex` | integer | 否 | 终止位置（≥0，含），不传则到末尾 |
| `blockType` | string | 否 | 按块类型过滤，见 BlockType 枚举 |

**返回值:**

```json
{
  "success": true,
  "blocks": [
    {
      "blockId": "mmpzx96vb8asm77jil",
      "index": 0,
      "blockType": "heading",
      "element": { "blockType": "heading", "heading": { "level": 1, "text": "文档标题" } }
    },
    {
      "blockId": "mmpzx96ve10038tufl",
      "index": 1,
      "blockType": "paragraph",
      "element": { "blockType": "paragraph", "paragraph": { "text": "段落内容" } }
    }
  ]
}
```

**关键字段:**
- `blocks[].blockId` — 块唯一标识，用于 `update_document_block` / `delete_document_block` 的 blockId
- `blocks[].index` — 块在文档中的位置（从 0 开始），用于 `insert_document_block` 的 index 参数

**调用示例:**

```bash
# 查询全部块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "docNodeId"}'

# 查询第 1~3 个块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "docNodeId", "startIndex": 1, "endIndex": 3}'

# 只查询段落块
mcporter call dingtalk-docs list_document_blocks --args '{"nodeId": "docNodeId", "blockType": "paragraph"}'
```

---

## 2. insert_document_block — 插入块元素

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID |
| `element` | object | 是 | 待插入的块元素，必须包含 blockType 及对应属性对象 |
| `referenceBlockId` | string | 否 | 参照块 ID（由 list_document_blocks 获取），优先级高于 index |
| `index` | integer | 否 | 参照位置索引（从 0 开始）。两者均不传则追加到末尾 |
| `where` | string | 否 | 插入方向：`before`（之前）或 `after`（之后，默认） |

**返回值:**

```json
{ "success": true, "blockId": "新块的blockId" }
```

**调用示例:**

```bash
# 在文档末尾插入段落
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "docNodeId",
  "element": {"blockType": "paragraph", "paragraph": {}, "children": [{"text": "新段落"}]}
}'

# 在指定块之后插入二级标题（level 传整数）
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "docNodeId",
  "referenceBlockId": "mmpzx96vb8asm77jil",
  "where": "after",
  "element": {"blockType": "heading", "heading": {"level": 2}, "children": [{"text": "新章节"}]}
}'

# 在指定块之前插入无序列表
mcporter call dingtalk-docs insert_document_block --args '{
  "nodeId": "docNodeId",
  "referenceBlockId": "mmpzx96vb8asm77jil",
  "where": "before",
  "element": {"blockType": "unorderedList", "unorderedList": {"list": {"level": 0, "listStyleType": "disc", "listStyle": {"format": "disc", "text": "%1", "align": "left"}}}, "children": [{"text": "列表项"}]}
}'
```

---

## 3. update_document_block — 更新块元素

**PATCH 语义**：只修改传入的字段，未传入的字段保持原值不变。当前仅支持 `paragraph` 类型。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID |
| `blockId` | string | 是 | 目标块 ID（由 list_document_blocks 获取） |
| `element` | object | 是 | 更新内容，必须包含 blockType 及对应属性（当前仅支持 paragraph） |

**返回值:**

```json
{ "success": true }
```

**调用示例:**

```bash
# 修改段落文字（不影响其他属性）
mcporter call dingtalk-docs update_document_block --args '{
  "nodeId": "docNodeId",
  "blockId": "mmpzx96ve10038tufl",
  "element": {"blockType": "paragraph", "paragraph": {}, "children": [{"text": "更新后的内容"}]}
}'

# 设置段落折叠（不影响文字）
mcporter call dingtalk-docs update_document_block --args '{
  "nodeId": "docNodeId",
  "blockId": "mmpzx96ve10038tufl",
  "element": {"blockType": "paragraph", "paragraph": {"folded": true}}
}'
```

---

## 4. delete_document_block — 删除块元素

**⚠️ 删除不可恢复。删除含子块的块（callout/columns/table）时，所有子块一并删除。**

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `nodeId` | string | 是 | 文档标识，支持 URL 或 ID |
| `blockId` | string | 是 | 目标块 ID（由 list_document_blocks 获取） |

**返回值:**

```json
{ "success": true }
```

**调用示例:**

```bash
# 删除指定块（先确认 blockId）
mcporter call dingtalk-docs delete_document_block --args '{"nodeId": "docNodeId", "blockId": "mmpzx97482905xaj5dy"}'
```

**批量删除建议：** 按 index 从后向前删除，避免索引位移导致误删。

---

## 附录 A：BlockType 枚举

| 枚举值 | 描述 | 支持 insert | 支持 update |
|--------|------|:-----------:|:-----------:|
| `paragraph` | 段落 | ✅ | ✅ |
| `heading` | 标题（level 1-6） | ✅ | ❌ |
| `blockquote` | 引用块 | ✅ | ❌ |
| `callout` | 高亮块 | ✅ | ❌ |
| `columns` | 分栏块 | ✅ | ❌ |
| `orderedList` | 有序列表 | ✅ | ❌ |
| `unorderedList` | 无序列表 | ✅ | ❌ |
| `table` | 表格 | ✅ | ❌ |
| `sheet` | 电子表格 | ✅ | ❌ |
| `attachment` | 附件 | ✅ | ❌ |
| `slot` | 插槽 | ✅ | ❌ |

---

## 附录 B：块元素数据结构（insert 时使用）

### children 规则

- `paragraph`、`heading`、`orderedList`、`unorderedList`、`blockquote` 的 `children` → **InlineElement 数组**
- `callout`、`columns` 的 `children` → **BlockElement 数组**
- `table` 暂不支持指定 `children`

**⚠️ 高频易错点：**
- `paragraph` 属性对象**不可省略**，内容为空时须传 `"paragraph": {}`（`blockquote` 同理）
- `heading.level` **必须传整数**（`1` 而非 `"1"`），传字符串会导致后端报错
- 列表块的 `list` 字段**必填**，不可省略
- 多级有序列表同组须保持相同 `listId`，否则展示错误

### B.1 段落（paragraph）

```json
{
  "blockType": "paragraph",
  "paragraph": { "text": "段落文字", "indent": { "left": 32 }, "folded": false },
  "children": [{ "text": "加粗文字", "bold": true }, { "text": "普通文字" }]
}
```

### B.2 标题（heading）

```json
{
  "blockType": "heading",
  "heading": { "level": 1 },
  "children": [{ "text": "一级标题" }]
}
```

`level` 取值 1～6（整数），1 表示一级标题。**⚠️ 必须传整数，传字符串 `"1"` 会报错。**

### B.3 引用（blockquote）

```json
{
  "blockType": "blockquote",
  "blockquote": {},
  "children": [{ "text": "引用内容" }]
}
```

**⚠️ `blockquote` 属性对象不可省略，内容为空时须传 `{}`。**

### B.4 分栏（columns）

```json
{
  "blockType": "columns",
  "columns": { "size": 2, "noFill": false },
  "children": [
    { "blockType": "paragraph", "paragraph": {}, "children": [{ "text": "左栏内容" }] },
    { "blockType": "paragraph", "paragraph": {}, "children": [{ "text": "右栏内容" }] }
  ]
}
```

`size` 为分栏数量，`children` 为 **BlockElement 数组**（不能是 InlineElement）。

### B.5 高亮块（callout）

```json
{
  "blockType": "callout",
  "callout": { "sticker": "灯泡", "showstk": true, "bgcolor": "#FFF9C4", "border": "#FFD700" },
  "children": [
    { "blockType": "paragraph", "paragraph": {}, "children": [{ "text": "高亮块内容" }] }
  ]
}
```

sticker 可选值见附录 D（Emoji 枚举）。

### B.6 有序列表（orderedList）

```json
{
  "blockType": "orderedList",
  "orderedList": {
    "list": { "listId": "list-001", "level": 0, "listStyleType": "decimal",
              "listStyle": { "format": "decimal", "text": "%1.", "align": "left" } }
  },
  "children": [{ "text": "列表项内容" }]
}
```

同组多级列表需保持 `listId` 一致，`level` 从 0 开始。

### B.7 无序列表（unorderedList）

```json
{
  "blockType": "unorderedList",
  "unorderedList": {
    "list": { "listId": "list-002", "level": 0, "listStyleType": "disc",
              "listStyle": { "format": "disc", "text": "%1", "align": "left" } }
  },
  "children": [{ "text": "列表项内容" }]
}
```

### B.8 表格（table）

```json
{
  "blockType": "table",
  "table": {
    "rolSize": 3,
    "colSize": 4,
    "cells": [
      ["Row1-Col1", "Row1-Col2", "Row1-Col3", "Row1-Col4"],
      ["Row2-Col1", "Row2-Col2", "Row2-Col3", "Row2-Col4"],
      ["Row3-Col1", "Row3-Col2", "Row3-Col3", "Row3-Col4"]
    ]
  }
}
```

`rolSize`（行数）和 `colSize`（列数）必填，`cells` 为二维字符串数组。

---

## 附录 C：InlineElement 数据结构

行内元素用于文本类块元素的 `children` 中。

### C.1 文本（text）

```json
{ "text": "加粗红色文字", "bold": true, "color": "red", "highlight": "yellow",
  "italic": false, "underline": false, "stike": false, "sz": 16, "fonts": "monospace" }
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 文本内容（必填） |
| `bold` | boolean | 加粗 |
| `italic` | boolean | 斜体 |
| `underline` | boolean | 下划线 |
| `stike` | boolean | 中划线 |
| `color` | string | 文字颜色 |
| `highlight` | string | 高亮背景色 |
| `sz` | number | 字号（px） |
| `fonts` | string | 字体：`monospace`/`Microsoft YaHei`/`Helvetica` 等 |

### C.2 链接（link）

```json
{
  "elementType": "link",
  "properties": { "href": "https://example.com" },
  "children": [{ "text": "点击跳转" }]
}
```

插入链接时 `children` 必须包含至少 1 个 text 不为空的文本节点。

### C.3 图片（image）

```json
{ "elementType": "image", "properties": { "src": "https://example.com/image.jpg" } }
```

---

## 附录 D：常用 Emoji 枚举（callout sticker）

`灯泡` `警告` `对勾` `禁止` `火箭` `火` `赞` `100分` `KPI` `OKR` `Done`
`优先级: 1` `优先级: 2` `优先级: 3` `进度: 未开始` `进度: 已完成`
`大笑` `流泪` `思考` `疑问` `惊讶` `加油` `鼓掌` `撒花` `握手`

> 完整枚举值区分全角/半角及大小写，请严格按照上述格式填写。
