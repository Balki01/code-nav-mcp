#!/usr/bin/env python3
"""
Local test script for code-nav MCP server
Tests core functionality without running full MCP server
"""

import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from server import CodeRepo


def test_repo_indexing():
    """Test repository indexing"""
    print("Test 1: Repository Indexing")
    print("-" * 50)

    linux_path = "/home/administrator/SRC/linux"

    if not Path(linux_path).exists():
        print(f"⚠️  Linux kernel not found at {linux_path}")
        print("   Skipping indexing test")
        return

    print(f"Indexing {linux_path}...")
    repo = CodeRepo("linux", linux_path, "test-branch")

    result = repo.index()
    print(f"Result: {result}")

    if repo.tags_file.exists():
        print("✓ Tags file created successfully")
        print(f"  Location: {repo.tags_file}")
    else:
        print("❌ Tags file not created")

    print()


def test_symbol_lookup():
    """Test symbol lookup"""
    print("Test 2: Symbol Lookup")
    print("-" * 50)

    linux_path = "/home/administrator/SRC/linux"

    if not Path(linux_path).exists():
        print(f"⚠️  Linux kernel not found at {linux_path}")
        return

    repo = CodeRepo("linux", linux_path)

    # Check if already indexed
    if not repo.tags_file.exists():
        print("Indexing first...")
        repo.index()

    print("Looking for symbol: 'isc_awb_work'")
    results = repo.find_symbol("isc_awb_work", kind="function")

    if results:
        print(f"✓ Found {len(results)} definition(s):")
        for r in results:
            print(f"  {r.file}:{r.line}")
            print(f"    Kind: {r.kind}")
            print(f"    Code: {r.pattern[:80]}...")
    else:
        print("❌ Symbol not found")

    print()


def test_references():
    """Test reference search"""
    print("Test 3: Reference Search")
    print("-" * 50)

    linux_path = "/home/administrator/SRC/linux"

    if not Path(linux_path).exists():
        print(f"⚠️  Linux kernel not found at {linux_path}")
        return

    repo = CodeRepo("linux", linux_path)

    print("Looking for references to: 'V4L2_CID_AUTO_WHITE_BALANCE'")
    results = repo.find_references("V4L2_CID_AUTO_WHITE_BALANCE", context=1)

    if results:
        print(f"✓ Found {len(results)} reference(s) (showing first 5):")
        for r in results[:5]:
            print(f"  {r.file}:{r.line}")
            print(f"    {r.content[:80]}...")
    else:
        print("⚠️  No references found")

    print()


def test_git_operations():
    """Test git integration"""
    print("Test 4: Git Operations")
    print("-" * 50)

    linux_path = "/home/administrator/SRC/linux"

    if not Path(linux_path).exists():
        print(f"⚠️  Linux kernel not found at {linux_path}")
        return

    repo = CodeRepo("linux", linux_path)

    print("Git log for symbol: 'isc_awb_work'")
    result = repo.git_show_symbol("isc_awb_work")

    if result and "No commits" not in result:
        print("✓ Git history found:")
        print(result[:300])
        if len(result) > 300:
            print("  ...")
    else:
        print("⚠️  No git history found")

    print()


def main():
    """Run all tests"""
    print("=" * 50)
    print("Code Navigation MCP Server - Local Tests")
    print("=" * 50)
    print()

    # Check dependencies
    import subprocess

    print("Checking dependencies...")
    deps = {
        "ctags": "universal-ctags",
        "rg": "ripgrep"
    }

    for cmd, pkg in deps.items():
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print(f"  ✓ {cmd} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ❌ {cmd} not found (install: {pkg})")

    print()

    # Run tests
    test_repo_indexing()
    test_symbol_lookup()
    test_references()
    test_git_operations()

    print("=" * 50)
    print("Tests Complete!")
    print("=" * 50)
    print()
    print("If all tests passed, the MCP server is ready to use.")
    print("Run install.sh for setup instructions.")


if __name__ == "__main__":
    main()
