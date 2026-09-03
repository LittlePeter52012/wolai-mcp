"""
Wolai MCP Server entry point.
Directly runs the package implementation in src/wolai_mcp/server.py.
"""
import sys
from pathlib import Path

# Ensure src is on sys.path for direct execution: python server.py
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from wolai_mcp.server import main, mcp

if __name__ == "__main__":
    main()
