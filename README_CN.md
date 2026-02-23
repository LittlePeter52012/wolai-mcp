<p align="center">
  <img src="wolai-mcp.jpeg" width="120" alt="Wolai MCP Icon">
</p>

# Wolai MCP Server 🐺

[English](README.md) | **中文**

[![PyPI](https://img.shields.io/pypi/v/wolai-mcp)](https://pypi.org/project/wolai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**通过 MCP 协议将 AI 智能体连接到你的 [Wolai](https://www.wolai.com) 知识库。**

从 Claude、Gemini、Cursor 或任何 MCP 兼容的 AI 智能体中读取、写入、搜索和管理你的 Wolai 页面。

---

## ✨ 功能一览

| 类别   | 工具                                                                        | 说明                                |
| ------ | --------------------------------------------------------------------------- | ----------------------------------- |
| 📖 读取 | `get_page_content`, `list_child_blocks`, `get_root_info`, `get_breadcrumbs` | 读取页面、列出子页面、导航层级结构  |
| 🔍 搜索 | `search_pages_by_title`                                                     | 按标题模糊搜索页面树                |
| ✏️ 写入 | `create_page`, `add_block`, `add_code_block`                                | 创建页面、添加文本/列表/标题/代码块 |
| ⚙️ 配置 | `set_wolai_credentials`, `set_root_page`, `get_wolai_config`                | 运行时凭证和根页面管理              |

**共 11 个工具** — 覆盖读取、写入、搜索和配置功能。

---

## 🚀 快速开始

### 方式一：`uvx` 直接运行（推荐）

无需安装，在临时隔离环境中直接运行：

```bash
uvx wolai-mcp
```

> 没有 `uv`？一键安装：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 方式二：`pip` 安装

```bash
pip install wolai-mcp
```

### 获取凭证

1. 前往 [Wolai 开发者平台](https://www.wolai.com/dev)
2. 创建应用 → 获取 **App ID** 和 **App Secret**
3. 从 Wolai 页面 URL 中获取**根页面 ID**

---

## 📋 配置

所有凭证通过**环境变量**传入 — 无需修改任何代码。

| 变量               | 说明            | 必填                  |
| ------------------ | --------------- | --------------------- |
| `WOLAI_APP_ID`     | Wolai 应用 ID   | ✅                     |
| `WOLAI_APP_SECRET` | Wolai 应用密钥  | ✅                     |
| `WOLAI_ROOT_ID`    | 知识库根页面 ID | 可选（用于搜索/导航） |

---

## 🔧 各平台配置方式

### Claude Desktop

添加到 `claude_desktop_config.json`：

<table><tr><th>uvx 方式（推荐）</th><th>pip 方式</th></tr><tr><td>

```json
{
  "mcpServers": {
    "wolai-kb": {
      "command": "uvx",
      "args": ["wolai-mcp"],
      "env": {
        "WOLAI_APP_ID": "你的应用ID",
        "WOLAI_APP_SECRET": "你的密钥",
        "WOLAI_ROOT_ID": "你的根页面ID"
      }
    }
  }
}
```

</td><td>

```json
{
  "mcpServers": {
    "wolai-kb": {
      "command": "wolai-mcp",
      "env": {
        "WOLAI_APP_ID": "你的应用ID",
        "WOLAI_APP_SECRET": "你的密钥",
        "WOLAI_ROOT_ID": "你的根页面ID"
      }
    }
  }
}
```

</td></tr></table>

### Gemini CLI

添加到 `~/.gemini/settings.json`：

```json
{
  "mcpServers": {
    "wolai-kb": {
      "command": "wolai-mcp",
      "env": {
        "WOLAI_APP_ID": "你的应用ID",
        "WOLAI_APP_SECRET": "你的密钥",
        "WOLAI_ROOT_ID": "你的根页面ID"
      }
    }
  }
}
```

### Cursor / CherryStudio / 其他 MCP 客户端

<table><tr><th>uvx 方式</th><th>pip 方式</th></tr><tr><td>

```json
{
  "wolai-kb": {
    "command": "uvx",
    "args": ["wolai-mcp"],
    "env": {
      "WOLAI_APP_ID": "你的应用ID",
      "WOLAI_APP_SECRET": "你的密钥",
      "WOLAI_ROOT_ID": "你的根页面ID"
    }
  }
}
```

</td><td>

```json
{
  "wolai-kb": {
    "command": "wolai-mcp",
    "env": {
      "WOLAI_APP_ID": "你的应用ID",
      "WOLAI_APP_SECRET": "你的密钥",
      "WOLAI_ROOT_ID": "你的根页面ID"
    }
  }
}
```

</td></tr></table>

---

## 💡 使用示例

配置完成后，可以直接对 AI 智能体说：

- *"读取我 Wolai 知识库的首页内容"*
- *"搜索标题包含'项目计划'的页面"*
- *"在首页下创建一个新页面叫'会议纪要'"*
- *"往指定页面添加一段代码"*
- *"显示当前 Wolai 配置状态"*

---

## 🔐 运行时配置

无需重启即可更换配置：

- **`set_wolai_credentials`** — 切换 Wolai 账号
- **`set_root_page`** — 更换知识库根页面
- **`get_wolai_config`** — 查看当前配置

---

## 📄 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。
