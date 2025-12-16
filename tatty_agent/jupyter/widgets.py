"""
Interactive chat widgets for Jupyter notebooks

This module provides ChatGPT-like chat interface widgets for seamless
TATty Agent interaction within notebook cells.
"""
import asyncio
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

try:
    from IPython.display import display, HTML, clear_output, Javascript
    import ipywidgets as widgets
    from ipywidgets import interact, interactive, fixed, interact_manual
    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    widgets = None

    def display(*args, **kwargs):
        pass

from ..core.runtime import AgentRuntime
from ..core.state import AgentState, AgentCallbacks
from ..config import load_config
from .display import TattyDisplayFormatter
from .notebook import NotebookContextManager
from .progress import LiveExecutionDisplay


class TattyChatWidget:
    """
    Interactive chat widget for TATty Agent in Jupyter notebooks

    Provides a ChatGPT-like interface with:
    - Message input area
    - Conversation history display
    - Real-time typing indicators
    - Expandable message threads
    - Rich response formatting
    """

    def __init__(self, working_dir: str = ".", config: Any = None):
        self.working_dir = working_dir
        self.config = config or load_config(working_dir=working_dir)
        self.notebook_context = NotebookContextManager()
        self.display_formatter = TattyDisplayFormatter()
        self.live_display = LiveExecutionDisplay()

        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_processing = False

        # Widget components
        self._widget = None
        self._input_area = None
        self._chat_output = None
        self._send_button = None
        self._clear_button = None
        self._status_label = None

        if JUPYTER_AVAILABLE and widgets:
            self._create_widget()

    def _create_widget(self):
        """Create the interactive chat widget"""
        if not widgets:
            return

        # Style configuration
        widget_style = {
            'border': '1px solid #e1e4e8',
            'border_radius': '8px',
            'background': 'white'
        }

        # Chat output area (scrollable)
        self._chat_output = widgets.Output(
            layout=widgets.Layout(
                height='400px',
                width='100%',
                overflow='auto',
                border='1px solid #e9ecef',
                border_radius='4px 4px 0 0',
                padding='10px'
            )
        )

        # Input area
        self._input_area = widgets.Textarea(
            value='',
            placeholder='Ask TATty Agent anything... (Shift+Enter to send)',
            layout=widgets.Layout(
                width='100%',
                height='80px',
                resize='vertical'
            ),
            style={'description_width': '0px'}
        )

        # Control buttons
        self._send_button = widgets.Button(
            description="🚀 Send",
            button_style='primary',
            layout=widgets.Layout(width='100px')
        )

        self._clear_button = widgets.Button(
            description="🗑️ Clear",
            button_style='warning',
            layout=widgets.Layout(width='100px')
        )

        self._export_button = widgets.Button(
            description="📤 Export",
            button_style='info',
            layout=widgets.Layout(width='100px')
        )

        # Status label
        self._status_label = widgets.Label(
            value="Ready to chat with TATty Agent",
            layout=widgets.Layout(flex='1')
        )

        # Wire up events
        self._send_button.on_click(self._on_send_clicked)
        self._clear_button.on_click(self._on_clear_clicked)
        self._export_button.on_click(self._on_export_clicked)

        # Handle Shift+Enter in textarea
        self._input_area.observe(self._on_input_change, names='value')

        # Control panel
        control_panel = widgets.HBox([
            self._status_label,
            self._send_button,
            self._clear_button,
            self._export_button
        ], layout=widgets.Layout(
            border='1px solid #e9ecef',
            border_radius='0 0 4px 4px',
            padding='8px'
        ))

        # Input panel
        input_panel = widgets.VBox([
            widgets.HTML("<div style='font-weight: bold; margin-bottom: 5px;'>💬 Chat with TATty Agent</div>"),
            self._input_area
        ])

        # Main widget
        self._widget = widgets.VBox([
            self._chat_output,
            input_panel,
            control_panel
        ], layout=widgets.Layout(
            border='2px solid #667eea',
            border_radius='8px',
            margin='10px 0'
        ))

        # Add welcome message
        self._add_system_message("👋 Welcome to TATty Agent! I'm ready to help with your development tasks.")

    def display(self):
        """Display the chat widget"""
        if not self._widget:
            print("Chat widget not available (requires ipywidgets)")
            return

        display(self._widget)

    def _on_send_clicked(self, button):
        """Handle send button click"""
        self._send_message()

    def _on_clear_clicked(self, button):
        """Handle clear button click"""
        self._clear_conversation()

    def _on_export_clicked(self, button):
        """Handle export button click"""
        self._export_conversation()

    def _on_input_change(self, change):
        """Handle input area changes (for Shift+Enter detection)"""
        # This is a simplified version - actual Shift+Enter detection
        # would require JavaScript integration
        pass

    def _send_message(self):
        """Send the current message"""
        if self.is_processing or not self._input_area.value.strip():
            return

        message = self._input_area.value.strip()
        self._input_area.value = ""

        # Add user message to chat
        self._add_user_message(message)

        # Process the message asynchronously
        self._process_message_async(message)

    def _clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history.clear()
        self._chat_output.clear_output()
        self._add_system_message("Conversation cleared. How can I help you?")

    def _export_conversation(self):
        """Export conversation to a new notebook cell"""
        if not self.conversation_history:
            self._add_system_message("No conversation to export.")
            return

        success = self.notebook_context.export_conversation_to_cell(self.conversation_history)
        if success:
            self._add_system_message("✅ Conversation exported to new cell!")
        else:
            self._add_system_message("❌ Failed to export conversation.")

    def _add_user_message(self, message: str):
        """Add a user message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        with self._chat_output:
            display(HTML(f"""
            <div style="
                margin: 10px 0;
                text-align: right;
            ">
                <div style="
                    display: inline-block;
                    max-width: 80%;
                    background: #007bff;
                    color: white;
                    padding: 12px;
                    border-radius: 18px 18px 4px 18px;
                    text-align: left;
                    word-wrap: break-word;
                ">
                    <div style="font-size: 14px; line-height: 1.4;">
                        {self._escape_html(message)}
                    </div>
                    <div style="
                        font-size: 11px;
                        opacity: 0.8;
                        margin-top: 4px;
                    ">👤 {timestamp}</div>
                </div>
            </div>
            """))

        # Add to conversation history
        self.conversation_history.append({
            "type": "user",
            "content": message,
            "timestamp": timestamp
        })

        # Scroll to bottom
        self._scroll_to_bottom()

    def _add_agent_message(self, message: str, execution_time: float = None, tools_used: int = 0):
        """Add an agent response to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_str = f" • {execution_time:.1f}s" if execution_time else ""
        tools_str = f" • {tools_used} tools" if tools_used else ""

        with self._chat_output:
            display(HTML(f"""
            <div style="
                margin: 10px 0;
                text-align: left;
            ">
                <div style="
                    display: inline-block;
                    max-width: 80%;
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    color: #495057;
                    padding: 12px;
                    border-radius: 18px 18px 18px 4px;
                    text-align: left;
                    word-wrap: break-word;
                ">
                    <div style="font-size: 14px; line-height: 1.4; white-space: pre-wrap;">
                        {self._format_agent_content(message)}
                    </div>
                    <div style="
                        font-size: 11px;
                        color: #6c757d;
                        margin-top: 4px;
                    ">🤖 {timestamp}{time_str}{tools_str}</div>
                </div>
            </div>
            """))

        # Add to conversation history
        self.conversation_history.append({
            "type": "agent",
            "content": message,
            "timestamp": timestamp,
            "execution_time": execution_time,
            "tools_used": tools_used
        })

        # Scroll to bottom
        self._scroll_to_bottom()

    def _add_system_message(self, message: str):
        """Add a system message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        with self._chat_output:
            display(HTML(f"""
            <div style="
                margin: 10px 0;
                text-align: center;
            ">
                <div style="
                    display: inline-block;
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 8px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                ">
                    {self._escape_html(message)}
                </div>
            </div>
            """))

        self._scroll_to_bottom()

    def _add_typing_indicator(self):
        """Add a typing indicator"""
        with self._chat_output:
            display(HTML(f"""
            <div id="typing_indicator" style="
                margin: 10px 0;
                text-align: left;
            ">
                <div style="
                    display: inline-block;
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    color: #6c757d;
                    padding: 12px;
                    border-radius: 18px 18px 18px 4px;
                    font-size: 14px;
                ">
                    <span style="animation: pulse 1.5s infinite;">🤖 TATty is thinking</span>
                    <span style="animation: pulse 1.5s infinite 0.5s;">.</span>
                    <span style="animation: pulse 1.5s infinite 1s;">.</span>
                    <span style="animation: pulse 1.5s infinite 1.5s;">.</span>
                </div>
            </div>

            <style>
            @keyframes pulse {{
                0%, 50%, 100% {{ opacity: 1; }}
                25%, 75% {{ opacity: 0.5; }}
            }}
            </style>
            """), display_id="typing_indicator")

        self._scroll_to_bottom()

    def _remove_typing_indicator(self):
        """Remove the typing indicator"""
        try:
            display(HTML(""), display_id="typing_indicator")
        except:
            pass

    def _process_message_async(self, message: str):
        """Process message asynchronously"""
        def run_agent():
            self.is_processing = True
            self._status_label.value = "🤖 Processing your request..."
            self._send_button.description = "⏳ Processing"
            self._send_button.disabled = True

            self._add_typing_indicator()

            try:
                # Set up agent runtime
                state = AgentState(working_dir=self.working_dir)
                callbacks = self._create_chat_callbacks()
                runtime = AgentRuntime(state, callbacks)

                # Add notebook context if available
                if self.notebook_context:
                    notebook_vars = self.notebook_context.get_notebook_variables()
                    if notebook_vars:
                        context_info = f"Available variables: {', '.join(list(notebook_vars.keys())[:5])}"
                        state.messages.append({
                            "role": "system",
                            "message": f"Notebook context: {context_info}"
                        })

                # Run the agent
                start_time = time.time()
                result = asyncio.run(runtime.run_loop(message, max_iterations=20))
                execution_time = time.time() - start_time

                # Remove typing indicator
                self._remove_typing_indicator()

                # Add agent response
                tools_used = getattr(callbacks, '_tools_count', 0)
                self._add_agent_message(result, execution_time, tools_used)

            except Exception as e:
                self._remove_typing_indicator()
                self._add_agent_message(f"Sorry, I encountered an error: {str(e)}")

            finally:
                self.is_processing = False
                self._status_label.value = "Ready for your next question"
                self._send_button.description = "🚀 Send"
                self._send_button.disabled = False

        # Run in a separate thread to avoid blocking the UI
        thread = threading.Thread(target=run_agent)
        thread.daemon = True
        thread.start()

    def _create_chat_callbacks(self) -> AgentCallbacks:
        """Create callbacks for chat interface"""
        callbacks = AgentCallbacks()
        callbacks._tools_count = 0

        async def on_tool_start(tool_name: str, params: dict, tool_idx: int, total_tools: int, depth: int):
            callbacks._tools_count += 1
            self._status_label.value = f"🛠️ Using {tool_name}... ({tool_idx}/{total_tools})"

        async def on_iteration(iteration: int, depth: int):
            self._status_label.value = f"🔄 Thinking (iteration {iteration})..."

        callbacks.on_tool_start = on_tool_start
        callbacks.on_iteration = on_iteration

        return callbacks

    def _format_agent_content(self, content: str) -> str:
        """Format agent content with basic markdown-like styling"""
        # Simple code block formatting
        if "```" in content:
            parts = content.split("```")
            formatted = ""
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Regular text
                    formatted += self._escape_html(part)
                else:  # Code block
                    formatted += f'<div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 8px; margin: 4px 0; font-family: monospace; font-size: 12px; overflow-x: auto;">{self._escape_html(part)}</div>'
            return formatted
        else:
            return self._escape_html(content).replace('\n', '<br>')

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))

    def _scroll_to_bottom(self):
        """Scroll chat to bottom (requires JavaScript integration)"""
        try:
            display(Javascript("""
            setTimeout(function() {
                var outputs = document.querySelectorAll('.jp-OutputArea-output');
                if (outputs.length > 0) {
                    var lastOutput = outputs[outputs.length - 1];
                    lastOutput.scrollTop = lastOutput.scrollHeight;
                }
            }, 100);
            """))
        except:
            pass  # Ignore scroll failures

    def send_message(self, message: str):
        """Programmatically send a message"""
        if self._input_area:
            self._input_area.value = message
            self._send_message()
        else:
            # Fallback for non-widget mode
            print(f"Sending message: {message}")

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history"""
        return self.conversation_history.copy()


def create_chat_widget(working_dir: str = ".", config: Any = None) -> TattyChatWidget:
    """
    Create a new chat widget instance

    Args:
        working_dir: Working directory for the agent
        config: Optional configuration override

    Returns:
        TattyChatWidget instance

    Example:
        ```python
        from tatty_agent.jupyter import create_chat_widget

        chat = create_chat_widget()
        chat.display()
        ```
    """
    return TattyChatWidget(working_dir, config)


def create_quick_chat() -> Optional[TattyChatWidget]:
    """
    Create and immediately display a chat widget

    Returns:
        TattyChatWidget instance or None if widgets not available

    Example:
        ```python
        from tatty_agent.jupyter import create_quick_chat

        chat = create_quick_chat()  # Automatically displayed
        ```
    """
    if not JUPYTER_AVAILABLE or not widgets:
        print("Interactive chat widget requires ipywidgets in Jupyter")
        return None

    chat = TattyChatWidget()
    chat.display()
    return chat