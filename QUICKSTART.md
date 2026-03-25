# Quick Start Guide

## 5-Minute Setup

### Step 1: Install (2 minutes)

```bash
cd /home/administrator/SRC/code-nav-mcp
pip install -r requirements.txt

# Install system tools if needed
sudo apt install universal-ctags ripgrep
```

### Step 2: Configure Claude Code (1 minute)

Use the `/update-config` skill to add the MCP server:

```
Hey Claude, add this MCP server to my settings:

{
  "mcpServers": {
    "code-nav": {
      "command": "python3",
      "args": ["/home/administrator/SRC/code-nav-mcp/server.py"]
    }
  }
}
```

Or manually edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "code-nav": {
      "command": "python3",
      "args": ["/home/administrator/SRC/code-nav-mcp/server.py"]
    }
  }
}
```

### Step 3: Restart Claude Code (30 seconds)

Exit and restart Claude Code to load the MCP server.

### Step 4: Index Your Repos (2 minutes)

In your next Claude Code session:

```
Add these repos to code-nav MCP:
1. Linux kernel at /home/administrator/SRC/linux (branch: balki/isc-6.18-fixes)
2. libcamera at /work5/balki/SRC_BUILD/libcamera (branch: mchp-next-v2-v0.6.0)
```

Claude will use the MCP tools to index both repos.

### Step 5: Start Navigating! (instant)

```
Find where isc_awb_work is defined
```

```
Show me all callers of isc_update_awb_ctrls
```

```
Git blame the isc_s_awb_ctrl function
```

## Example Session

```
User: Find where V4L2_CID_AUTO_WHITE_BALANCE is used in the ISC driver

Claude: [Uses code-nav MCP find_references tool]
Found 15 references:
- microchip-isc-base.c:1629 - inactive check
- microchip-isc-base.c:2119 - cluster setup
- microchip_isc_ipa.cpp:234 - IPA sets AWB=0
...

User: Read just line 1629 from that file

Claude: [Uses Read tool with specific line]
...
```

**Result**: Found the bug location in 5 seconds, used ~1K tokens instead of 50K!

## Common Use Cases

### Use Case 1: Find a Function Definition

**Traditional (expensive):**
```
"Read all files in drivers/media/platform/microchip/ and find isc_awb_work"
→ Reads 10+ files, 10K+ lines, 80K tokens
```

**With code-nav MCP (efficient):**
```
"Find isc_awb_work definition"
→ Uses find_symbol tool
→ Returns: microchip-isc-base.c:1503
→ 50 tokens
```

**Savings: 99.9%**

### Use Case 2: Understand Call Chains

**Traditional:**
```
"Who calls isc_update_awb_ctrls? Read all files that might call it"
→ Read many files, grep manually, cross-reference
→ 50K+ tokens
```

**With code-nav MCP:**
```
"Find all callers of isc_update_awb_ctrls"
→ Uses find_callers tool
→ Returns structured list of call sites
→ 1K tokens
```

**Savings: 98%**

### Use Case 3: Git History Investigation

**Traditional:**
```
"Run git blame on microchip-isc-base.c and show me who last changed the AWB control handler"
→ Run bash git blame
→ Read entire blame output (2000+ lines)
→ 30K tokens
```

**With code-nav MCP:**
```
"Who last modified isc_s_awb_ctrl?"
→ Uses git_blame_function tool
→ Returns just the function's blame
→ 500 tokens
```

**Savings: 98%**

## Pro Tips

1. **Always search before reading** - Use find_symbol/find_references first to get exact locations
2. **Use repo filters** - Narrow searches with `repo="linux"` parameter
3. **Combine with Read tool** - After finding location, read just that range
4. **Re-index after big changes** - If you checkout a different branch, re-run add_repo

## Verification

Check if MCP server is loaded:

```
User: "List all indexed repos in code-nav"

Claude: [Uses list_repos tool]
Indexed Repositories:

• linux
  Path: /home/administrator/SRC/linux
  Branch: balki/isc-6.18-fixes
  Tags: ✓ indexed

• libcamera
  Path: /work5/balki/SRC_BUILD/libcamera
  Branch: mchp-next-v2-v0.6.0
  Tags: ✓ indexed
```

If you see this, everything is working! 🎉

## Troubleshooting

**"MCP server not found"**
- Make sure you restarted Claude Code after adding the config
- Check the path in settings.json is correct

**"ctags command not found"**
```bash
sudo apt install universal-ctags
```

**"Indexing failed"**
- Check repo path exists
- Make sure you have read permissions
- Try a smaller repo first to test

## Next Steps

- Save this workflow to memory: "Remember I have code-nav MCP set up for efficient kernel debugging"
- Update your investigation workflow to always search before reading
- Enjoy 90%+ token savings on your kernel work!
