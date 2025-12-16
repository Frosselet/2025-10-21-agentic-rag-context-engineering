"""
Enhanced display formatting for Jupyter notebooks

This module provides rich HTML/Markdown output formatting for TATty Agent
in Jupyter notebooks, including syntax highlighting, interactive elements,
and embedded artifacts.
"""
import json
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    from IPython.display import (
        display, HTML, Markdown, Code, JSON, Image,
        Javascript, FileLink, clear_output
    )
    from IPython.core.display import DisplayObject
    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    # Fallback classes for non-Jupyter environments
    class DisplayObject:
        pass

    def display(*args, **kwargs):
        pass

    def HTML(content):
        return content

    def Markdown(content):
        return content


class TattyDisplayFormatter:
    """Rich display formatter for TATty Agent results in Jupyter"""

    def __init__(self, theme: str = "default"):
        self.theme = theme
        self._custom_css_loaded = False

    def _load_custom_css(self):
        """Load custom CSS for TATty Agent displays"""
        if not JUPYTER_AVAILABLE or self._custom_css_loaded:
            return

        css = """
        <style>
        .tatty-agent-output {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 10px 0;
        }

        .tatty-agent-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 12px;
            border-radius: 6px 6px 0 0;
            font-weight: bold;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .tatty-agent-body {
            padding: 12px;
            background: #f8f9fa;
        }

        .tatty-tool-execution {
            border-left: 4px solid #28a745;
            padding-left: 12px;
            margin: 8px 0;
            background: #f8fff9;
            border-radius: 4px;
        }

        .tatty-tool-name {
            font-weight: bold;
            color: #28a745;
            font-size: 13px;
        }

        .tatty-tool-params {
            color: #6c757d;
            font-size: 12px;
            margin: 4px 0;
        }

        .tatty-tool-result {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 8px;
            margin-top: 6px;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }

        .tatty-conversation-entry {
            margin: 10px 0;
            border-radius: 8px;
            overflow: hidden;
        }

        .tatty-user-message {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }

        .tatty-agent-message {
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }

        .tatty-message-header {
            padding: 8px 12px;
            background: rgba(0,0,0,0.05);
            font-weight: bold;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .tatty-message-body {
            padding: 12px;
        }

        .tatty-timestamp {
            color: #6c757d;
            font-size: 11px;
            font-weight: normal;
        }

        .tatty-expandable {
            cursor: pointer;
            user-select: none;
        }

        .tatty-expandable:hover {
            background: rgba(0,0,0,0.05);
        }

        .tatty-collapsed {
            display: none;
        }

        .tatty-progress-bar {
            width: 100%;
            height: 4px;
            background: #e9ecef;
            border-radius: 2px;
            overflow: hidden;
            margin: 8px 0;
        }

        .tatty-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            animation: progress-pulse 2s ease-in-out infinite;
        }

        @keyframes progress-pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }

        .tatty-code-block {
            background: #2d3748;
            color: #e2e8f0;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
        }

        .tatty-artifact-link {
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            color: #856404;
            text-decoration: none;
            font-size: 12px;
            margin: 2px;
        }

        .tatty-artifact-link:hover {
            background: #ffeaa7;
            text-decoration: none;
        }
        </style>
        """

        display(HTML(css))
        self._custom_css_loaded = True

    def display_agent_response(
        self,
        query: str,
        result: str,
        execution_time: float,
        tools_used: List[Dict[str, Any]] = None
    ):
        """Display a complete agent response with rich formatting"""
        self._load_custom_css()

        timestamp = datetime.now().strftime("%H:%M:%S")
        tools_used = tools_used or []

        html_content = f"""
        <div class="tatty-agent-output">
            <div class="tatty-agent-header">
                <span>🤖 TATty Agent Response</span>
                <span class="tatty-timestamp">{timestamp} • {execution_time:.1f}s</span>
            </div>
            <div class="tatty-agent-body">
                <div class="tatty-conversation-entry tatty-user-message">
                    <div class="tatty-message-header">
                        <span>👤 Your Query</span>
                    </div>
                    <div class="tatty-message-body">
                        {self._escape_html(query)}
                    </div>
                </div>

                {self._format_tool_executions(tools_used)}

                <div class="tatty-conversation-entry tatty-agent-message">
                    <div class="tatty-message-header">
                        <span>🤖 Agent Response</span>
                    </div>
                    <div class="tatty-message-body">
                        {self._format_result_content(result)}
                    </div>
                </div>
            </div>
        </div>
        """

        display(HTML(html_content))

        # Also provide raw text for copy-paste
        self._display_raw_text_toggle(result)

    def display_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: str,
        execution_time: float = None
    ):
        """Display individual tool execution with collapsible result"""
        self._load_custom_css()

        tool_id = f"tool_{abs(hash(f'{tool_name}{str(params)}'))}"
        time_str = f" • {execution_time:.2f}s" if execution_time else ""

        params_str = ", ".join([f"{k}={v}" for k, v in params.items() if v is not None])
        if len(params_str) > 100:
            params_str = params_str[:97] + "..."

        html_content = f"""
        <div class="tatty-tool-execution">
            <div class="tatty-tool-name">🛠️ {tool_name}{time_str}</div>
            {f'<div class="tatty-tool-params">{self._escape_html(params_str)}</div>' if params_str else ''}
            <div class="tatty-expandable" onclick="
                var result = document.getElementById('{tool_id}');
                var isHidden = result.style.display === 'none';
                result.style.display = isHidden ? 'block' : 'none';
                this.innerHTML = isHidden ? '📋 Result (click to hide)' : '📋 Result (click to show)';
            ">📋 Result (click to show)</div>
            <div id="{tool_id}" class="tatty-tool-result" style="display: none;">
                {self._escape_html(result)}
            </div>
        </div>
        """

        display(HTML(html_content))

    def display_progress_indicator(self, message: str = "Agent thinking...", show_bar: bool = True):
        """Display a progress indicator for ongoing operations"""
        self._load_custom_css()

        progress_html = """
        <div class="tatty-progress-bar">
            <div class="tatty-progress-fill" style="width: 100%;"></div>
        </div>
        """ if show_bar else ""

        html_content = f"""
        <div class="tatty-agent-output">
            <div class="tatty-agent-header">
                <span>⏳ {message}</span>
            </div>
            <div class="tatty-agent-body">
                {progress_html}
                <div style="text-align: center; color: #6c757d; font-size: 12px;">
                    Processing your request...
                </div>
            </div>
        </div>
        """

        display(HTML(html_content))

    def display_conversation_history(self, history: List[Dict[str, Any]]):
        """Display conversation history in an expandable format"""
        self._load_custom_css()

        if not history:
            display(HTML('<div style="color: #6c757d; text-align: center;">No conversation history</div>'))
            return

        entries_html = ""
        for i, entry in enumerate(history):
            entry_type = entry.get("type", "unknown")
            content = entry.get("content", "")
            timestamp = entry.get("timestamp", "")

            if entry_type == "user_query":
                icon = "👤"
                title = "Your Query"
                css_class = "tatty-user-message"
            elif entry_type == "agent_result":
                icon = "🤖"
                title = "Agent Response"
                css_class = "tatty-agent-message"
            else:
                icon = "⚠️"
                title = entry_type.replace("_", " ").title()
                css_class = "tatty-agent-message"

            entry_id = f"history_{i}"
            short_content = content[:100] + "..." if len(content) > 100 else content

            entries_html += f"""
            <div class="tatty-conversation-entry {css_class}">
                <div class="tatty-message-header tatty-expandable" onclick="
                    var content = document.getElementById('{entry_id}');
                    var isHidden = content.style.display === 'none';
                    content.style.display = isHidden ? 'block' : 'none';
                    this.querySelector('.expand-icon').innerHTML = isHidden ? '🔽' : '▶️';
                ">
                    <span><span class="expand-icon">▶️</span> {icon} {title}</span>
                    <span class="tatty-timestamp">{timestamp}</span>
                </div>
                <div id="{entry_id}" class="tatty-message-body" style="display: none;">
                    {self._format_result_content(content)}
                </div>
                <div class="tatty-message-body" style="color: #6c757d; font-size: 12px;">
                    {self._escape_html(short_content)}
                </div>
            </div>
            """

        html_content = f"""
        <div class="tatty-agent-output">
            <div class="tatty-agent-header">
                <span>📚 Conversation History ({len(history)} entries)</span>
            </div>
            <div class="tatty-agent-body">
                {entries_html}
            </div>
        </div>
        """

        display(HTML(html_content))

    def display_artifact_links(self, artifacts: List[Dict[str, str]]):
        """Display links to generated artifacts"""
        if not artifacts:
            return

        self._load_custom_css()

        links_html = ""
        for artifact in artifacts:
            name = artifact.get("name", "Unknown")
            path = artifact.get("path", "")
            type_icon = self._get_file_icon(path)

            links_html += f"""
            <a href="files/{path}" class="tatty-artifact-link" target="_blank">
                {type_icon} {name}
            </a>
            """

        html_content = f"""
        <div style="margin: 10px 0;">
            <strong>📁 Generated Artifacts:</strong><br>
            {links_html}
        </div>
        """

        display(HTML(html_content))

    def _format_tool_executions(self, tools_used: List[Dict[str, Any]]) -> str:
        """Format tool execution information"""
        if not tools_used:
            return ""

        tools_html = ""
        for tool in tools_used:
            name = tool.get("name", "Unknown")
            params = tool.get("params", {})
            result = tool.get("result", "")
            time_taken = tool.get("execution_time", 0)

            tool_id = f"tool_result_{abs(hash(str(tool)))}"
            params_str = ", ".join([f"{k}={v}" for k, v in params.items() if v is not None])

            tools_html += f"""
            <div class="tatty-tool-execution">
                <div class="tatty-tool-name">🛠️ {name} • {time_taken:.2f}s</div>
                {f'<div class="tatty-tool-params">{self._escape_html(params_str)}</div>' if params_str else ''}
                <div class="tatty-expandable" onclick="
                    var result = document.getElementById('{tool_id}');
                    var isHidden = result.style.display === 'none';
                    result.style.display = isHidden ? 'block' : 'none';
                    this.innerHTML = isHidden ? '📋 Result (click to hide)' : '📋 Result (click to show)';
                ">📋 Result (click to show)</div>
                <div id="{tool_id}" class="tatty-tool-result" style="display: none;">
                    {self._escape_html(result)}
                </div>
            </div>
            """

        return tools_html

    def _format_result_content(self, content: str) -> str:
        """Format result content with syntax highlighting for code blocks"""
        # Simple markdown-style code block detection
        if "```" in content:
            parts = content.split("```")
            formatted = ""
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Regular text
                    formatted += self._escape_html(part)
                else:  # Code block
                    lines = part.split('\n')
                    language = lines[0] if lines else ""
                    code = '\n'.join(lines[1:]) if len(lines) > 1 else part
                    formatted += f'<div class="tatty-code-block">{self._escape_html(code)}</div>'
            return formatted
        else:
            return self._escape_html(content).replace('\n', '<br>')

    def _display_raw_text_toggle(self, text: str):
        """Display a collapsible raw text section for copy-paste"""
        text_id = f"raw_text_{abs(hash(text))}"

        html_content = f"""
        <div style="margin-top: 10px;">
            <button onclick="
                var textDiv = document.getElementById('{text_id}');
                var isHidden = textDiv.style.display === 'none';
                textDiv.style.display = isHidden ? 'block' : 'none';
                this.innerHTML = isHidden ? '📋 Hide Raw Text' : '📋 Show Raw Text (for copy-paste)';
            " style="
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            ">📋 Show Raw Text (for copy-paste)</button>
            <div id="{text_id}" style="
                display: none;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 12px;
                margin-top: 8px;
                font-family: monospace;
                font-size: 12px;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            ">{self._escape_html(text)}</div>
        </div>
        """

        display(HTML(html_content))

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))

    def _get_file_icon(self, path: str) -> str:
        """Get appropriate icon for file type"""
        path_lower = path.lower()
        if path_lower.endswith(('.py', '.ipynb')):
            return "🐍"
        elif path_lower.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return "📜"
        elif path_lower.endswith(('.html', '.htm')):
            return "🌐"
        elif path_lower.endswith(('.css', '.scss', '.sass')):
            return "🎨"
        elif path_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            return "🖼️"
        elif path_lower.endswith(('.pdf', '.doc', '.docx')):
            return "📄"
        elif path_lower.endswith(('.csv', '.xlsx', '.xls')):
            return "📊"
        elif path_lower.endswith(('.md', '.markdown')):
            return "📝"
        else:
            return "📁"


# Global formatter instance
_default_formatter = TattyDisplayFormatter()

# Convenience functions
def display_agent_response(query: str, result: str, execution_time: float, tools_used: List[Dict[str, Any]] = None):
    """Display a rich agent response"""
    _default_formatter.display_agent_response(query, result, execution_time, tools_used)

def display_tool_execution(tool_name: str, params: Dict[str, Any], result: str, execution_time: float = None):
    """Display a tool execution result"""
    _default_formatter.display_tool_execution(tool_name, params, result, execution_time)

def display_progress_indicator(message: str = "Agent thinking...", show_bar: bool = True):
    """Display a progress indicator"""
    _default_formatter.display_progress_indicator(message, show_bar)

def display_conversation_history(history: List[Dict[str, Any]]):
    """Display conversation history"""
    _default_formatter.display_conversation_history(history)

def display_artifact_links(artifacts: List[Dict[str, str]]):
    """Display artifact links"""
    _default_formatter.display_artifact_links(artifacts)