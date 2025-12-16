"""
CLI interface for TATty Agent

This module provides command-line entry points for the agent:
- main: Core CLI functionality (interactive, single-shot, TUI modes)
- commands: Initialization and utility commands (tatty-init, tatty-tui)
"""

from .main import cli_main

__all__ = ['cli_main']