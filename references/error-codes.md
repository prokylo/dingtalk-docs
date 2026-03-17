# 钉钉云文档错误码参考 (v1.0)

> SKILL.md 的按需加载参考文件。遇到错误时查阅此文档。
>
> **每次 API 调用都会返回 `logId`（请求追踪 ID），遇到问题时请保存该值提供给技术支持。**

## 错误码速查表

| 错误信息 / 错误码 | 原因 | 修复动作 |
|------------------|------|----------|
| `Invalid credentials` / 401 | 凭证配置错误、令牌过期，或配置的是**旧版 MCP URL** | 访问 [钉钉文档 MCP 广场](https://mcp.dingtalk.com/#/detail?mcpId=9629) 获取新版 StreamableHttp URL，执行 `mcporter config add dingtalk-docs --url "<新版URL>"` |
| `Permission denied` / `PERMISSION_DENIED` | 当前用户无权限操作该文档/文件夹 | 确认文档分享权限，检查是否只读，联系文档所有者授权 |
| `Document not found` / `NODE_NOT_FOUND` | nodeId 无效或文档已删除 | 确认 nodeId 来自返回值（禁止编造），用 `search_documents` 重新搜索 |
| `UNSUPPORTED_BLOCK_TYPE` | `update_document_block` 传入了非 paragraph 类型的块 | 当前仅支持更新 paragraph 类型，其他类型请用 `update_document(mode="overwrite")` 替代 |
| `BLOCK_NOT_FOUND` | blockId 不存在或不属于该文档的一级块 | 先调 `list_document_blocks` 重新获取最新 blockId |
| `UNSUPPORTED_CONTENT_TYPE` | 对表格/PPT/PDF 等非 ALIDOC 文档调用内容读写 | 先用 `get_document_info` 确认 contentType=ALIDOC，非 ALIDOC 文档不支持 Markdown 读写 |
| `CROSS_ORG_NOT_ALLOWED` | 文档属于其他组织 | 不支持跨组织操作，确认文档属于当前用户所在组织 |
| `Timeout` | 网络超时 | 检查网络连接，稍后重试；提供 logId 给技术支持 |
| `Invalid parameter` | 参数格式错误 | 见下方参数说明 |
| 看到旧工具名（如 `list_accessible_documents`、`write_content_to_document`） | 配置的是旧版 MCP URL | 升级到新版 MCP URL（同 Invalid credentials 修复步骤） |

## 新版参数说明

新版 API 参数体系已简化，不再有旧版的类型陷阱：

| 参数 | 新版格式 | 旧版对比 |
|------|---------|---------|
| `nodeId` | 字符串，支持 URL 或 ID 自动识别 | 旧版需手动拼完整 URL |
| `mode` | 字符串枚举：`"overwrite"` 或 `"append"` | 旧版 updateType=0/1（数字，易传错） |
| `folderId` | 字符串，支持 URL 或 ID | 旧版 parentDentryUuid（仅支持 ID） |

## 调试流程

```
1. 保存 logId → 每次 API 返回都包含，遇到问题时提供给技术支持
2. 检查错误码 → 对照上方速查表
3. 确认 nodeId 来源 → 必须从 API 返回值中提取，禁止编造
4. 确认文档类型 → get_document_info 确认 contentType=ALIDOC 才能读写内容
5. 检查权限 → 确认用户对文档/文件夹有操作权限
6. 检查 MCP URL 版本 → 新版工具名以 search_documents / create_document 等为准
7. 重试 → 排除服务端临时故障
```

## 日志位置

```bash
~/.mcporter/logs/      # mcporter 日志
~/.openclaw/logs/      # 技能执行日志
```
