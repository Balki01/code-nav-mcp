# Code Navigation MCP - Usage Examples

Real-world examples showing token savings for kernel development.

## Example 1: Finding a Bug in AWB Control Handler

### Scenario
You notice that IPA WB gains aren't being applied. You suspect the control handler might be checking for inactive flags.

### Traditional Approach (❌ High Token Usage)

**User:** "Find where V4L2_CTRL_FLAG_INACTIVE is checked in the ISC driver"

**Claude reads:**
1. All files in `drivers/media/platform/microchip/` (5 files, 8000 lines)
2. Related header files (3 files, 2000 lines)
3. Re-reads after finding candidates (3000 lines)

**Total: ~13,000 lines read = ~100K tokens**

### With Code-Nav MCP (✅ Low Token Usage)

**User:** "Find where V4L2_CTRL_FLAG_INACTIVE is checked in the ISC driver"

**Claude uses:**
```
smart_grep(pattern="V4L2_CTRL_FLAG_INACTIVE", file_type="c", repo="linux", context=3)
```

**Output:**
```
Found 2 matches:

[linux] drivers/media/platform/microchip/microchip-isc-base.c:1629
  if (ctrl->flags & V4L2_CTRL_FLAG_INACTIVE)
      return 0;

[linux] drivers/media/platform/microchip/microchip-isc-base.c:1712
  if (ctrl->flags & V4L2_CTRL_FLAG_INACTIVE)
      return 0;
```

**Then:**
```
User: "Read lines 1620-1640 of that file to see the context"
Claude: [Uses Read tool with specific range]
```

**Total: ~50 lines read = ~500 tokens**

**Savings: 99.5%** 🎉

---

## Example 2: Understanding Call Chain

### Scenario
You need to understand the flow from histogram interrupt to WB gain update.

### Traditional Approach (❌ High Token Usage)

**User:** "Show me the call chain from histogram interrupt to WB gain hardware update"

**Claude:**
1. Searches for interrupt handlers (reads multiple files)
2. Searches for work queue handlers (more files)
3. Traces function calls manually (re-reads)
4. Searches for register writes (more files)

**Total: ~15,000 lines read = ~120K tokens**

### With Code-Nav MCP (✅ Low Token Usage)

**User:** "Show me the call chain from histogram interrupt to WB gain hardware update"

**Claude uses:**
```
# Step 1: Find the work function
find_symbol(symbol="isc_awb_work", kind="function", repo="linux")
→ microchip-isc-base.c:1503

# Step 2: Find who schedules this work
find_references(symbol="isc_awb_work", repo="linux")
→ isc_stats_isr:1234 (schedules work)

# Step 3: Find what updates hardware
find_symbol(symbol="isc_update_awb_ctrls", kind="function", repo="linux")
→ microchip-isc-base.c:62

# Step 4: Find callers of the update function
find_callers(function="isc_update_awb_ctrls", repo="linux")
→ Called from isc_awb_work:1550
→ Called from isc_s_awb_ctrl:1720
```

**Then read just those 3 functions (150 lines total)**

**Total: ~200 lines read = ~2K tokens**

**Savings: 98.3%** 🎉

---

## Example 3: Git History Investigation

### Scenario
The AWB behavior changed recently. You need to find when and why.

### Traditional Approach (❌ High Token Usage)

**User:** "Show me recent changes to the AWB work function"

**Claude:**
```bash
git log --oneline drivers/media/platform/microchip/microchip-isc-base.c
```
(Returns 500 commits)

```bash
git log -p -- drivers/media/platform/microchip/microchip-isc-base.c
```
(Returns 50,000+ lines of diffs)

Then manually searches through all the diffs for AWB-related changes.

**Total: ~50,000 lines read = ~400K tokens**

### With Code-Nav MCP (✅ Low Token Usage)

**User:** "Show me recent changes to the AWB work function"

**Claude uses:**
```
# Find commits that changed this symbol
git_show_symbol(symbol="isc_awb_work", repo="linux")
```

**Output:**
```
9c99cd701146 media: microchip-isc: use WARN_ON_ONCE for NULL checks in isc_stats_isr
83cb5145e6d7 media: microchip-isc: add IPA teardown holdoff for kernel AWB
7f6297dc1a39 media: microchip-isc: disable CBHS for RGB output
55359b6cc7ae media: microchip-isc: fix histogram channel index
```

**Then:**
```
git_blame_function(function="isc_awb_work", repo="linux")
```

Shows who last modified each line of the function.

**Total: ~100 lines read = ~1K tokens**

**Savings: 99.75%** 🎉

---

## Example 4: Cross-Repository Investigation

### Scenario
IPA is sending WB gains but they're not being applied. Need to check both kernel driver and IPA code.

### Traditional Approach (❌ High Token Usage)

**Claude:**
1. Reads entire kernel control handler (2000 lines)
2. Reads entire IPA main file (1500 lines)
3. Reads IPA AWB algorithm (1000 lines)
4. Re-reads to cross-reference (2000 lines)

**Total: ~6,500 lines = ~50K tokens**

### With Code-Nav MCP (✅ Low Token Usage)

**Claude uses:**
```
# Check kernel side
find_symbol(symbol="isc_s_awb_ctrl", kind="function", repo="linux")
→ microchip-isc-base.c:1706

# Check IPA side
find_symbol(symbol="setIspControls", kind="function", repo="libcamera")
→ microchip_isc_ipa.cpp:234

# Find where IPA sends AWB control
smart_grep(pattern="V4L2_CID_AUTO_WHITE_BALANCE", repo="libcamera")
→ microchip_isc_ipa.cpp:237 (sets AWB=0)

# Find cluster setup in kernel
smart_grep(pattern="v4l2_ctrl_auto_cluster.*awb", repo="linux")
→ microchip-isc-base.c:2119 (cluster with 10 controls)
```

**Then read just those 4 specific function/sections (~200 lines)**

**Total: ~250 lines = ~2K tokens**

**Savings: 96%** 🎉

---

## Example 5: Struct Member Analysis

### Scenario
You need to understand the `mchp_isc_stat_buffer` structure used in kernel-userspace communication.

### Traditional Approach (❌ High Token Usage)

**Claude:**
1. Searches all header files (reads 20+ headers)
2. Finds struct definition
3. Searches for usage (re-reads multiple files)
4. Finds all access patterns (more re-reads)

**Total: ~10,000 lines = ~80K tokens**

### With Code-Nav MCP (✅ Low Token Usage)

**Claude uses:**
```
# Find struct definition
find_symbol(symbol="mchp_isc_stat_buffer", kind="struct", repo="linux")
→ microchip-isc.h:245

# Find all usage
find_references(symbol="mchp_isc_stat_buffer", repo="linux")
→ 8 files found

# Check IPA side
find_references(symbol="mchp_isc_stat_buffer", repo="libcamera")
→ Used in awb.cpp:134
```

**Then read just the struct definition and key usage sites (~100 lines)**

**Total: ~150 lines = ~1.5K tokens**

**Savings: 98%** 🎉

---

## Summary: Token Savings Comparison

| Task | Traditional | With Code-Nav MCP | Savings |
|------|------------|-------------------|---------|
| Find inactive flag check | 100K tokens | 500 tokens | 99.5% |
| Trace call chain | 120K tokens | 2K tokens | 98.3% |
| Git history search | 400K tokens | 1K tokens | 99.75% |
| Cross-repo debugging | 50K tokens | 2K tokens | 96% |
| Struct analysis | 80K tokens | 1.5K tokens | 98% |

**Average savings: 98.3%**

For a typical investigation session with 5-10 such queries:
- **Traditional**: 750K - 1.5M tokens
- **With Code-Nav MCP**: 7.5K - 15K tokens
- **Cost reduction**: ~99%

---

## Best Practices

1. **Always search before reading**
   - Use `find_symbol` or `smart_grep` first
   - Get exact file:line locations
   - Then use Read tool for just that range

2. **Use repo filtering**
   - Narrow searches with `repo="linux"` or `repo="libcamera"`
   - Faster results, less noise

3. **Combine tools strategically**
   ```
   find_symbol → get location
   find_callers → understand usage
   git_blame_function → see history
   Read specific lines → verify details
   ```

4. **Let Claude use the tools**
   - Just ask questions naturally
   - Claude will automatically choose the right MCP tools
   - Trust the structured output

5. **Re-index after big changes**
   - If you checkout a different branch
   - After pulling major updates
   - Just run `add_repo` again (it re-indexes)

---

## Integration with Your Workflow

### Before Code-Nav MCP
```
User: "Debug the AWB gain issue"
Claude: [Reads 15 files, 20,000 lines, 150K tokens]
Claude: "I found the issue..."
```

### After Code-Nav MCP
```
User: "Debug the AWB gain issue"
Claude: [Uses find_symbol, find_callers, smart_grep]
Claude: [Reads 3 specific functions, 200 lines, 2K tokens]
Claude: "I found the issue..."
```

**Same result, 98.7% less tokens used!**

---

## Next Steps

1. **Run the installer**: `./install.sh`
2. **Test locally**: `./test_local.py`
3. **Configure Claude Code**: Add MCP server to settings
4. **Index your repos**: Add linux and libcamera repos
5. **Start investigating**: Use natural language, let Claude use the tools
6. **Track your savings**: Compare token usage in your next session!

Enjoy efficient kernel debugging! 🚀
