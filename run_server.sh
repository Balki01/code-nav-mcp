#!/bin/bash
# Wrapper script to run the MCP server with local library path

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/lib:${PYTHONPATH}"
export TMPDIR=/tmp/claude-1000

exec python3 "${SCRIPT_DIR}/server.py" "$@"
