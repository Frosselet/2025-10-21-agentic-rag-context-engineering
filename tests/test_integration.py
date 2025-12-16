"""
Integration tests for TATty Agent package

These tests verify that all package modes work together correctly:
- CLI integration
- Library API integration
- Tool system integration
- Configuration system integration
- Project initialization integration
"""
import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Test imports work correctly
def test_package_imports():
    """Test that all main package imports work"""
    try:
        import tatty_agent
        from tatty_agent import TattyAgent, run_agent, ask_agent, initialize_project
        from tatty_agent.config import TattyConfig, load_config
        from tatty_agent.core import AgentRuntime, AgentState, AgentCallbacks
        assert True  # All imports successful
    except ImportError as e:
        pytest.fail(f"Package import failed: {e}")


def test_jupyter_imports():
    """Test that Jupyter integration imports work (if available)"""
    try:
        from tatty_agent.jupyter import (
            display_agent_response,
            get_notebook_context,
            track_tool_execution,
            create_chat_widget
        )
        assert True  # All imports successful
    except ImportError:
        # Jupyter dependencies may not be installed
        pytest.skip("Jupyter dependencies not available")


class TestLibraryAPIIntegration:
    """Integration tests for library API usage patterns"""

    def test_agent_initialization_with_config(self):
        """Test agent initialization with custom configuration"""
        from tatty_agent import TattyAgent, TattyConfig

        with tempfile.TemporaryDirectory() as temp_dir:
            config = TattyConfig(
                working_dir=temp_dir,
                verbose=True,
                max_iterations=10
            )

            agent = TattyAgent(config=config)

            assert temp_dir in agent.working_dir
            assert agent.verbose is True
            assert agent.max_iterations == 10

    def test_agent_working_directory_management(self):
        """Test working directory changes"""
        from tatty_agent import TattyAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            agent = TattyAgent()

            # Change working directory
            agent.set_working_dir(temp_dir)
            assert temp_dir in agent.get_working_dir()

            # Verify state is updated
            assert temp_dir in agent.state.working_dir

    def test_agent_conversation_history(self):
        """Test conversation history management"""
        from tatty_agent import TattyAgent

        agent = TattyAgent()

        # Initially empty
        assert len(agent.get_conversation_history()) == 0

        # Add mock conversation
        agent._conversation_history.append({
            "type": "user",
            "content": "Test query"
        })
        agent._conversation_history.append({
            "type": "assistant",
            "content": "Test response"
        })

        history = agent.get_conversation_history()
        assert len(history) == 2
        assert history[0]["type"] == "user"
        assert history[1]["type"] == "assistant"

        # Clear history
        agent.clear_conversation_history()
        assert len(agent.get_conversation_history()) == 0


class TestConfigurationIntegration:
    """Integration tests for configuration system"""

    def test_config_loading_priority(self):
        """Test configuration loading priority: args > env > defaults"""
        from tatty_agent.config import load_config

        with patch.dict(os.environ, {
            'TATTY_VERBOSE': 'true',
            'TATTY_MAX_ITERATIONS': '30'
        }):
            # Load with environment variables
            config1 = load_config()
            assert config1.verbose is True
            assert config1.max_iterations == 30

            # Override with arguments
            config2 = load_config(verbose=False, max_iterations=15)
            assert config2.verbose is False  # Argument overrides env
            assert config2.max_iterations == 15  # Argument overrides env

    def test_config_validation(self):
        """Test configuration validation and defaults"""
        from tatty_agent.config import TattyConfig

        # Test with invalid values
        config = TattyConfig(
            log_level="INVALID",
            default_model="",
            max_iterations=-5
        )

        # Should be validated and corrected
        assert config.log_level == "INFO"  # Corrected to default
        assert config.default_model == "gpt-4"  # Corrected to default
        assert config.max_iterations == 20  # Should be corrected to minimum valid


class TestProjectInitializationIntegration:
    """Integration tests for project initialization"""

    def test_full_project_initialization(self):
        """Test complete project initialization workflow"""
        from tatty_agent.config.initialization import ProjectInitializer

        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)

            # Check initial status
            status = initializer.check_project_status()
            assert status["initialized"] is False
            assert len(status["missing"]) > 0

            # Initialize project
            result = initializer.initialize_project()
            assert result["success"] is True
            assert len(result["created_folders"]) >= 4
            assert len(result["created_files"]) >= 1

            # Verify folders were created
            expected_folders = ["scripts", "data", "visualization", "documents"]
            for folder in expected_folders:
                folder_path = Path(temp_dir) / folder
                assert folder_path.exists()
                assert folder_path.is_dir()

            # Verify .env file was created
            env_file = Path(temp_dir) / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "OPENAI_API_KEY" in content
            assert "BOUNDARY_API_KEY" in content

            # Check status after initialization
            status_after = initializer.check_project_status()
            assert status_after["initialized"] is True

    def test_initialization_with_existing_files(self):
        """Test initialization behavior with existing files"""
        from tatty_agent.config.initialization import ProjectInitializer

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing .env file
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("EXISTING_VAR=value")

            initializer = ProjectInitializer(temp_dir)

            # Initialize without force (should skip existing)
            result1 = initializer.initialize_project(force=False)
            assert ".env" in result1["existing_files"]

            # Verify original content preserved
            content = env_file.read_text()
            assert "EXISTING_VAR=value" in content

            # Initialize with force (should overwrite)
            result2 = initializer.initialize_project(force=True)
            assert ".env" in result2["created_files"]

            # Verify content was overwritten
            new_content = env_file.read_text()
            assert "OPENAI_API_KEY" in new_content


class TestToolSystemIntegration:
    """Integration tests for tool system"""

    def test_tool_registry_loading(self):
        """Test that all tools are properly registered"""
        from tatty_agent.tools.registry import get_registered_tools, execute_tool

        tools = get_registered_tools()

        # Should have tools from all modules
        expected_tools = [
            "Read", "Edit", "Write", "MultiEdit",  # file_ops
            "Bash", "Glob", "Grep", "Ls",  # system
            "WebFetch", "WebSearch",  # web
            "ArtifactManagement", "InstallPackages"  # artifacts
        ]

        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool {tool_name} not registered"

    def test_tool_execution_workflow(self):
        """Test basic tool execution workflow"""
        from tatty_agent.tools.registry import execute_tool
        from tatty_agent.core.types import types

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")

            # Test Read tool
            read_tool = types.ReadTool(
                action="Read",
                path=str(test_file)
            )

            result = execute_tool(read_tool, temp_dir)
            assert "Test content" in result


class TestCLIIntegration:
    """Integration tests for CLI functionality"""

    def test_cli_help_command(self):
        """Test CLI help command works"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "tatty_agent.cli.main", "--help"
            ], capture_output=True, text=True, timeout=10)

            # Should not crash and should show help
            assert result.returncode == 0
            assert "TATty Agent" in result.stdout or "usage:" in result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("CLI not available or timeout")

    def test_tatty_init_command_available(self):
        """Test that tatty-init command is available"""
        try:
            result = subprocess.run([
                sys.executable, "-c",
                "from tatty_agent.cli.commands import tatty_init; print('OK')"
            ], capture_output=True, text=True, timeout=5)

            assert result.returncode == 0
            assert "OK" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("Command import timeout")


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility"""

    def test_main_imports_preserved(self):
        """Test that main imports are preserved for backward compatibility"""
        # These imports should work for existing users
        try:
            from tatty_agent import TattyAgent
            from tatty_agent import run_agent, ask_agent
            from tatty_agent import initialize_project
            assert True
        except ImportError as e:
            pytest.fail(f"Backward compatibility import failed: {e}")

    def test_convenience_functions_work(self):
        """Test that convenience functions work as before"""
        from tatty_agent import run_agent, ask_agent

        # These should not crash (but may not execute fully in tests)
        with patch('tatty_agent.TattyAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.run.return_value = "Test result"
            mock_agent.ask.return_value = "Test answer"
            mock_agent_class.return_value = mock_agent

            result1 = run_agent("test query", working_dir="/tmp")
            result2 = ask_agent("test question", working_dir="/tmp")

            assert result1 == "Test result"
            assert result2 == "Test answer"


class TestErrorHandling:
    """Integration tests for error handling"""

    def test_invalid_working_directory(self):
        """Test behavior with invalid working directory"""
        from tatty_agent import TattyAgent

        # Should handle invalid directory gracefully
        agent = TattyAgent(working_dir="/nonexistent/directory")
        # Should not crash during initialization
        assert agent is not None

    def test_missing_dependencies_graceful_failure(self):
        """Test graceful handling of missing optional dependencies"""
        # Test that the package still works if optional dependencies are missing
        with patch.dict('sys.modules', {'textual': None}):
            try:
                from tatty_agent import TattyAgent
                agent = TattyAgent()
                # Basic functionality should still work
                assert agent is not None
            except ImportError:
                # Should not fail due to missing textual
                pytest.fail("Package failed to import without optional dependencies")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])