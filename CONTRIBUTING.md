# Contributing to Code Navigation MCP Server

Thank you for your interest in contributing! This project helps developers navigate large codebases efficiently.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/code-nav-mcp.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test locally: `./test_setup.py && ./test_functional.py`
6. Commit: `git commit -m "Add: your feature description"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install mcp

# Install system tools
sudo apt install universal-ctags ripgrep

# Test the server
python3 test_setup.py
```

## Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings for public functions
- Keep functions focused and small

## Testing

Before submitting a PR:

1. Run `test_setup.py` to verify dependencies
2. Run `test_functional.py` to test indexing
3. Test with at least one real repository

## Reporting Bugs

Open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, ctags version)

## Feature Requests

We welcome feature ideas! Open an issue describing:
- The use case
- Why it would be useful
- How it might work

## Questions?

Open an issue with the `question` label.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and build better tools.
