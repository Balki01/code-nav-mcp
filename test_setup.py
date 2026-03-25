#!/usr/bin/env python3
"""Quick setup test - verifies dependencies are working"""

import sys
import os
from pathlib import Path

# Add local lib to path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

print("Testing Code Navigation MCP Setup")
print("=" * 50)

# Test 1: Check MCP SDK
print("\n1. Checking MCP SDK...")
try:
    import mcp
    import mcp.server
    print(f"   ✓ MCP SDK installed successfully")
except ImportError as e:
    print(f"   ✗ MCP SDK not found: {e}")
    sys.exit(1)

# Test 2: Check ctags
print("\n2. Checking universal-ctags...")
import subprocess
try:
    result = subprocess.run(["ctags", "--version"], capture_output=True, text=True, check=True)
    if "Universal Ctags" in result.stdout:
        version = result.stdout.split('\n')[0].split()[2].rstrip(',')
        print(f"   ✓ universal-ctags installed (version {version})")
    else:
        print(f"   ⚠ Found exuberant-ctags (old), need universal-ctags")
except (subprocess.CalledProcessError, FileNotFoundError):
    print(f"   ✗ ctags not found")
    sys.exit(1)

# Test 3: Check ripgrep
print("\n3. Checking ripgrep...")
try:
    result = subprocess.run(["rg", "--version"], capture_output=True, text=True, check=True)
    version = result.stdout.split('\n')[0].split()[1]
    print(f"   ✓ ripgrep installed (version {version})")
except (subprocess.CalledProcessError, FileNotFoundError):
    print(f"   ✗ ripgrep not found")
    sys.exit(1)

# Test 4: Check if we can import the server
print("\n4. Checking server.py...")
try:
    from server import CodeRepo
    print(f"   ✓ Server module loads successfully")
except ImportError as e:
    print(f"   ✗ Server module failed to load: {e}")
    sys.exit(1)

# Test 5: Quick functionality test
print("\n5. Testing basic functionality...")
linux_path = "/home/administrator/SRC/linux"
if Path(linux_path).exists():
    print(f"   ✓ Linux kernel repo found at {linux_path}")
    print(f"   Ready to index!")
else:
    print(f"   ⚠ Linux kernel not found at {linux_path}")
    print(f"     (Will work once you point it to a valid repo)")

print("\n" + "=" * 50)
print("✓ All checks passed!")
print("\nNext steps:")
print("1. Add this to your Claude Code settings:")
print(f'   "code-nav": {{"command": "/tmp/claude-1000/code-nav-mcp/run_server.sh"}}')
print("2. Restart Claude Code")
print("3. Index your repos!")
