"""
Wolai MCP Server — Connect AI agents to your Wolai knowledge base.
All credentials are configured via environment variables in your MCP settings.
"""
import os
import requests
import json
import sys

# Check if mcp is installed
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' package is not installed. Please install it with: pip install 'mcp[cli]'")
    sys.exit(1)

# Initialize FastMCP Server
mcp = FastMCP("wolai-knowledge-base")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  🔑  所有密钥通过环境变量传入，在 MCP 配置文件 env 中设置       ║
# ║  WOLAI_APP_ID      — Wolai 应用 ID                              ║
# ║  WOLAI_APP_SECRET   — Wolai 应用密钥                             ║
# ║  WOLAI_ROOT_ID      — 知识库根页面 ID                            ║
# ║  获取地址: https://www.wolai.com/dev                             ║
# ╚═══════════════════════════════════════════════════════════════════╝

BASE_URL = "https://openapi.wolai.com/v1"

# ─── Auth ─────────────────────────────────────────────────────────────────────
_token = None


def _get_app_id() -> str:
    val = os.environ.get("WOLAI_APP_ID", "")
    if not val:
        raise ValueError(
            "WOLAI_APP_ID is not set. "
            "Set it in your MCP config env or via set_wolai_credentials tool."
        )
    return val


def _get_app_secret() -> str:
    val = os.environ.get("WOLAI_APP_SECRET", "")
    if not val:
        raise ValueError(
            "WOLAI_APP_SECRET is not set. "
            "Set it in your MCP config env or via set_wolai_credentials tool."
        )
    return val


def _get_root_id() -> str:
    return os.environ.get("WOLAI_ROOT_ID", "")


def get_token():
    """Retrieve or refresh the authentication token."""
    global _token
    if _token:
        return _token

    url = f"{BASE_URL}/token"
    payload = {
        "appId": _get_app_id(),
        "appSecret": _get_app_secret(),
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "app_token" in data["data"]:
            _token = data["data"]["app_token"]
            return _token
        else:
            raise ValueError(f"Failed to retrieve token: {data}")
    except Exception as e:
        print(f"Auth Error: {e}", file=sys.stderr)
        raise


def get_headers():
    """Get standard headers for API requests."""
    return {
        "Authorization": get_token(),
        "Content-Type": "application/json"
    }

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_wolai_content(content_obj) -> str:
    """
    Parses Wolai's complex content structure: a list of rich text objects.
    Example: [{'title': 'Hello', 'type': 'text'}, {'title': 'World', 'bold': True}]
    """
    if not content_obj or not isinstance(content_obj, list):
        return str(content_obj or "")

    text_parts = []
    for item in content_obj:
        if not isinstance(item, dict):
            text_parts.append(str(item))
            continue
        title = item.get("title", "")
        if item.get("bold"):
            title = f"**{title}**"
        if item.get("italic"):
            title = f"*{title}*"
        text_parts.append(title)

    return "".join(text_parts)


# ═══════════════════════════════════════════════
#  Configuration Tools
# ═══════════════════════════════════════════════

@mcp.tool()
def set_wolai_credentials(app_id: str, app_secret: str) -> str:
    """
    Set or update the Wolai API credentials at runtime.
    This allows switching accounts without restarting the server.
    The credentials persist for the current session only.

    Args:
        app_id: Your Wolai App ID (get from https://www.wolai.com/dev).
        app_secret: Your Wolai App Secret.
    """
    global _token
    if not app_id or not app_secret:
        return "❌ Both app_id and app_secret are required."
    os.environ["WOLAI_APP_ID"] = app_id
    os.environ["WOLAI_APP_SECRET"] = app_secret
    _token = None  # Force re-auth with new credentials
    # Verify
    try:
        get_token()
        return "✅ Wolai credentials set and verified! Authentication successful."
    except Exception as e:
        os.environ.pop("WOLAI_APP_ID", None)
        os.environ.pop("WOLAI_APP_SECRET", None)
        return f"❌ Credential verification failed: {e}. Credentials were not saved."


@mcp.tool()
def set_root_page(root_id: str) -> str:
    """
    Change the root page ID for knowledge base operations.
    This controls which page is used as the starting point for searches and navigation.

    Args:
        root_id: The Wolai page ID to use as the new root.
    """
    if not root_id:
        return "❌ root_id is required."
    os.environ["WOLAI_ROOT_ID"] = root_id
    # Verify the page exists
    try:
        headers = get_headers()
        res = requests.get(f"{BASE_URL}/blocks/{root_id}", headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", {})
            title = parse_wolai_content(data.get("content", ""))
            return f"✅ Root page set to: '{title}' (ID: {root_id})"
        else:
            return f"⚠️ Root page set to {root_id}, but could not verify (status {res.status_code})"
    except Exception as e:
        return f"⚠️ Root page set to {root_id}, but verification failed: {e}"


@mcp.tool()
def get_wolai_config() -> str:
    """
    Show the current Wolai MCP configuration status.
    """
    app_id = os.environ.get("WOLAI_APP_ID", "")
    app_secret = os.environ.get("WOLAI_APP_SECRET", "")
    root_id = _get_root_id()

    id_status = f"✅ {app_id[:8]}..." if app_id else "❌ Not set"
    secret_status = f"✅ ...{app_secret[-8:]}" if app_secret else "❌ Not set"
    root_status = f"✅ {root_id}" if root_id else "❌ Not set"
    auth_status = "✅ Authenticated" if _token else "⏳ Not yet authenticated"

    return (
        f"🔧 Wolai MCP Configuration\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  App ID:      {id_status}\n"
        f"  App Secret:  {secret_status}\n"
        f"  Root Page:   {root_status}\n"
        f"  Auth Token:  {auth_status}\n"
        f"  API URL:     {BASE_URL}\n"
        f"  Get credentials: https://www.wolai.com/dev"
    )


# ═══════════════════════════════════════════════
#  Read Tools
# ═══════════════════════════════════════════════

@mcp.tool()
def get_root_info() -> str:
    """Returns the current Root ID and its basic info (Annual Index page)."""
    root_id = _get_root_id()
    if not root_id:
        return "❌ WOLAI_ROOT_ID is not set. Use set_root_page or set it in your MCP config env."
    headers = get_headers()
    try:
        res = requests.get(f"{BASE_URL}/blocks/{root_id}", headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", {})
            title = parse_wolai_content(data.get("content", ""))
            return f"Current Root Directory: '{title}' (ID: {root_id})"
    except Exception:
        pass
    return f"Default Root ID: {root_id}"


@mcp.tool()
def get_page_content(block_id: str) -> str:
    """
    Retrieves the content of a specific Wolai page or block by its ID.

    Args:
        block_id: The ID of the block/page to read.
    """
    url = f"{BASE_URL}/blocks/{block_id}"
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        block_data = response.json().get("data", {})

        children_url = f"{BASE_URL}/blocks/{block_id}/children"
        children_response = requests.get(children_url, headers=headers)
        children_response.raise_for_status()
        children_data = children_response.json().get("data", [])

        title = parse_wolai_content(block_data.get("content", ""))
        content_lines = [f"# Page: {title} (ID: {block_id})"]

        for child in children_data:
            c_type = child.get("type", "text")
            raw_content = child.get("content", "")
            c_content = parse_wolai_content(raw_content)

            if not c_content and c_type != "divider":
                continue

            if c_type == "heading_1":
                content_lines.append(f"# {c_content}")
            elif c_type == "heading_2":
                content_lines.append(f"## {c_content}")
            elif c_type == "heading_3":
                content_lines.append(f"### {c_content}")
            elif c_type == "text":
                content_lines.append(c_content)
            elif c_type == "bulleted_list":
                content_lines.append(f"- {c_content}")
            elif c_type == "numbered_list":
                content_lines.append(f"1. {c_content}")
            elif c_type == "callout":
                content_lines.append(f"> 💡 {c_content}")
            elif c_type in ["code", "python", "javascript", "java"]:
                content_lines.append(f"```\n{c_content}\n```")
            elif c_type == "page":
                content_lines.append(f"📄 [Child Page]: {c_content} (ID: {child.get('id')})")
            elif c_type == "divider":
                content_lines.append("---")
            else:
                content_lines.append(f"[{c_type}]: {c_content}")

        return "\n\n".join(content_lines)
    except Exception as e:
        return f"Error reading page {block_id}: {str(e)}"


@mcp.tool()
def list_child_blocks(block_id: str) -> str:
    """
    Lists the immediate child blocks/pages of a given block ID.

    Args:
        block_id: The ID of the parent block/page.
    """
    url = f"{BASE_URL}/blocks/{block_id}/children"
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json().get("data", [])

        if not data:
            return "No children found."

        results = []
        for child in data:
            c_type = child.get("type", "unknown")
            c_id = child.get("id", "")
            c_content = parse_wolai_content(child.get("content", ""))
            if not c_content:
                c_content = "(Empty)" if c_type != "divider" else "---"
            results.append(f"- [{c_type}] {c_content} (ID: {c_id})")

        return "\n".join(results)
    except Exception as e:
        return f"Error listing children for {block_id}: {str(e)}"


@mcp.tool()
def search_pages_by_title(query: str, start_id: str = "", max_depth: int = 2) -> str:
    """
    Finds pages with titles containing the query string, starting from a root ID.
    Since Wolai lacks a global search API, this tool explores the page tree.

    Args:
        query: The keyword to search for in page titles.
        start_id: The ID to start searching from (default is your annual root).
        max_depth: How many levels deep to search (default 2 to save time).
    """
    if not start_id:
        start_id = _get_root_id()
    if not start_id:
        return "❌ No root page set. Use set_root_page or provide start_id."

    found = []
    visited = set()
    queue = [(start_id, 0)]
    headers = get_headers()

    try:
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)

            res = requests.get(f"{BASE_URL}/blocks/{current_id}", headers=headers)
            if res.status_code == 200:
                data = res.json().get("data", {})
                title = parse_wolai_content(data.get("content", ""))
                if query.lower() in title.lower():
                    found.append(f"- FOUND: {title} (ID: {current_id}) at depth {depth}")

            if depth < max_depth:
                c_res = requests.get(f"{BASE_URL}/blocks/{current_id}/children", headers=headers)
                if c_res.status_code == 200:
                    children = c_res.json().get("data", [])
                    for child in children:
                        if child.get("type") in ["page", "heading_1", "heading_2"]:
                            queue.append((child.get("id"), depth + 1))

        if not found:
            return f"No pages matching '{query}' found within depth {max_depth} of {start_id}."

        return "\n".join(found)
    except Exception as e:
        return f"Search error: {str(e)}"


@mcp.tool()
def get_breadcrumbs(block_id: str) -> str:
    """
    Returns the full path from the root to a given block, showing the page hierarchy.
    Example output: "Root > Projects > My Project > Today's Note"

    Args:
        block_id: The ID of the block/page to trace back to root.
    """
    crumbs = []
    current_id = block_id
    headers = get_headers()
    visited = set()

    try:
        while current_id and current_id not in visited:
            visited.add(current_id)
            res = requests.get(f"{BASE_URL}/blocks/{current_id}", headers=headers)
            if res.status_code != 200:
                break
            data = res.json().get("data", {})
            title = parse_wolai_content(data.get("content", ""))
            crumbs.append(title or current_id)

            parent_id = data.get("parent_id", "")
            if not parent_id or parent_id == current_id:
                break
            current_id = parent_id

        crumbs.reverse()
        return " > ".join(crumbs) if crumbs else f"Could not resolve path for {block_id}"
    except Exception as e:
        return f"Error getting breadcrumbs: {str(e)}"


# ═══════════════════════════════════════════════
#  Write Helpers
# ═══════════════════════════════════════════════

# Verified against live Wolai API (2026-02):
#   ✅ text, heading (level 1-3), enum_list, bull_list, todo_list,
#      toggle_list, quote, callout, divider, page, bookmark, image,
#      video, block_equation, code (needs 'language' field)

# User-friendly aliases → (Wolai API type, heading level or None)
_TYPE_ALIAS_MAP = {
    # Headings
    "heading":        ("heading", 1),
    "heading_1":      ("heading", 1),
    "heading_2":      ("heading", 2),
    "heading_3":      ("heading", 3),
    "h1":             ("heading", 1),
    "h2":             ("heading", 2),
    "h3":             ("heading", 3),
    # Lists
    "bullet":         ("enum_list", None),
    "bulleted_list":  ("enum_list", None),
    "ul":             ("enum_list", None),
    "numbered_list":  ("bull_list", None),
    "ol":             ("bull_list", None),
    "todo":           ("todo_list", None),
    "checkbox":       ("todo_list", None),
    "toggle":         ("toggle_list", None),
    "toggle_list":    ("toggle_list", None),
    # Other aliases
    "math":           ("block_equation", None),
    "equation":       ("block_equation", None),
    "block_equation": ("block_equation", None),
    "hr":             ("divider", None),
}


def build_block_object(content: str, block_type: str = "text") -> dict:
    """
    Builds a Wolai block object from plain text and a block type string.
    Maps user-friendly aliases to the actual Wolai API type names.
    """
    if block_type in _TYPE_ALIAS_MAP:
        resolved_type, level = _TYPE_ALIAS_MAP[block_type]
    else:
        resolved_type, level = block_type, None

    block = {
        "type": resolved_type,
        "content": [{"title": content}],
    }

    # Headings need a 'level' field (1, 2, or 3)
    if resolved_type == "heading":
        block["level"] = level or 1

    # Todo blocks need a 'checked' field
    if resolved_type == "todo_list":
        block["checked"] = False

    # Divider has no content
    if resolved_type == "divider":
        block.pop("content", None)

    return block


def _extract_id_from_response(data) -> str:
    """Extract block ID from Wolai's POST /blocks response (list of URLs)."""
    if data and isinstance(data, list):
        url_or_id = data[0]
        if isinstance(url_or_id, str):
            fragment = url_or_id.rsplit("#", 1)[-1] if "#" in url_or_id else url_or_id.rsplit("/", 1)[-1]
            return fragment
        elif isinstance(url_or_id, dict):
            return url_or_id.get("id", "unknown")
    return "unknown"


# ═══════════════════════════════════════════════
#  Write Tools
# ═══════════════════════════════════════════════

@mcp.tool()
def create_page(title: str, parent_id: str = "") -> str:
    """
    Creates a new empty sub-page under a given parent page.

    Args:
        title: The title of the new page.
        parent_id: ID of the parent page. Defaults to the knowledge-base root.
    """
    if not parent_id:
        parent_id = _get_root_id()
    if not parent_id:
        return "❌ No parent_id provided and WOLAI_ROOT_ID is not set."

    payload = {
        "parent_id": parent_id,
        "blocks": [
            {
                "type": "page",
                "content": [{"title": title}],
            }
        ],
    }

    try:
        response = requests.post(
            f"{BASE_URL}/blocks", json=payload, headers=get_headers()
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        new_id = _extract_id_from_response(data)
        return f"✅ Page '{title}' created successfully (ID: {new_id}, parent: {parent_id})"
    except Exception as e:
        return f"❌ Failed to create page: {str(e)}"


@mcp.tool()
def add_block(parent_id: str, content: str, block_type: str = "text") -> str:
    """
    Appends one or more content blocks to a page.
    Separate lines with newlines to create multiple blocks.

    Args:
        parent_id: The page or block ID to append content to.
        content: The text content. Use newlines to create multiple blocks.
        block_type: One of:
            - text (default)
            - heading / h1 / heading_1, h2 / heading_2, h3 / heading_3
            - bullet / bulleted_list / ul  (unordered list)
            - ol / numbered_list  (ordered list)
            - todo / checkbox  (to-do item)
            - toggle / toggle_list  (collapsible)
            - quote, callout
            - divider / hr
            - math / equation / block_equation
            - image, video, bookmark  (content = URL)
    """
    # Divider is special: one block, no per-line split
    if block_type in ("divider", "hr"):
        blocks = [build_block_object("", block_type)]
    else:
        lines = [line for line in content.split("\n") if line.strip()]
        if not lines:
            return "⚠️ No content provided."
        blocks = [build_block_object(line, block_type) for line in lines]

    payload = {
        "parent_id": parent_id,
        "blocks": blocks,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/blocks", json=payload, headers=get_headers()
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        count = len(data) if isinstance(data, list) else 1
        return f"✅ Added {count} block(s) of type '{block_type}' to {parent_id}"
    except Exception as e:
        return f"❌ Failed to add block: {str(e)}"


@mcp.tool()
def add_code_block(parent_id: str, code: str, language: str = "python") -> str:
    """
    Appends a code block with syntax highlighting to a page.

    Args:
        parent_id: The page or block ID to append the code to.
        code: The source code content.
        language: Programming language for syntax highlighting
                  (e.g. python, javascript, java, c, cpp, go, rust, sql, bash, json, yaml, markdown, html, css).
    """
    block = {
        "type": "code",
        "content": [{"title": code}],
        "language": language.lower(),
    }

    payload = {
        "parent_id": parent_id,
        "blocks": [block],
    }

    try:
        response = requests.post(
            f"{BASE_URL}/blocks", json=payload, headers=get_headers()
        )
        response.raise_for_status()
        return f"✅ Added code block ({language}) to {parent_id}"
    except Exception as e:
        return f"❌ Failed to add code block: {str(e)}"


# ═══════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════

def main():
    """Entry point for the `wolai-mcp` CLI command."""
    mcp.run()

if __name__ == "__main__":
    main()
