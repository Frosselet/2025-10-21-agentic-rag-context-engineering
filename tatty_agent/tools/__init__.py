"""
Tool modules for TATty Agent

This package contains all tool implementations organized by category:
- registry: Central tool registration and dispatch system
- file_ops: File operations (read, edit, write, multi_edit)
- system: System tools (bash, glob, grep, ls)
- web: Web tools (web_fetch, web_search)
- utility: Utility tools (todo management, notebook tools, plan mode)
- development: Development tools (pytest, lint, typecheck, format, dependency, git)
- artifacts: Artifact management and package installation

All tool handlers have been successfully extracted from main.py and
modularized during Phase 2.
"""

from .registry import execute_tool, get_registry, register_tool, ToolRegistry

__all__ = [
    'execute_tool',
    'get_registry',
    'register_tool',
    'ToolRegistry'
]