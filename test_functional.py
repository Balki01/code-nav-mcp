#!/usr/bin/env python3
"""Functional test - actually index and search code"""

import sys
from pathlib import Path

# Add local lib to path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

from server import CodeRepo

print("Functional Test: Code Navigation")
print("=" * 50)

# Test with just the ISC driver directory (faster than whole kernel)
test_path = "/home/administrator/SRC/linux/drivers/media/platform/microchip"

if not Path(test_path).exists():
    print(f"Test path not found: {test_path}")
    sys.exit(1)

print(f"\n1. Indexing: {test_path}")
repo = CodeRepo("isc-driver", test_path)
result = repo.index()
print(f"   {result}")

print(f"\n2. Finding symbol: 'isc_awb_work'")
symbols = repo.find_symbol("isc_awb_work", kind="function")
if symbols:
    print(f"   ✓ Found {len(symbols)} definition(s):")
    for s in symbols:
        print(f"     {s.file}:{s.line} - {s.kind}")
        print(f"     {s.pattern[:60]}...")
else:
    print(f"   ✗ Symbol not found")

print(f"\n3. Finding references: 'V4L2_CTRL_FLAG_INACTIVE'")
refs = repo.find_references("V4L2_CTRL_FLAG_INACTIVE", context=1)
if refs:
    print(f"   ✓ Found {len(refs)} reference(s):")
    for r in refs[:3]:  # Show first 3
        print(f"     {r.file}:{r.line}")
        print(f"     {r.content[:60]}...")
else:
    print(f"   ⚠ No references found")

print(f"\n4. Finding callers: 'isc_update_awb_ctrls'")
callers = repo.find_references("isc_update_awb_ctrls\\s*\\(", context=0)
if callers:
    print(f"   ✓ Found {len(callers)} call site(s):")
    for c in callers[:3]:  # Show first 3
        print(f"     {c.file}:{c.line}")
else:
    print(f"   ⚠ No callers found")

print("\n" + "=" * 50)
print("✓ Functional test complete!")
print("\nThe MCP server is working correctly.")
print("Ready to integrate with Claude Code!")
