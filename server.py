#!/usr/bin/env python3
"""
Generic Code Navigation MCP Server

Provides efficient code navigation without reading full files:
- Symbol lookup (ctags-based)
- Cross-references (ripgrep-based)
- Git integration (blame, show)
- Multi-repo support

Usage:
    python server.py
"""

import asyncio
import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    exit(1)


@dataclass
class SymbolResult:
    """Result of a symbol lookup"""
    symbol: str
    file: str
    line: int
    kind: str  # function, struct, define, variable, etc.
    pattern: str  # the actual code line
    repo: str


@dataclass
class ReferenceResult:
    """Result of a reference search"""
    file: str
    line: int
    content: str
    repo: str


class CodeRepo:
    """Represents an indexed code repository"""

    def __init__(self, name: str, path: str, branch: Optional[str] = None):
        self.name = name
        self.path = Path(path).resolve()
        self.branch = branch
        self.tags_file = self.path / ".tags"

        if not self.path.exists():
            raise ValueError(f"Repository path does not exist: {path}")

    def index(self) -> str:
        """Generate ctags index for the repository"""
        try:
            # Universal ctags with extra fields
            cmd = [
                "ctags",
                "-R",
                "--fields=+nkzS",  # line number, kind, scope, signature
                "--extras=+q",      # qualified tags
                "--output-format=json",
                f"-f{self.tags_file}",
                str(self.path)
            ]

            result = subprocess.run(cmd, cwd=self.path, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                return f"Warning: ctags indexing had issues: {result.stderr}"

            return f"Indexed {self.name} at {self.path} (branch: {self.branch or 'current'})"

        except subprocess.TimeoutExpired:
            return f"Error: Indexing timed out for {self.name}"
        except FileNotFoundError:
            return "Error: ctags not found. Install with: sudo apt install universal-ctags"
        except Exception as e:
            return f"Error indexing {self.name}: {str(e)}"

    def find_symbol(self, symbol: str, kind: Optional[str] = None) -> List[SymbolResult]:
        """Find symbol definitions using tags file"""
        if not self.tags_file.exists():
            return []

        results = []
        try:
            with open(self.tags_file, 'r') as f:
                for line in f:
                    if line.startswith('!'):  # Skip tag file headers
                        continue

                    try:
                        tag = json.loads(line.strip())

                        # Match symbol name
                        if tag.get('name') != symbol:
                            continue

                        # Filter by kind if specified
                        tag_kind = tag.get('kind', '')
                        if kind and tag_kind != kind:
                            continue

                        results.append(SymbolResult(
                            symbol=tag['name'],
                            file=tag['path'],
                            line=tag.get('line', 0),
                            kind=tag_kind,
                            pattern=tag.get('pattern', '').strip('/^$/'),
                            repo=self.name
                        ))

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error reading tags: {e}")

        return results

    def find_references(self, symbol: str, context: int = 2) -> List[ReferenceResult]:
        """Find all references to a symbol using ripgrep"""
        try:
            cmd = [
                "rg",
                "--json",
                "-w",  # word boundary
                f"-C{context}",
                symbol
            ]

            result = subprocess.run(
                cmd,
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=30
            )

            references = []
            for line in result.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if data['type'] == 'match':
                        match_data = data['data']
                        references.append(ReferenceResult(
                            file=match_data['path']['text'],
                            line=match_data['line_number'],
                            content=match_data['lines']['text'].strip(),
                            repo=self.name
                        ))
                except (json.JSONDecodeError, KeyError):
                    continue

            return references

        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error finding references: {e}")
            return []

    def git_blame_function(self, file: str, function: str) -> Optional[str]:
        """Get git blame for a specific function"""
        try:
            # First, find the function definition line range
            symbols = self.find_symbol(function, kind='function')
            if not symbols:
                return f"Function {function} not found in {self.name}"

            # Find the symbol in this file
            symbol = next((s for s in symbols if file in s.file), None)
            if not symbol:
                return f"Function {function} not found in file {file}"

            # Use git blame with line range
            # Estimate function length (rough: 20 lines)
            start_line = symbol.line
            end_line = start_line + 20

            cmd = [
                "git", "blame",
                f"-L{start_line},{end_line}",
                "--",
                symbol.file
            ]

            result = subprocess.run(
                cmd,
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Git blame failed: {result.stderr}"

        except Exception as e:
            return f"Error in git blame: {str(e)}"

    def git_show_symbol(self, symbol: str) -> Optional[str]:
        """Show recent commits affecting a symbol"""
        try:
            cmd = [
                "git", "log",
                "-S", symbol,  # Pickaxe search
                "--oneline",
                "--max-count=10"
            ]

            result = subprocess.run(
                cmd,
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout if result.stdout else "No commits found"
            else:
                return f"Git log failed: {result.stderr}"

        except Exception as e:
            return f"Error in git log: {str(e)}"


class CodeNavServer:
    """MCP Server for code navigation"""

    def __init__(self):
        self.repos: Dict[str, CodeRepo] = {}
        self.server = Server("code-nav-mcp")
        self.setup_handlers()

    def setup_handlers(self):
        """Register MCP tool handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="add_repo",
                    description="Add and index a code repository for navigation. Supports any git repo (linux kernel, libcamera, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Short name for the repo (e.g., 'linux', 'libcamera')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Optional: Git branch name for reference"
                            }
                        },
                        "required": ["name", "path"]
                    }
                ),
                Tool(
                    name="list_repos",
                    description="List all indexed repositories",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="find_symbol",
                    description="Find where a symbol (function, struct, define, variable) is defined. Returns file:line without reading full files.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name to find (e.g., 'isc_awb_work', 'v4l2_ctrl_auto_cluster')"
                            },
                            "kind": {
                                "type": "string",
                                "description": "Optional: Filter by symbol kind (function, struct, macro, variable, typedef)",
                                "enum": ["function", "struct", "macro", "variable", "typedef", "member"]
                            },
                            "repo": {
                                "type": "string",
                                "description": "Optional: Search only in specific repo (otherwise searches all)"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="find_references",
                    description="Find all places where a symbol is referenced/used. Returns file:line:content without full file reads.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol to find references for"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Optional: Search only in specific repo"
                            },
                            "context": {
                                "type": "integer",
                                "description": "Lines of context around each match (default: 2)",
                                "default": 2
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="find_callers",
                    description="Find all functions that call a given function. Useful for understanding call chains.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function": {
                                "type": "string",
                                "description": "Function name to find callers for"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Optional: Search only in specific repo"
                            }
                        },
                        "required": ["function"]
                    }
                ),
                Tool(
                    name="git_blame_function",
                    description="Get git blame for a specific function - who last changed it and when",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function": {
                                "type": "string",
                                "description": "Function name"
                            },
                            "file": {
                                "type": "string",
                                "description": "Optional: Specific file if function exists in multiple files"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Repository name"
                            }
                        },
                        "required": ["function", "repo"]
                    }
                ),
                Tool(
                    name="git_show_symbol",
                    description="Show recent commits that modified a symbol (function, variable, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Repository name"
                            }
                        },
                        "required": ["symbol", "repo"]
                    }
                ),
                Tool(
                    name="smart_grep",
                    description="Grep across repositories with structured output (file:line:content). More efficient than reading full files.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Regex pattern to search for"
                            },
                            "file_type": {
                                "type": "string",
                                "description": "Optional: File type filter (c, cpp, h, py, etc.)"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Optional: Search only in specific repo"
                            },
                            "context": {
                                "type": "integer",
                                "description": "Lines of context (default: 2)",
                                "default": 2
                            }
                        },
                        "required": ["pattern"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            try:
                if name == "add_repo":
                    return await self.handle_add_repo(arguments)
                elif name == "list_repos":
                    return await self.handle_list_repos(arguments)
                elif name == "find_symbol":
                    return await self.handle_find_symbol(arguments)
                elif name == "find_references":
                    return await self.handle_find_references(arguments)
                elif name == "find_callers":
                    return await self.handle_find_callers(arguments)
                elif name == "git_blame_function":
                    return await self.handle_git_blame_function(arguments)
                elif name == "git_show_symbol":
                    return await self.handle_git_show_symbol(arguments)
                elif name == "smart_grep":
                    return await self.handle_smart_grep(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def handle_add_repo(self, args: Dict) -> List[TextContent]:
        """Add and index a repository"""
        name = args["name"]
        path = args["path"]
        branch = args.get("branch")

        try:
            repo = CodeRepo(name, path, branch)
            result = repo.index()
            self.repos[name] = repo

            return [TextContent(
                type="text",
                text=f"✓ {result}\nRepository '{name}' is now indexed and ready for navigation."
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"Failed to add repo: {str(e)}")]

    async def handle_list_repos(self, args: Dict) -> List[TextContent]:
        """List all indexed repositories"""
        if not self.repos:
            return [TextContent(type="text", text="No repositories indexed yet. Use add_repo first.")]

        output = "Indexed Repositories:\n\n"
        for name, repo in self.repos.items():
            output += f"• {name}\n"
            output += f"  Path: {repo.path}\n"
            output += f"  Branch: {repo.branch or 'current'}\n"
            output += f"  Tags: {'✓ indexed' if repo.tags_file.exists() else '✗ not indexed'}\n\n"

        return [TextContent(type="text", text=output)]

    async def handle_find_symbol(self, args: Dict) -> List[TextContent]:
        """Find symbol definitions"""
        symbol = args["symbol"]
        kind = args.get("kind")
        repo_name = args.get("repo")

        # Search in specified repo or all repos
        repos_to_search = [self.repos[repo_name]] if repo_name else self.repos.values()

        all_results = []
        for repo in repos_to_search:
            results = repo.find_symbol(symbol, kind)
            all_results.extend(results)

        if not all_results:
            return [TextContent(
                type="text",
                text=f"Symbol '{symbol}' not found{f' (kind: {kind})' if kind else ''}"
            )]

        # Format results
        output = f"Found {len(all_results)} definition(s) for '{symbol}':\n\n"
        for r in all_results:
            output += f"[{r.repo}] {r.file}:{r.line}\n"
            output += f"  Kind: {r.kind}\n"
            output += f"  Code: {r.pattern}\n\n"

        return [TextContent(type="text", text=output)]

    async def handle_find_references(self, args: Dict) -> List[TextContent]:
        """Find symbol references"""
        symbol = args["symbol"]
        repo_name = args.get("repo")
        context = args.get("context", 2)

        repos_to_search = [self.repos[repo_name]] if repo_name else self.repos.values()

        all_results = []
        for repo in repos_to_search:
            results = repo.find_references(symbol, context)
            all_results.extend(results)

        if not all_results:
            return [TextContent(type="text", text=f"No references found for '{symbol}'")]

        # Limit output to first 50 results
        limited_results = all_results[:50]
        output = f"Found {len(all_results)} reference(s) to '{symbol}'"
        if len(all_results) > 50:
            output += f" (showing first 50)"
        output += ":\n\n"

        for r in limited_results:
            output += f"[{r.repo}] {r.file}:{r.line}\n"
            output += f"  {r.content}\n\n"

        return [TextContent(type="text", text=output)]

    async def handle_find_callers(self, args: Dict) -> List[TextContent]:
        """Find functions that call the given function"""
        function = args["function"]
        repo_name = args.get("repo")

        # Find all call sites
        repos_to_search = [self.repos[repo_name]] if repo_name else self.repos.values()

        call_sites = []
        for repo in repos_to_search:
            # Look for function calls: function_name(
            pattern = f"{function}\\s*\\("
            refs = repo.find_references(pattern, context=0)
            call_sites.extend(refs)

        if not call_sites:
            return [TextContent(type="text", text=f"No callers found for '{function}'")]

        output = f"Found {len(call_sites)} call site(s) for '{function}':\n\n"
        for site in call_sites[:50]:  # Limit to 50
            output += f"[{site.repo}] {site.file}:{site.line}\n"
            output += f"  {site.content}\n\n"

        return [TextContent(type="text", text=output)]

    async def handle_git_blame_function(self, args: Dict) -> List[TextContent]:
        """Git blame for a function"""
        function = args["function"]
        file = args.get("file", "")
        repo_name = args["repo"]

        if repo_name not in self.repos:
            return [TextContent(type="text", text=f"Repository '{repo_name}' not found")]

        repo = self.repos[repo_name]
        result = repo.git_blame_function(file, function)

        return [TextContent(type="text", text=result or "No blame info available")]

    async def handle_git_show_symbol(self, args: Dict) -> List[TextContent]:
        """Show git history for a symbol"""
        symbol = args["symbol"]
        repo_name = args["repo"]

        if repo_name not in self.repos:
            return [TextContent(type="text", text=f"Repository '{repo_name}' not found")]

        repo = self.repos[repo_name]
        result = repo.git_show_symbol(symbol)

        return [TextContent(type="text", text=result or "No commits found")]

    async def handle_smart_grep(self, args: Dict) -> List[TextContent]:
        """Smart grep with structured output"""
        pattern = args["pattern"]
        file_type = args.get("file_type")
        repo_name = args.get("repo")
        context = args.get("context", 2)

        repos_to_search = [self.repos[repo_name]] if repo_name else self.repos.values()

        all_matches = []
        for repo in repos_to_search:
            try:
                cmd = ["rg", "--json", f"-C{context}"]
                if file_type:
                    cmd.extend(["-t", file_type])
                cmd.append(pattern)

                result = subprocess.run(
                    cmd,
                    cwd=repo.path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                for line in result.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        if data['type'] == 'match':
                            match_data = data['data']
                            all_matches.append({
                                'repo': repo.name,
                                'file': match_data['path']['text'],
                                'line': match_data['line_number'],
                                'content': match_data['lines']['text'].strip()
                            })
                    except (json.JSONDecodeError, KeyError):
                        continue

            except Exception as e:
                continue

        if not all_matches:
            return [TextContent(type="text", text=f"No matches found for pattern: {pattern}")]

        limited_matches = all_matches[:100]
        output = f"Found {len(all_matches)} match(es) for '{pattern}'"
        if len(all_matches) > 100:
            output += " (showing first 100)"
        output += ":\n\n"

        for match in limited_matches:
            output += f"[{match['repo']}] {match['file']}:{match['line']}\n"
            output += f"  {match['content']}\n\n"

        return [TextContent(type="text", text=output)]

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    server = CodeNavServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
