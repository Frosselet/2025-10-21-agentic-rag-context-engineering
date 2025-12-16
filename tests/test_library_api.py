"""
Tests for the main library API
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from tatty_agent import TattyAgent, run_agent, ask_agent, initialize_project


class TestTattyAgent:
    """Test suite for the main TattyAgent class"""

    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = TattyAgent(working_dir="/test/dir", verbose=True)

        assert "/test/dir" in agent.working_dir
        assert agent.verbose is True
        assert agent.max_iterations == 20
        assert isinstance(agent._conversation_history, list)

    def test_agent_initialization_defaults(self):
        """Test agent initialization with defaults"""
        agent = TattyAgent()

        assert agent.working_dir is not None
        assert agent.verbose is False
        assert agent.max_iterations == 20

    @patch('tatty_agent.AgentRuntime')
    @patch('asyncio.run')
    def test_agent_run(self, mock_asyncio_run, mock_runtime_class):
        """Test agent.run() method"""
        # Setup mocks
        mock_runtime = Mock()
        mock_runtime_class.return_value = mock_runtime
        mock_asyncio_run.return_value = "Test result"

        agent = TattyAgent()
        result = agent.run("Test query")

        assert result == "Test result"
        mock_asyncio_run.assert_called_once()
        assert len(agent._conversation_history) == 2  # Query + result

    @patch('tatty_agent.AgentRuntime')
    @patch('asyncio.run')
    def test_agent_ask(self, mock_asyncio_run, mock_runtime_class):
        """Test agent.ask() method (alias for run)"""
        mock_asyncio_run.return_value = "Test answer"

        agent = TattyAgent()
        result = agent.ask("Test question")

        assert result == "Test answer"

    def test_agent_execute_tool(self):
        """Test agent.execute_tool() method"""
        agent = TattyAgent()

        # This is a placeholder implementation, so just test it doesn't crash
        result = agent.execute_tool("TestTool", param1="value1")

        assert "TestTool" in result
        assert "param1" in result

    def test_get_conversation_history(self):
        """Test conversation history management"""
        agent = TattyAgent()

        # Initially empty
        history = agent.get_conversation_history()
        assert history == []

        # Add some history
        agent._conversation_history.append({"type": "test", "content": "test"})
        history = agent.get_conversation_history()
        assert len(history) == 1
        assert history[0]["type"] == "test"

    def test_clear_conversation_history(self):
        """Test clearing conversation history"""
        agent = TattyAgent()

        # Add some history
        agent._conversation_history.append({"type": "test", "content": "test"})
        assert len(agent._conversation_history) == 1

        # Clear history
        agent.clear_conversation_history()
        assert len(agent._conversation_history) == 0

    def test_working_directory_management(self):
        """Test working directory getter/setter"""
        agent = TattyAgent(working_dir="/initial/dir")

        assert "/initial/dir" in agent.get_working_dir()

        agent.set_working_dir("/new/dir")
        assert "/new/dir" in agent.get_working_dir()
        assert "/new/dir" in agent.state.working_dir

    @patch('tatty_agent.ProjectInitializer')
    def test_is_project_initialized(self, mock_initializer_class):
        """Test project initialization check"""
        mock_initializer = Mock()
        mock_initializer_class.return_value = mock_initializer
        mock_initializer.check_project_status.return_value = {"initialized": True}

        agent = TattyAgent()
        result = agent.is_project_initialized()

        assert result is True
        mock_initializer.check_project_status.assert_called_once()

    @patch('tatty_agent.ProjectInitializer')
    def test_initialize_project(self, mock_initializer_class):
        """Test project initialization through agent"""
        mock_initializer = Mock()
        mock_initializer_class.return_value = mock_initializer
        mock_initializer.initialize_project.return_value = {"success": True}

        agent = TattyAgent()
        result = agent.initialize_project(force=True)

        assert result["success"] is True
        mock_initializer.initialize_project.assert_called_once_with(force=True)

    def test_agent_repr(self):
        """Test agent string representation"""
        agent = TattyAgent(working_dir="/test/dir")
        repr_str = repr(agent)

        assert "TattyAgent" in repr_str
        assert "/test/dir" in repr_str


class TestConvenienceFunctions:
    """Test suite for convenience functions"""

    @patch('tatty_agent.TattyAgent')
    def test_run_agent(self, mock_agent_class):
        """Test run_agent convenience function"""
        mock_agent = Mock()
        mock_agent.run.return_value = "Test result"
        mock_agent_class.return_value = mock_agent

        result = run_agent("Test query", working_dir="/test/dir", verbose=True)

        assert result == "Test result"
        mock_agent_class.assert_called_once_with(working_dir="/test/dir", verbose=True)
        mock_agent.run.assert_called_once_with("Test query")

    @patch('tatty_agent.TattyAgent')
    def test_ask_agent(self, mock_agent_class):
        """Test ask_agent convenience function"""
        mock_agent = Mock()
        mock_agent.ask.return_value = "Test answer"
        mock_agent_class.return_value = mock_agent

        result = ask_agent("Test question", working_dir="/test/dir")

        assert result == "Test answer"
        mock_agent_class.assert_called_once_with(working_dir="/test/dir")
        mock_agent.ask.assert_called_once_with("Test question")

    @patch('tatty_agent.ProjectInitializer')
    def test_initialize_project_function(self, mock_initializer_class):
        """Test initialize_project convenience function"""
        mock_initializer = Mock()
        mock_initializer_class.return_value = mock_initializer
        mock_initializer.initialize_project.return_value = {"success": True}

        result = initialize_project("/test/dir", force=True)

        assert result["success"] is True
        mock_initializer_class.assert_called_once_with("/test/dir")
        mock_initializer.initialize_project.assert_called_once_with(force=True)


class TestLibraryIntegration:
    """Integration tests for library API"""

    def test_package_imports(self):
        """Test that main package imports work correctly"""
        import tatty_agent

        # Test main class import
        assert hasattr(tatty_agent, 'TattyAgent')
        assert hasattr(tatty_agent, 'run_agent')
        assert hasattr(tatty_agent, 'ask_agent')
        assert hasattr(tatty_agent, 'initialize_project')

        # Test metadata
        assert hasattr(tatty_agent, '__version__')
        assert hasattr(tatty_agent, '__author__')
        assert hasattr(tatty_agent, '__description__')

    def test_config_integration(self):
        """Test configuration integration"""
        from tatty_agent import TattyConfig, load_config

        config = load_config()
        assert isinstance(config, TattyConfig)

    def test_core_components_import(self):
        """Test core component imports"""
        from tatty_agent import AgentRuntime, AgentState, ProjectInitializer

        # These should be importable for advanced users
        assert AgentRuntime is not None
        assert AgentState is not None
        assert ProjectInitializer is not None