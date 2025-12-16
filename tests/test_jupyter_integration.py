"""
Integration tests for Jupyter components of TATty Agent

Tests the Jupyter-specific functionality including:
- Display formatting
- Magic commands
- Widget functionality
- Notebook integration
- Progress tracking
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path


class TestJupyterDisplayIntegration:
    """Integration tests for Jupyter display components"""

    def test_display_components_import(self):
        """Test that display components can be imported"""
        try:
            from tatty_agent.jupyter.display import (
                TattyDisplayFormatter,
                display_agent_response,
                display_tool_execution,
                display_progress_indicator
            )
            assert True
        except ImportError as e:
            pytest.skip(f"Jupyter dependencies not available: {e}")

    def test_agent_response_display(self):
        """Test agent response display formatting"""
        try:
            from tatty_agent.jupyter.display import display_agent_response

            # Should not crash with typical usage
            tools_used = [
                {
                    "name": "Read",
                    "params": {"file_path": "test.py"},
                    "result": "File content",
                    "execution_time": 0.5
                }
            ]

            with patch('tatty_agent.jupyter.display.display') as mock_display:
                display_agent_response(
                    query="Test query",
                    result="Test result",
                    execution_time=1.0,
                    tools_used=tools_used
                )
                # Should have called display
                assert mock_display.called

        except ImportError:
            pytest.skip("Jupyter dependencies not available")

    def test_tool_execution_display(self):
        """Test tool execution display formatting"""
        try:
            from tatty_agent.jupyter.display import display_tool_execution

            with patch('tatty_agent.jupyter.display.display') as mock_display:
                display_tool_execution(
                    tool_name="TestTool",
                    params={"param1": "value1"},
                    result="Tool result",
                    execution_time=0.3
                )
                assert mock_display.called

        except ImportError:
            pytest.skip("Jupyter dependencies not available")


class TestJupyterMagicIntegration:
    """Integration tests for IPython magic commands"""

    def test_magic_module_import(self):
        """Test that magic module can be imported"""
        try:
            from tatty_agent.jupyter import magic
            assert hasattr(magic, 'TattyMagics')
        except ImportError:
            pytest.skip("IPython dependencies not available")

    def test_magic_registration(self):
        """Test magic command registration"""
        try:
            from tatty_agent.jupyter.magic import TattyMagics
            from IPython.core.magic import Magics

            # Should be a proper magic class
            assert issubclass(TattyMagics, Magics)

            # Should have the expected magic methods
            magic_instance = TattyMagics()
            assert hasattr(magic_instance, 'tatty')
            assert hasattr(magic_instance, 'tatty_cell')

        except ImportError:
            pytest.skip("IPython dependencies not available")

    @patch('tatty_agent.jupyter.magic.TattyAgent')
    def test_line_magic_execution(self, mock_agent_class):
        """Test line magic execution"""
        try:
            from tatty_agent.jupyter.magic import TattyMagics
            from IPython.testing.tools import line_magic

            # Setup mock
            mock_agent = Mock()
            mock_agent.run.return_value = "Magic result"
            mock_agent_class.return_value = mock_agent

            magic_instance = TattyMagics()

            # Test line magic
            with patch.object(magic_instance, 'shell', create=True):
                result = magic_instance.tatty('test query')
                assert "Magic result" in str(result)

        except ImportError:
            pytest.skip("IPython dependencies not available")


class TestJupyterNotebookIntegration:
    """Integration tests for notebook context management"""

    def test_notebook_context_import(self):
        """Test notebook context components import"""
        try:
            from tatty_agent.jupyter.notebook import (
                NotebookContextManager,
                get_notebook_context,
                get_notebook_variables,
                execute_in_notebook
            )
            assert True
        except ImportError:
            pytest.skip("IPython dependencies not available")

    def test_notebook_context_manager(self):
        """Test notebook context manager functionality"""
        try:
            from tatty_agent.jupyter.notebook import NotebookContextManager

            with patch('tatty_agent.jupyter.notebook.get_ipython') as mock_get_ipython:
                mock_ipython = Mock()
                mock_ipython.user_ns = {
                    'test_var': 'test_value',
                    'test_dict': {'key': 'value'}
                }
                mock_get_ipython.return_value = mock_ipython

                context = NotebookContextManager()
                variables = context.get_notebook_variables()

                assert 'test_var' in variables
                assert variables['test_var'] == 'test_value'

        except ImportError:
            pytest.skip("IPython dependencies not available")

    def test_execute_in_notebook(self):
        """Test code execution in notebook context"""
        try:
            from tatty_agent.jupyter.notebook import execute_in_notebook

            with patch('tatty_agent.jupyter.notebook.get_ipython') as mock_get_ipython:
                mock_ipython = Mock()
                mock_ipython.run_cell.return_value.success = True
                mock_ipython.run_cell.return_value.result = "execution_result"
                mock_get_ipython.return_value = mock_ipython

                result = execute_in_notebook("print('test')")

                assert result['success'] is True
                assert result['result'] == "execution_result"

        except ImportError:
            pytest.skip("IPython dependencies not available")


class TestJupyterProgressIntegration:
    """Integration tests for progress tracking components"""

    def test_progress_components_import(self):
        """Test progress tracking components import"""
        try:
            from tatty_agent.jupyter.progress import (
                ToolExecutionProgressTracker,
                track_tool_execution,
                display_execution_summary
            )
            assert True
        except ImportError:
            pytest.skip("IPython/ipywidgets dependencies not available")

    def test_progress_tracker_context_manager(self):
        """Test progress tracker as context manager"""
        try:
            from tatty_agent.jupyter.progress import track_tool_execution

            with patch('tatty_agent.jupyter.progress.display') as mock_display:
                with track_tool_execution("TestTool", {"param": "value"}) as tracker:
                    assert tracker is not None
                    # Should not crash
                    tracker.update_progress(50, "Halfway done")

                # Should have displayed something
                assert mock_display.called

        except ImportError:
            pytest.skip("IPython/ipywidgets dependencies not available")

    def test_execution_summary_display(self):
        """Test execution summary display"""
        try:
            from tatty_agent.jupyter.progress import display_execution_summary

            execution_data = {
                'tool_name': 'TestTool',
                'start_time': 1000,
                'end_time': 1005,
                'result': 'Test result',
                'success': True
            }

            with patch('tatty_agent.jupyter.progress.display') as mock_display:
                display_execution_summary(execution_data)
                assert mock_display.called

        except ImportError:
            pytest.skip("IPython dependencies not available")


class TestJupyterWidgetIntegration:
    """Integration tests for Jupyter widget components"""

    def test_widget_components_import(self):
        """Test widget components import"""
        try:
            from tatty_agent.jupyter.widgets import (
                TattyChatWidget,
                create_chat_widget,
                create_quick_chat
            )
            assert True
        except ImportError:
            pytest.skip("ipywidgets dependencies not available")

    def test_chat_widget_creation(self):
        """Test chat widget creation"""
        try:
            from tatty_agent.jupyter.widgets import TattyChatWidget

            with tempfile.TemporaryDirectory() as temp_dir:
                # Should not crash during initialization
                widget = TattyChatWidget(working_dir=temp_dir)
                assert widget is not None

        except ImportError:
            pytest.skip("ipywidgets dependencies not available")

    def test_quick_chat_creation(self):
        """Test quick chat widget creation"""
        try:
            from tatty_agent.jupyter.widgets import create_quick_chat

            # Should not crash
            with patch('tatty_agent.jupyter.widgets.TattyChatWidget') as mock_widget:
                mock_instance = Mock()
                mock_widget.return_value = mock_instance

                chat = create_quick_chat()
                assert chat is not None

        except ImportError:
            pytest.skip("ipywidgets dependencies not available")


class TestJupyterFullIntegration:
    """Full integration tests combining multiple Jupyter components"""

    def test_complete_jupyter_workflow(self):
        """Test complete Jupyter integration workflow"""
        try:
            # Import all main components
            from tatty_agent.jupyter import (
                create_quick_chat,
                display_agent_response,
                get_notebook_context,
                track_tool_execution
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                # Test workflow should not crash
                with patch('tatty_agent.jupyter.display.display'):
                    with patch('tatty_agent.jupyter.notebook.get_ipython'):
                        # Create chat widget
                        chat = create_quick_chat()

                        # Display agent response
                        display_agent_response(
                            query="Test query",
                            result="Test result",
                            execution_time=1.0
                        )

                        # Track tool execution
                        with track_tool_execution("TestTool", {}) as tracker:
                            tracker.update_progress(100, "Done")

                        # Should complete without errors
                        assert True

        except ImportError:
            pytest.skip("Jupyter dependencies not available")

    def test_jupyter_import_accessibility(self):
        """Test that all Jupyter components are accessible from main module"""
        try:
            # These should be importable from the main jupyter module
            from tatty_agent.jupyter import (
                # Display components
                display_agent_response,
                display_tool_execution,

                # Notebook components
                get_notebook_context,
                execute_in_notebook,

                # Progress components
                track_tool_execution,

                # Widget components
                create_chat_widget,
                create_quick_chat,

                # Magic module
                magic
            )

            assert True  # All imports successful

        except ImportError:
            pytest.skip("Jupyter dependencies not available")


class TestJupyterErrorHandling:
    """Test error handling in Jupyter components"""

    def test_graceful_fallback_without_ipython(self):
        """Test graceful fallback when IPython is not available"""
        with patch.dict('sys.modules', {'IPython': None}):
            try:
                from tatty_agent.jupyter.notebook import get_notebook_variables

                # Should return empty dict or handle gracefully
                variables = get_notebook_variables()
                assert isinstance(variables, dict)

            except ImportError:
                # This is also acceptable - explicit requirement for IPython
                pass

    def test_widget_fallback_without_ipywidgets(self):
        """Test widget fallback when ipywidgets is not available"""
        with patch.dict('sys.modules', {'ipywidgets': None}):
            try:
                from tatty_agent.jupyter.widgets import create_quick_chat
                # Should either work with fallback or raise clear error
                chat = create_quick_chat()

            except ImportError as e:
                # Should have helpful error message
                assert "ipywidgets" in str(e).lower() or "widget" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])