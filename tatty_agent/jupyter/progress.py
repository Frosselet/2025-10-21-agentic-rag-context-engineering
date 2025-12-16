"""
Live tool execution display with progress indicators for Jupyter notebooks

This module provides real-time progress bars, status indicators, and
collapsible output sections for tool execution in notebooks.
"""
import asyncio
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from contextlib import contextmanager

try:
    from IPython.display import display, HTML, clear_output, update_display
    from IPython.core.display import DisplayObject
    import ipywidgets as widgets
    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    widgets = None

    def display(*args, **kwargs):
        pass

    def clear_output(wait=True):
        pass

    def update_display(*args, **kwargs):
        pass


class ToolExecutionProgressTracker:
    """Tracks and displays tool execution progress in real-time"""

    def __init__(self):
        self.current_tool: Optional[str] = None
        self.current_progress: float = 0.0
        self.execution_start: Optional[float] = None
        self.tool_history: List[Dict[str, Any]] = []
        self._display_id: Optional[str] = None
        self._interrupt_requested: bool = False
        self._status_widgets: Dict[str, Any] = {}

    def start_tool_execution(self, tool_name: str, params: Dict[str, Any] = None):
        """Start tracking a new tool execution"""
        self.current_tool = tool_name
        self.current_progress = 0.0
        self.execution_start = time.time()
        self._interrupt_requested = False

        # Create unique display ID
        self._display_id = f"tool_progress_{abs(hash(f'{tool_name}_{time.time()}'))}"

        # Display initial progress
        self._display_initial_progress(tool_name, params or {})

    def update_progress(self, progress: float, status: str = None):
        """Update the current tool's progress"""
        if not self.current_tool:
            return

        self.current_progress = min(100.0, max(0.0, progress))

        # Update display
        self._update_progress_display(status)

    def complete_tool_execution(self, result: str, success: bool = True):
        """Complete the current tool execution"""
        if not self.current_tool:
            return

        execution_time = time.time() - self.execution_start if self.execution_start else 0

        # Store in history
        self.tool_history.append({
            "name": self.current_tool,
            "execution_time": execution_time,
            "success": success,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Display completion
        self._display_completion(result, execution_time, success)

        # Reset current tool
        self.current_tool = None
        self.current_progress = 0.0
        self.execution_start = None

    def request_interrupt(self):
        """Request interruption of current tool execution"""
        self._interrupt_requested = True

    def is_interrupt_requested(self) -> bool:
        """Check if interruption has been requested"""
        return self._interrupt_requested

    def _display_initial_progress(self, tool_name: str, params: Dict[str, Any]):
        """Display initial progress indicator"""
        if not JUPYTER_AVAILABLE:
            return

        # Create parameter string
        param_str = ", ".join([f"{k}={v}" for k, v in params.items() if v is not None])
        if len(param_str) > 80:
            param_str = param_str[:77] + "..."

        # Create HTML for initial display
        html_content = f"""
        <div id="{self._display_id}" style="
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 10px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        ">
            <div style="
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 12px;
                border-radius: 6px 6px 0 0;
                font-weight: bold;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <span>🛠️ Executing {tool_name}</span>
                <button onclick="
                    // Signal interruption (would need backend integration)
                    this.innerHTML = '⏸️ Interrupted';
                    this.disabled = true;
                " style="
                    background: rgba(255,255,255,0.2);
                    border: 1px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 11px;
                ">❌ Cancel</button>
            </div>
            <div style="padding: 12px; background: #f8f9fa;">
                {f'<div style="color: #6c757d; font-size: 12px; margin-bottom: 8px;">{param_str}</div>' if param_str else ''}
                <div style="
                    background: #e9ecef;
                    border-radius: 10px;
                    height: 6px;
                    overflow: hidden;
                    margin: 8px 0;
                ">
                    <div style="
                        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        height: 100%;
                        width: 0%;
                        transition: width 0.3s ease;
                        animation: pulse 2s ease-in-out infinite;
                    " id="{self._display_id}_bar"></div>
                </div>
                <div id="{self._display_id}_status" style="
                    color: #495057;
                    font-size: 12px;
                    text-align: center;
                ">Starting execution...</div>
            </div>
        </div>

        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
        }}
        </style>
        """

        display(HTML(html_content), display_id=self._display_id)

    def _update_progress_display(self, status: str = None):
        """Update the progress display"""
        if not JUPYTER_AVAILABLE or not self._display_id:
            return

        elapsed_time = time.time() - self.execution_start if self.execution_start else 0
        status_text = status or f"Executing... ({elapsed_time:.1f}s)"

        # Update progress bar and status
        js_update = f"""
        <script>
        (function() {{
            var bar = document.getElementById('{self._display_id}_bar');
            var status = document.getElementById('{self._display_id}_status');

            if (bar) {{
                bar.style.width = '{self.current_progress}%';
            }}

            if (status) {{
                status.innerHTML = '{status_text}';
            }}
        }})();
        </script>
        """

        try:
            update_display(HTML(js_update), display_id=f"{self._display_id}_update")
        except:
            pass  # Ignore update failures

    def _display_completion(self, result: str, execution_time: float, success: bool):
        """Display tool execution completion"""
        if not JUPYTER_AVAILABLE or not self._display_id:
            return

        status_icon = "✅" if success else "❌"
        status_text = "Completed" if success else "Failed"
        result_preview = result[:100] + "..." if len(result) > 100 else result

        # Create expandable result section
        result_id = f"{self._display_id}_result"
        html_completion = f"""
        <div id="{self._display_id}" style="
            border: 1px solid #{'d4edda' if success else 'f5c6cb'};
            border-radius: 6px;
            margin: 10px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        ">
            <div style="
                background: {'#d4edda' if success else '#f5c6cb'};
                color: {'#155724' if success else '#721c24'};
                padding: 8px 12px;
                border-radius: 6px 6px 0 0;
                font-weight: bold;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <span>{status_icon} {self.current_tool} {status_text}</span>
                <span style="font-weight: normal; font-size: 12px;">{execution_time:.2f}s</span>
            </div>
            <div style="padding: 12px; background: #f8f9fa;">
                <div style="
                    color: #6c757d;
                    font-size: 12px;
                    margin-bottom: 8px;
                ">{result_preview}</div>
                <div style="text-align: center;">
                    <button onclick="
                        var resultDiv = document.getElementById('{result_id}');
                        var isHidden = resultDiv.style.display === 'none';
                        resultDiv.style.display = isHidden ? 'block' : 'none';
                        this.innerHTML = isHidden ? '📋 Hide Full Result' : '📋 Show Full Result';
                    " style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 12px;
                    ">📋 Show Full Result</button>
                </div>
                <div id="{result_id}" style="
                    display: none;
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 12px;
                    margin-top: 8px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 12px;
                    white-space: pre-wrap;
                ">{self._escape_html(result)}</div>
            </div>
        </div>
        """

        try:
            update_display(HTML(html_completion), display_id=self._display_id)
        except:
            # Fallback to regular display
            display(HTML(html_completion))

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))


class LiveExecutionDisplay:
    """Provides live execution display with interactive controls"""

    def __init__(self):
        self.tracker = ToolExecutionProgressTracker()
        self._active_executions: Dict[str, Any] = {}

    @contextmanager
    def tool_execution(self, tool_name: str, params: Dict[str, Any] = None):
        """Context manager for tool execution with progress tracking"""
        self.tracker.start_tool_execution(tool_name, params or {})
        success = False
        result = ""

        try:
            yield self.tracker
            success = True
        except KeyboardInterrupt:
            result = "Execution interrupted by user"
            raise
        except Exception as e:
            result = f"Execution failed: {str(e)}"
            raise
        else:
            result = "Execution completed successfully"
        finally:
            if not result:
                result = "Execution completed"
            self.tracker.complete_tool_execution(result, success)

    def display_execution_summary(self):
        """Display summary of all tool executions"""
        if not self.tracker.tool_history:
            display(HTML('<div style="color: #6c757d; text-align: center;">No tool executions recorded</div>'))
            return

        total_time = sum(tool["execution_time"] for tool in self.tracker.tool_history)
        successful_count = sum(1 for tool in self.tracker.tool_history if tool["success"])
        total_count = len(self.tracker.tool_history)

        # Create summary table
        rows = ""
        for tool in self.tracker.tool_history[-10:]:  # Show last 10 executions
            status_icon = "✅" if tool["success"] else "❌"
            timestamp = tool["timestamp"][:19]  # Remove microseconds
            time_str = f"{tool['execution_time']:.2f}s"

            rows += f"""
            <tr>
                <td style="text-align: center;">{status_icon}</td>
                <td>{tool['name']}</td>
                <td style="text-align: right;">{time_str}</td>
                <td style="font-size: 11px; color: #6c757d;">{timestamp}</td>
            </tr>
            """

        html_summary = f"""
        <div style="
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 10px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        ">
            <div style="
                background: #f6f8fa;
                padding: 12px;
                border-radius: 6px 6px 0 0;
                border-bottom: 1px solid #e1e4e8;
                font-weight: bold;
            ">
                📊 Execution Summary: {successful_count}/{total_count} successful • {total_time:.1f}s total
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 8px; border-bottom: 1px solid #e1e4e8;">Status</th>
                        <th style="padding: 8px; border-bottom: 1px solid #e1e4e8; text-align: left;">Tool</th>
                        <th style="padding: 8px; border-bottom: 1px solid #e1e4e8; text-align: right;">Time</th>
                        <th style="padding: 8px; border-bottom: 1px solid #e1e4e8; text-align: left;">Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

        display(HTML(html_summary))


# Global live execution display instance
_live_display: Optional[LiveExecutionDisplay] = None

def get_live_display() -> LiveExecutionDisplay:
    """Get the global live execution display"""
    global _live_display
    if _live_display is None:
        _live_display = LiveExecutionDisplay()
    return _live_display

def track_tool_execution(tool_name: str, params: Dict[str, Any] = None):
    """Context manager for tracking tool execution"""
    return get_live_display().tool_execution(tool_name, params)

def display_execution_summary():
    """Display execution summary"""
    get_live_display().display_execution_summary()

def create_interactive_execution_widget() -> Optional[Any]:
    """Create an interactive widget for controlling tool execution"""
    if not JUPYTER_AVAILABLE or not widgets:
        return None

    # Create widget components
    output = widgets.Output()
    progress_bar = widgets.FloatProgress(
        value=0,
        min=0,
        max=100.0,
        description='Progress:',
        bar_style='info',
        style={'bar_color': '#667eea'},
        layout=widgets.Layout(width='100%')
    )

    status_label = widgets.Label(value="Ready to execute tools...")
    cancel_button = widgets.Button(
        description="❌ Cancel",
        button_style='danger',
        layout=widgets.Layout(width='100px')
    )

    def on_cancel_clicked(b):
        get_live_display().tracker.request_interrupt()
        status_label.value = "Cancellation requested..."

    cancel_button.on_click(on_cancel_clicked)

    # Create layout
    control_box = widgets.HBox([
        widgets.VBox([progress_bar, status_label], layout=widgets.Layout(flex='1')),
        cancel_button
    ])

    execution_widget = widgets.VBox([
        widgets.HTML("<h4>🛠️ Tool Execution Control</h4>"),
        control_box,
        output
    ])

    return execution_widget