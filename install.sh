#!/bin/bash
set -e

echo "==================================="
echo "Code Navigation MCP Server Installer"
echo "==================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python3 found"

# Check/install MCP SDK
echo ""
echo "Installing MCP Python SDK..."
pip install -q mcp || pip3 install -q mcp
echo "✓ MCP SDK installed"

# Check ctags
echo ""
if ! command -v ctags &> /dev/null; then
    echo "⚠️  universal-ctags not found"
    echo "   Install with: sudo apt install universal-ctags"
    echo "   (Required for symbol indexing)"
    MISSING_DEPS=1
else
    # Check if it's universal-ctags (not exuberant-ctags)
    if ctags --version | grep -q "Universal Ctags"; then
        echo "✓ universal-ctags found"
    else
        echo "⚠️  Found old exuberant-ctags, need universal-ctags"
        echo "   Install with: sudo apt install universal-ctags"
        MISSING_DEPS=1
    fi
fi

# Check ripgrep
echo ""
if ! command -v rg &> /dev/null; then
    echo "⚠️  ripgrep not found"
    echo "   Install with: sudo apt install ripgrep"
    echo "   (Required for reference search)"
    MISSING_DEPS=1
else
    echo "✓ ripgrep found"
fi

# Make server executable
echo ""
chmod +x server.py
echo "✓ Made server.py executable"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Show configuration instructions
echo ""
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo ""

if [ -n "$MISSING_DEPS" ]; then
    echo "⚠️  Some dependencies are missing. Install them with:"
    echo ""
    echo "  sudo apt install universal-ctags ripgrep"
    echo ""
fi

echo "Next steps:"
echo ""
echo "1. Add this to your Claude Code settings (~/.claude/settings.json):"
echo ""
echo '   "mcpServers": {'
echo '     "code-nav": {'
echo '       "command": "python3",'
echo "       \"args\": [\"$SCRIPT_DIR/server.py\"]"
echo '     }'
echo '   }'
echo ""
echo "2. Or use the /update-config skill in Claude Code"
echo ""
echo "3. Restart Claude Code"
echo ""
echo "4. In Claude Code, say:"
echo '   "Add my Linux kernel repo at /home/administrator/SRC/linux to code-nav"'
echo ""
echo "See QUICKSTART.md for detailed usage examples."
echo ""
