"""
Tests for configuration and initialization systems
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from tatty_agent.config.settings import TattyConfig, ConfigLoader, load_config
from tatty_agent.config.initialization import ProjectInitializer


class TestTattyConfig:
    """Test suite for TattyConfig"""

    def test_config_initialization(self):
        """Test config initialization with defaults"""
        config = TattyConfig()

        assert config.working_dir == str(Path(".").resolve())
        assert config.default_model == "gpt-4"
        assert config.fast_model == "gpt-3.5-turbo"
        assert config.max_iterations == 20
        assert config.timeout == 120
        assert config.verbose is False
        assert config.debug is False

    def test_config_custom_values(self):
        """Test config with custom values"""
        config = TattyConfig(
            working_dir="/custom/dir",
            default_model="custom-model",
            verbose=True,
            debug=True
        )

        assert config.working_dir == "/custom/dir"
        assert config.default_model == "custom-model"
        assert config.verbose is True
        assert config.debug is True

    def test_config_validation(self):
        """Test config validation in post_init"""
        config = TattyConfig(
            log_level="INVALID",
            default_model="",
            fast_model=""
        )

        # Should be corrected by validation
        assert config.log_level == "INFO"
        assert config.default_model == "gpt-4"
        assert config.fast_model == "gpt-3.5-turbo"


class TestConfigLoader:
    """Test suite for ConfigLoader"""

    def test_loader_initialization(self):
        """Test config loader initialization"""
        loader = ConfigLoader()
        assert isinstance(loader.config, TattyConfig)

    def test_load_from_env(self):
        """Test loading from environment variables"""
        with patch.dict(os.environ, {
            'TATTY_WORKING_DIR': '/env/dir',
            'TATTY_VERBOSE': 'true',
            'TATTY_DEBUG': 'false',
            'TATTY_MAX_ITERATIONS': '30',
            'OPENAI_API_KEY': 'test-key'
        }):
            loader = ConfigLoader()
            loader.load_from_env()

            assert loader.config.working_dir == '/env/dir'
            assert loader.config.verbose is True
            assert loader.config.debug is False
            assert loader.config.max_iterations == 30
            assert loader.config.openai_api_key == 'test-key'

    def test_load_from_dict(self):
        """Test loading from dictionary"""
        loader = ConfigLoader()
        config_dict = {
            'working_dir': '/dict/dir',
            'verbose': True,
            'max_iterations': 25
        }

        loader.load_from_dict(config_dict)

        assert loader.config.working_dir == '/dict/dir'
        assert loader.config.verbose is True
        assert loader.config.max_iterations == 25

    def test_override_from_args(self):
        """Test overriding with direct arguments"""
        loader = ConfigLoader()
        loader.override_from_args(
            working_dir='/args/dir',
            verbose=True,
            max_iterations=35
        )

        assert loader.config.working_dir == '/args/dir'
        assert loader.config.verbose is True
        assert loader.config.max_iterations == 35

    def test_convert_env_value_bool(self):
        """Test environment value conversion for booleans"""
        loader = ConfigLoader()

        assert loader._convert_env_value('verbose', 'true') is True
        assert loader._convert_env_value('verbose', 'false') is False
        assert loader._convert_env_value('verbose', '1') is True
        assert loader._convert_env_value('verbose', '0') is False
        assert loader._convert_env_value('verbose', 'yes') is True
        assert loader._convert_env_value('verbose', 'no') is False

    def test_convert_env_value_int(self):
        """Test environment value conversion for integers"""
        loader = ConfigLoader()

        assert loader._convert_env_value('max_iterations', '42') == 42
        assert loader._convert_env_value('max_iterations', 'invalid') == 20  # Default


class TestProjectInitializer:
    """Test suite for ProjectInitializer"""

    def test_initializer_creation(self):
        """Test project initializer creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)
            assert str(initializer.project_root) == str(Path(temp_dir).resolve())

    def test_check_project_status_empty(self):
        """Test project status check on empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)
            status = initializer.check_project_status()

            assert status["initialized"] is False
            assert len(status["missing"]) > 0

    def test_initialize_project_creates_folders(self):
        """Test that project initialization creates standard folders"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)
            results = initializer.initialize_project()

            assert results["success"] is True
            assert len(results["created_folders"]) > 0

            # Check that folders were actually created
            for folder in ["scripts", "data", "visualization", "documents"]:
                folder_path = Path(temp_dir) / folder
                assert folder_path.exists()
                assert folder_path.is_dir()

    def test_initialize_project_creates_env_file(self):
        """Test that project initialization creates .env file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)
            results = initializer.initialize_project()

            env_file = Path(temp_dir) / ".env"
            assert env_file.exists()
            assert ".env" in results["created_files"]

            # Check content
            content = env_file.read_text()
            assert "OPENAI_API_KEY" in content
            assert "BOUNDARY_API_KEY" in content

    def test_initialize_project_force_overwrite(self):
        """Test force overwrite functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing .env file
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("existing content")

            initializer = ProjectInitializer(temp_dir)

            # First run without force
            results1 = initializer.initialize_project(force=False)
            assert ".env" in results1["existing_files"]

            # Second run with force
            results2 = initializer.initialize_project(force=True)
            assert ".env" in results2["created_files"]

            # Check content was overwritten
            content = env_file.read_text()
            assert "OPENAI_API_KEY" in content

    def test_clean_project(self):
        """Test project cleanup functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)

            # Initialize project first
            initializer.initialize_project()

            # Clean without confirmation (should fail)
            results1 = initializer.clean_project(confirm=False)
            assert results1["success"] is False

            # Clean with confirmation
            results2 = initializer.clean_project(confirm=True)
            assert results2["success"] is True


class TestConfigIntegration:
    """Integration tests for configuration system"""

    def test_load_config_integration(self):
        """Test the main load_config function"""
        config = load_config()
        assert isinstance(config, TattyConfig)

    def test_load_config_with_overrides(self):
        """Test load_config with parameter overrides"""
        config = load_config(
            working_dir="/test/dir",
            verbose=True
        )

        assert config.working_dir == "/test/dir"
        assert config.verbose is True