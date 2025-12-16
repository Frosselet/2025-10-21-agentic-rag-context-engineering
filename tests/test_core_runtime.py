"""
Tests for core runtime functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from tatty_agent.core.runtime import AgentRuntime
from tatty_agent.core.state import AgentState, AgentCallbacks


class TestAgentRuntime:
    """Test suite for AgentRuntime"""

    @pytest.fixture
    def agent_state(self):
        """Create a test agent state"""
        return AgentState(working_dir="/tmp/test")

    @pytest.fixture
    def agent_callbacks(self):
        """Create test callbacks"""
        callbacks = AgentCallbacks()
        callbacks.on_iteration = AsyncMock()
        callbacks.on_tool_start = AsyncMock()
        callbacks.on_tool_result = AsyncMock()
        callbacks.on_agent_reply = AsyncMock()
        return callbacks

    @pytest.fixture
    def agent_runtime(self, agent_state, agent_callbacks):
        """Create a test agent runtime"""
        return AgentRuntime(agent_state, agent_callbacks)

    def test_runtime_initialization(self, agent_runtime, agent_state, agent_callbacks):
        """Test runtime initialization"""
        assert agent_runtime.state == agent_state
        assert agent_runtime.callbacks == agent_callbacks
        assert AgentRuntime._current_state == agent_state

    @pytest.mark.asyncio
    async def test_execute_tool_non_agent(self, agent_runtime):
        """Test tool execution for non-Agent tools"""
        from tatty_agent.core.types import types

        # Mock tool
        mock_tool = Mock()
        mock_tool.action = "TestTool"

        # Mock the execute_tool function
        with patch('tatty_agent.tools.registry.execute_tool', return_value="test result") as mock_execute:
            result = await agent_runtime.execute_tool(mock_tool)

            assert result == "test result"
            mock_execute.assert_called_once_with(mock_tool, agent_runtime.state.working_dir)

    @pytest.mark.asyncio
    async def test_execute_tool_agent_type(self, agent_runtime):
        """Test tool execution for Agent type (sub-agent)"""
        from tatty_agent.core.types import types

        # Mock tool
        mock_tool = Mock()
        mock_tool.action = "Agent"
        mock_tool.description = "Test sub-agent"
        mock_tool.prompt = "Test prompt"

        with patch.object(agent_runtime, 'execute_sub_agent', return_value="sub-agent result") as mock_sub_agent:
            result = await agent_runtime.execute_tool(mock_tool, depth=1)

            assert result == "sub-agent result"
            mock_sub_agent.assert_called_once_with(mock_tool, 1)

    @pytest.mark.asyncio
    async def test_run_iteration_interrupt(self, agent_runtime):
        """Test run_iteration with interrupt requested"""
        agent_runtime.state.interrupt_requested = True

        is_complete, result = await agent_runtime.run_iteration()

        assert is_complete is True
        assert "interrupted" in result.lower()

    @pytest.mark.asyncio
    async def test_run_loop_basic(self, agent_runtime):
        """Test basic run_loop functionality"""
        with patch.object(agent_runtime, 'run_iteration') as mock_iteration:
            # Mock successful completion on first iteration
            mock_iteration.return_value = (True, "Test completed")

            result = await agent_runtime.run_loop("Test query", max_iterations=5)

            assert result == "Test completed"
            mock_iteration.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_run_loop_max_iterations(self, agent_runtime):
        """Test run_loop reaching max iterations"""
        with patch.object(agent_runtime, 'run_iteration') as mock_iteration:
            # Mock never completing
            mock_iteration.return_value = (False, None)

            result = await agent_runtime.run_loop("Test query", max_iterations=2)

            assert "maximum iterations" in result.lower()
            assert mock_iteration.call_count == 2


class TestAgentState:
    """Test suite for AgentState"""

    def test_state_initialization(self):
        """Test agent state initialization"""
        state = AgentState(working_dir="/test/dir")

        assert state.working_dir == "/test/dir"
        assert state.messages == []
        assert state.todos == []
        assert state.interrupt_requested is False
        assert state.current_iteration == 0
        assert state.current_depth == 0

    def test_state_defaults(self):
        """Test agent state with default values"""
        state = AgentState()

        assert state.working_dir == "."
        assert isinstance(state.messages, list)
        assert isinstance(state.todos, list)


class TestAgentCallbacks:
    """Test suite for AgentCallbacks"""

    def test_callbacks_initialization(self):
        """Test callbacks initialization"""
        callbacks = AgentCallbacks()

        assert callbacks.on_iteration is None
        assert callbacks.on_tool_start is None
        assert callbacks.on_tool_result is None
        assert callbacks.on_agent_reply is None
        assert callbacks.on_status_update is None
        assert callbacks.on_sub_agent_start is None
        assert callbacks.on_sub_agent_complete is None

    def test_callbacks_assignment(self):
        """Test callback function assignment"""
        callbacks = AgentCallbacks()

        async def test_callback():
            pass

        callbacks.on_iteration = test_callback
        assert callbacks.on_iteration == test_callback