# Data Structures

An online document is a tree composed of block elements. Different types of `BlockElement` support different nestable child element types. For example, a `callout` block can nest any `BlockElement`, while a `paragraph` block can only nest `InlineElement`.

A single block element has the following structure:

```tsx
{
  "blockType": enum(BlockType),             // Block element type, see BlockType enum below
  /**
   * The following are all supported Block types, such as Heading, Paragraph.
   * Each block type has its own specific property object.
   */
  "blockquote": Object(Callout),
  "callout": Object(Callout),
  "columns": Object(Columns),
  "heading": Object(Heading),
  "paragraph": Object(Paragraph),
  "orderedList": Object(OrderedList),
  "unorderedList": Object(UnorderedList),
  "table": Object(Table),
  // Each Block type has its own supported BlockChildren, see each Block type's `children` description
  "children": BlockChildren[],
}
```

## BlockElement Reference

An online document is a tree structure composed of **block elements (BlockElement)**. Different block types support different child element types:
- `callout` and `columns`: `children` must be a **BlockElement array**
- `paragraph`, `heading`, `orderedList`, `unorderedList`, `blockquote`: `children` must be an **InlineElement array**
- `table`: `children` is **not supported**

---

### BlockType Enum

| Value | Description |
|---|---|
| `paragraph` | Paragraph block |
| `heading` | Heading block |
| `blockquote` | Blockquote block |
| `callout` | Callout (highlight) block |
| `columns` | Columns (multi-column layout) block |
| `orderedList` | Ordered list block |
| `unorderedList` | Unordered list block |
| `table` | Table block |
| `tableRow` | Table row block (child of table) |
| `tableCell` | Table cell block (child of table) |

> Unsupported element types are returned as `Undefined`.

---

### 1. Paragraph

```json
{
  "blockType": "paragraph",
  "paragraph": {
    "text": "Paragraph text content",
    "indent": { "left": 32 },
    "folded": false
  },
  "children": [InlineElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `text` | string | No | Text content of the paragraph |
| `indent` | object(Indent) | No | Indentation; `left` must be a positive integer |
| `folded` | boolean | No | Whether to fold blocks with a larger indent value than this paragraph |

- `children`: **InlineElement array**
- The `paragraph` object **must not be omitted**; pass `{}` when content is empty

---

### 2. Heading

```json
{
  "blockType": "heading",
  "heading": {
    "level": 1,
    "text": "Heading Level 1"
  },
  "children": [InlineElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `text` | string | No | Heading text content |
| `level` | integer(enum) | No | Heading level, `1`–`6`; 1 = H1 |

- `children`: **InlineElement array**

---

### 3. Blockquote

```json
{
  "blockType": "blockquote",
  "blockquote": {
    "text": "Quoted content",
    "indent": { "left": 32 }
  },
  "children": [InlineElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `text` | string | No | Text inside the blockquote |
| `indent` | object(Indent) | No | Indentation value |

- `children`: **InlineElement array**

---

### 4. Callout

```json
{
  "blockType": "callout",
  "callout": {
    "sticker": "灯泡",
    "showstk": true,
    "color": "#333333",
    "border": "#FFD700",
    "bgcolor": "#FFF9C4"
  },
  "children": [BlockElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `sticker` | string(enum Emoji) | No | Emoji code, see Emoji enum |
| `showstk` | boolean | No | Whether to display the emoji |
| `color` | string | No | Text color |
| `border` | string | No | Border color |
| `bgcolor` | string | No | Background color |

- `children`: **BlockElement array** (InlineElement is not allowed)

---

### 5. Columns

```json
{
  "blockType": "columns",
  "columns": {
    "size": 2,
    "noFill": false
  },
  "children": [BlockElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `size` | number | No | Number of columns |
| `noFill` | boolean | No | Whether to disable automatic background fill |

- `children`: **BlockElement array** (InlineElement is not allowed)

---

### 6. Ordered List

```json
{
  "blockType": "orderedList",
  "orderedList": {
    "list": {
      "listId": "list-001",
      "level": 0,
      "listStyleType": "decimal",
      "listStyle": {
        "format": "decimal",
        "text": "%1.",
        "align": "left"
      },
      "symbolStyle": {
        "bold": false
      }
    },
    "indent": { "left": 32 }
  },
  "children": [InlineElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `list` | object(ListObject) | Yes | Ordered list properties, see ListObject |
| `indent` | object(Indent) | No | Indentation; `left` must be a positive integer |

- `children`: **InlineElement array**

---

### 7. Unordered List

```json
{
  "blockType": "unorderedList",
  "unorderedList": {
    "list": {
      "listId": "list-002",
      "level": 0,
      "listStyleType": "disc",
      "listStyle": {
        "format": "disc",
        "text": "%1",
        "align": "left"
      },
      "symbolStyle": {
        "bold": false
      }
    },
    "indent": { "left": 32 }
  },
  "children": [InlineElement]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `list` | object(ListObject) | Yes | Unordered list properties, see ListObject |
| `indent` | object(Indent) | No | Indentation; `left` must be a positive integer |

- `children`: **InlineElement array**

---

### 8. Table

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

| Field | Type | Required | Description |
|---|---|---:|---|
| `rolSize` | number | Yes | Number of rows |
| `colSize` | number | Yes | Number of columns |
| `cells` | string[][] | No | Cell text content as a 2D string array |

- `children`: **Not supported**

---

## InlineElement Reference

Inline elements are used in the `children` of text-based block elements (paragraph, heading, list, etc.).

### InlineType Enum

| Value | Description |
|---|---|
| `text` | Text |
| `sticker` | Emoji |
| `image` | Image |
| `link` | Hyperlink |

---

### Text

```json
{
  "text": "Bold red text",
  "sz": 16,
  "color": "red",
  "highlight": "yellow",
  "bold": true,
  "italic": false,
  "stike": false,
  "underline": false,
  "fonts": "monospace"
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `text` | string | Yes | Text content |
| `sz` | number | No | Font size (px) |
| `color` | string | No | Text color |
| `highlight` | string | No | Highlight background color |
| `bold` | boolean | No | Bold |
| `italic` | boolean | No | Italic |
| `stike` | boolean | No | Strikethrough |
| `underline` | boolean | No | Underline |
| `fonts` | string(enum Fonts) | No | Font family, see Fonts enum |

**Fonts Enum**

| Value | Description |
|---|---|
| `monospace` | Monospace |
| `STSong` | STSong |
| `Microsoft YaHei` | Microsoft YaHei |
| `FangSong_GB2312` | FangSong GB2312 |
| `Helvetica` | Helvetica |
| `Helvetica Neue` | Helvetica Neue |
| `Consolas` | Consolas |
| `宋体` | SimSun |
| `Impact` | Impact |
| `sanrif` | Sanrif |
| `Calibri` | Calibri |

---

### Emoji (sticker)

```json
{
  "elementType": "sticker",
  "properties": {
    "code": "大笑"
  }
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `code` | string(enum Emoji) | Yes | Emoji code, see Emoji enum |

---

### Image

```json
{
  "elementType": "image",
  "properties": {
    "src": "https://example.com/image.jpg"
  }
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `src` | string | No | Image URL |

---

### Link

```json
{
  "elementType": "link",
  "properties": {
    "href": "https://example.com"
  },
  "children": [
    { "text": "Click to open link" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---:|---|
| `href` | string | No | Link URL |

- `children`: **Text array** — required when inserting a link; must contain at least one text node with a non-empty `text` field.

---

## Common Data Structures

### Indent

| Field | Type | Required | Description | Example |
|---|---|---:|---|---|
| `left` | number | No | Indentation value; must be a positive integer, otherwise an error is returned | `32` |

---

### ListObject

| Field | Type | Required | Description |
|---|---|---:|---|
| `listId` | string | No | List ID. For multi-level ordered lists, all items in the same group must share the same `listId`; otherwise the display will be incorrect |
| `level` | number | Yes | List nesting level (starts from 0) |
| `listStyleType` | string | Yes | List style type |
| `listStyle` | object(ListStyle) | Yes | List style details, see ListStyle |
| `symbolStyle` | object(SymbolStyle) | No | Bullet/number symbol style, see SymbolStyle |

---

### ListStyle

| Field | Type | Required | Description |
|---|---|---:|---|
| `format` | string | Yes | Bullet format |
| `text` | string | Yes | Text template |
| `align` | string | Yes | Alignment: `left`, `center`, or `right` |

---

### SymbolStyle

| Field | Type | Required | Description |
|---|---|---:|---|
| `sz` | number | No | Symbol font size |
| `shd` | string | No | Symbol background color |
| `fonts` | string | No | Symbol font family |
| `color` | string | No | Symbol font color |
| `bold` | boolean | No | Bold |
| `strike` | boolean | No | Strikethrough |
| `italic` | boolean | No | Italic |

---

## Emoji Enum (Complete List)

The following values can be used in `callout.sticker` and inline sticker elements (`sticker.properties.code`).

| | | | |
|---|---|---|---|
| `优先级: 1` | `优先级: 2` | `优先级: 3` | `优先级: 4` |
| `优先级: 5` | `优先级: 6` | `优先级: 7` | `进度: 未开始` |
| `进度: 20%` | `进度: 40%` | `进度: 50%` | `进度: 70%` |
| `进度: 90%` | `进度: 已完成` | `微笑` | `憨笑` |
| `大笑` | `加油` | `色` | `偷笑` |
| `跳舞` | `捂脸哭` | `笑哭` | `流泪` |
| `疑问` | `傻笑` | `流鼻血` | `狗子` |
| `赞` | `OK` | `抱拳` | `向上` |
| `向下` | `向左` | `向右` | `资料` |
| `本子` | `笔记本` | `折线图` | `柱状图` |
| `羽毛笔` | `钢笔` | `警告` | `问号` |
| `禁止` | `禁行` | `锁` | `气泡` |
| `沙漏` | `公文包` | `火箭` | `火` |
| `奖牌` | `灯泡` | `钉子` | `旗子` |
| `茶` | `休假` | `气球` | `锦鲤` |
| `咖啡` | `奶茶` | `调色板` | `感谢` |
| `打招呼` | `666` | `握手` | `胜利` |
| `一点点` | `鼓掌` | `送花花` | `比心` |
| `加一` | `100分` | `KPI` | `对勾` |
| `爱心` | `可爱` | `发呆` | `老板` |
| `害羞` | `闭嘴` | `睡` | `大哭` |
| `尴尬` | `调皮` | `惊讶` | `流汗` |
| `广播` | `自信` | `你强` | `怒吼` |
| `惊愕` | `快哭了` | `无聊` | `吐` |
| `算账` | `晕` | `摸摸` | `飞吻` |
| `鄙视` | `嘘` | `思考` | `亲亲` |
| `感冒` | `对不起` | `再见` | `投降` |
| `哼` | `欠扁` | `坏笑` | `拜托` |
| `可怜` | `舒服` | `爱意` | `财迷` |
| `迷惑` | `PK` | `委屈` | `灵感` |
| `天使` | `鬼脸` | `凄凉` | `郁闷` |
| `吃瓜` | `嘿嘿` | `抠鼻` | `呲牙` |
| `彩虹` | `耶` | `捂眼睛` | `推眼镜` |
| `暗中观察` | `开心` | `惊喜` | `回头` |
| `发怒` | `忍者` | `衰` | `脑暴` |
| `冷笑` | `黑眼圈` | `恭喜` | `费解` |
| `收到` | `炸弹` | `白眼` | `一团乱麻` |
| `无奈` | `敲打` | `专注` | `忙疯了` |
| `鞠躬` | `摊手` | `抱抱` | `举手` |
| `跪了` | `猫咪` | `二哈` | `三多` |
| `承让` | `撒花` | `邮件` | `文档` |
| `演示` | `表格` | `生日快乐` | `心碎` |
| `红包` | `嘴唇` | `鲜花` | `残花` |
| `干杯` | `出差` | `时间` | `福` |
| `月饼` | `礼物` | `幼苗` | `烟花` |
| `灯笼` | `爆竹` | `鸡腿` | `高铁` |
| `三连` | `OKR` | `Done` | |
