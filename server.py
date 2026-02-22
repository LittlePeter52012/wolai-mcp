import requests
import json
import sys
import argparse

# Check if mcp is installed
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' package is not installed. Please install it with: pip install 'mcp[cli]'")
    sys.exit(1)

# Initialize FastMCP Server
mcp = FastMCP("wolai-knowledge-base")

# Configuration
APP_ID = "REDACTED_APP_ID"
APP_SECRET = "REDACTED_OLD_APP_SECRET"
BASE_URL = "https://openapi.wolai.com/v1"

# The user's root page ID (changes annually)
DEFAULT_ROOT_ID = "REDACTED_ROOT_ID"

# Global token storage
_token = None

def get_token():
    """Retrieve or refresh the authentication token."""
    global _token
    if _token:
        return _token

    url = f"{BASE_URL}/token"
    payload = {
        "appId": APP_ID,
        "appSecret": APP_SECRET
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
    """Get standard headers for requests."""
    return {
        "Authorization": get_token(),
        "Content-Type": "application/json"
    }

def parse_wolai_content(content_obj) -> str:
    """
    Parses Wolai's complex content structure: a list of rich text objects.
    Example: [{'title': 'Hello', 'type': 'text'}, {'title': 'World', 'bold': True}]
    """
    if not content_obj or not isinstance(content_obj, list):
        return str(content_obj or "")
    
    text_parts = []
    for item in content_obj:
        title = item.get("title", "")
        # Add minimal style cues if needed, but keep it clean for AI
        if item.get("bold"):
            title = f"**{title}**"
        if item.get("italic"):
            title = f"*{title}*"
        text_parts.append(title)
    
    return "".join(text_parts)

@mcp.tool()
def get_root_info() -> str:
    """Returns the current Root ID and its basic info (Annual Index)."""
    headers = get_headers()
    try:
        res = requests.get(f"{BASE_URL}/blocks/{DEFAULT_ROOT_ID}", headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", {})
            title = parse_wolai_content(data.get("content", ""))
            return f"Current Root Directory: '{title}' (ID: {DEFAULT_ROOT_ID})"
    except:
        pass
    return f"Default Root ID: {DEFAULT_ROOT_ID}"

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
            # Wolai sometimes uses 'content' or nested structures
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
def search_pages_by_title(query: str, start_id: str = DEFAULT_ROOT_ID, max_depth: int = 2) -> str:
    """
    Finds pages with titles containing the query string, starting from a root ID.
    Since Wolai lacks a global search API, this tool explores the page tree.
    
    Args:
        query: The keyword to search for in page titles.
        start_id: The ID to start searching from (default is your annual root).
        max_depth: How many levels deep to search (default 2 to save time).
    """
    found = []
    visited = set()
    queue = [(start_id, 0)] # (id, current_depth)
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
                        # Follow pages or headers that might contain other pages
                        if child.get("type") in ["page", "heading_1", "heading_2"]:
                            queue.append((child.get("id"), depth + 1))
        
        if not found:
            return f"No pages matching '{query}' found within depth {max_depth} of {start_id}."
        
        return "\n".join(found)
    except Exception as e:
        return f"Search error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
