"""
Configuration and settings management for TATty Agent

This module handles configuration loading from various sources:
- Environment variables
- Configuration files (.env, pyproject.toml)
- Programmatic configuration
- CLI arguments
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class TattyConfig:
    """Configuration class for TATty Agent"""

    # API Keys
    openai_api_key: Optional[str] = None
    boundary_api_key: Optional[str] = None

    # Working directory
    working_dir: str = "."

    # Model preferences
    default_model: str = "gpt-4"
    fast_model: str = "gpt-3.5-turbo"

    # Execution settings
    max_iterations: int = 20
    timeout: int = 120

    # UI preferences
    verbose: bool = False
    debug: bool = False
    colorize: bool = True

    # Tool settings
    enable_web_tools: bool = True
    enable_git_tools: bool = True
    enable_package_install: bool = True

    # Safety settings
    require_confirmation: bool = True
    sandbox_mode: bool = False

    # Advanced settings
    custom_tools_dir: Optional[str] = None
    baml_config_path: Optional[str] = None
    log_level: str = "INFO"

    # Internal settings
    _config_sources: list = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.working_dir = str(Path(self.working_dir).resolve())

        # Ensure log level is valid
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            self.log_level = "INFO"

        # Validate model names
        if not self.default_model:
            self.default_model = "gpt-4"
        if not self.fast_model:
            self.fast_model = "gpt-3.5-turbo"


class ConfigLoader:
    """Loads configuration from various sources"""

    def __init__(self):
        self.config = TattyConfig()

    def load_from_env(self, prefix: str = "TATTY_") -> 'ConfigLoader':
        """Load configuration from environment variables"""
        env_mappings = {
            f"{prefix}OPENAI_API_KEY": "openai_api_key",
            f"{prefix}BOUNDARY_API_KEY": "boundary_api_key",
            "OPENAI_API_KEY": "openai_api_key",  # Also check standard names
            "BOUNDARY_API_KEY": "boundary_api_key",
            f"{prefix}WORKING_DIR": "working_dir",
            f"{prefix}DEFAULT_MODEL": "default_model",
            f"{prefix}FAST_MODEL": "fast_model",
            f"{prefix}MAX_ITERATIONS": "max_iterations",
            f"{prefix}TIMEOUT": "timeout",
            f"{prefix}VERBOSE": "verbose",
            f"{prefix}DEBUG": "debug",
            f"{prefix}COLORIZE": "colorize",
            f"{prefix}ENABLE_WEB_TOOLS": "enable_web_tools",
            f"{prefix}ENABLE_GIT_TOOLS": "enable_git_tools",
            f"{prefix}ENABLE_PACKAGE_INSTALL": "enable_package_install",
            f"{prefix}REQUIRE_CONFIRMATION": "require_confirmation",
            f"{prefix}SANDBOX_MODE": "sandbox_mode",
            f"{prefix}CUSTOM_TOOLS_DIR": "custom_tools_dir",
            f"{prefix}BAML_CONFIG_PATH": "baml_config_path",
            f"{prefix}LOG_LEVEL": "log_level",
        }

        for env_var, config_attr in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                config_value = self._convert_env_value(config_attr, value)
                setattr(self.config, config_attr, config_value)
                self.config._config_sources.append(f"env:{env_var}")

        return self

    def load_from_file(self, config_path: Optional[str] = None) -> 'ConfigLoader':
        """Load configuration from .env file"""
        if config_path is None:
            # Try common locations
            possible_paths = [
                Path(".env"),
                Path(".env.local"),
                Path("config/.env"),
                Path(self.config.working_dir) / ".env"
            ]

            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break

        if config_path and Path(config_path).exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(config_path, override=False)
                self.config._config_sources.append(f"file:{config_path}")

                # Re-load from environment after loading .env
                self.load_from_env()
            except ImportError:
                # dotenv not available, try manual parsing
                self._parse_env_file(config_path)

        return self

    def load_from_dict(self, config_dict: Dict[str, Any]) -> 'ConfigLoader':
        """Load configuration from a dictionary"""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.config._config_sources.append(f"dict:{key}")

        return self

    def override_from_args(self, **kwargs) -> 'ConfigLoader':
        """Override configuration with direct arguments"""
        for key, value in kwargs.items():
            if hasattr(self.config, key) and value is not None:
                setattr(self.config, key, value)
                self.config._config_sources.append(f"arg:{key}")

        return self

    def get_config(self) -> TattyConfig:
        """Get the final configuration"""
        return self.config

    def _convert_env_value(self, attr_name: str, value: str) -> Any:
        """Convert string environment values to appropriate types"""
        # Get the type hint from the config class
        config_field_type = TattyConfig.__annotations__.get(attr_name, str)

        # Handle Optional types
        if hasattr(config_field_type, '__origin__'):
            if config_field_type.__origin__ is Union:
                # Get the non-None type from Optional[T]
                non_none_types = [t for t in config_field_type.__args__ if t is not type(None)]
                if non_none_types:
                    config_field_type = non_none_types[0]

        # Convert based on type
        if config_field_type is bool:
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        elif config_field_type is int:
            try:
                return int(value)
            except ValueError:
                return getattr(self.config, attr_name)  # Keep current value
        elif config_field_type is float:
            try:
                return float(value)
            except ValueError:
                return getattr(self.config, attr_name)  # Keep current value
        else:
            return value

    def _parse_env_file(self, file_path: str) -> None:
        """Manually parse .env file when dotenv is not available"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Set in environment
                        os.environ[key] = value

            self.config._config_sources.append(f"manual_file:{file_path}")
        except Exception as e:
            # Silently fail if we can't parse the file
            pass


def load_config(
    config_path: Optional[str] = None,
    working_dir: Optional[str] = None,
    **overrides
) -> TattyConfig:
    """
    Load configuration from all available sources

    Args:
        config_path: Path to .env file
        working_dir: Override working directory
        **overrides: Direct configuration overrides

    Returns:
        Configured TattyConfig instance
    """
    loader = ConfigLoader()

    # Load from environment first
    loader.load_from_env()

    # Load from file (if available)
    loader.load_from_file(config_path)

    # Apply direct overrides
    if working_dir:
        overrides['working_dir'] = working_dir

    if overrides:
        loader.override_from_args(**overrides)

    return loader.get_config()


def get_default_config() -> TattyConfig:
    """Get a default configuration (useful for testing)"""
    return TattyConfig()


def print_config_info(config: TattyConfig) -> None:
    """Print configuration information for debugging"""
    print("📋 TATty Agent Configuration:")
    print(f"  Working Directory: {config.working_dir}")
    print(f"  Default Model: {config.default_model}")
    print(f"  Fast Model: {config.fast_model}")
    print(f"  Max Iterations: {config.max_iterations}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Verbose: {config.verbose}")
    print(f"  Debug: {config.debug}")

    # Check API keys (show only last 4 characters for security)
    openai_key = config.openai_api_key
    boundary_key = config.boundary_api_key

    print(f"  OpenAI Key: {'***' + openai_key[-4:] if openai_key else 'Not set'}")
    print(f"  Boundary Key: {'***' + boundary_key[-4:] if boundary_key else 'Not set'}")

    if config.debug and config._config_sources:
        print(f"  Config Sources: {', '.join(config._config_sources)}")


# Global config instance (can be overridden)
_global_config: Optional[TattyConfig] = None


def get_global_config() -> TattyConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def set_global_config(config: TattyConfig) -> None:
    """Set the global configuration instance"""
    global _global_config
    _global_config = config