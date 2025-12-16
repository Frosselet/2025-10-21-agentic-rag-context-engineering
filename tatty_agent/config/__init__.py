"""
Configuration and initialization for TATty Agent

This package provides:
- settings: Configuration management from env vars, files, and arguments
- initialization: Project setup and external artifact folder management
"""

from .settings import (
    TattyConfig,
    ConfigLoader,
    load_config,
    get_default_config,
    get_global_config,
    set_global_config,
    print_config_info
)

from .initialization import ProjectInitializer

__all__ = [
    'TattyConfig',
    'ConfigLoader',
    'load_config',
    'get_default_config',
    'get_global_config',
    'set_global_config',
    'print_config_info',
    'ProjectInitializer'
]