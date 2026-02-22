#!/bin/bash
# ─── Wolai MCP Server 一键安装脚本 ───
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Wolai MCP Server Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# 2. Install the package
echo "📥 Installing wolai-mcp..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -e . -q

# 3. Verify
echo ""
echo "✅ Installation complete!"
echo ""

# 4. Print the absolute path to the executable
EXEC_PATH="$SCRIPT_DIR/venv/bin/wolai-mcp"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Executable path:"
echo "   $EXEC_PATH"
echo ""

# 5. Print config templates
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Copy-paste configs below:"
echo ""

echo "── Claude Code (run in terminal) ──"
cat <<EOF
claude mcp add-json wolai-kb '{
  "type": "stdio",
  "command": "$EXEC_PATH"
}' --scope user
EOF

echo ""
echo "── Claude Desktop (add to ~/Library/Application Support/Claude/claude_desktop_config.json) ──"
cat <<EOF
{
  "mcpServers": {
    "wolai-kb": {
      "command": "$EXEC_PATH"
    }
  }
}
EOF

echo ""
echo "── Cursor (add to .cursor/mcp.json) ──"
cat <<EOF
{
  "mcpServers": {
    "wolai-kb": {
      "command": "$EXEC_PATH"
    }
  }
}
EOF

echo ""
echo "🎉 Done! Pick the config above for your platform and paste it in."
