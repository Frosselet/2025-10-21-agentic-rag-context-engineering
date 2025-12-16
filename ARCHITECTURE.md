# Architecture Overview

## Module Structure

The codebase is now cleanly separated into three modules:

### 1. `main.py` - Tool Handlers & CLI Interface
**Responsibilities:**
- Individual tool handler functions (`execute_bash`, `execute_glob`, etc.)
- CLI argument parsing and modes (single command, interactive)
- Shared `_todo_store` for in-memory todo list
- Simple print-based callbacks for CLI output

**Key Functions:**
```python
execute_bash(tool: BashTool) -> str
execute_glob(tool: GlobTool) -> str
execute_read(tool: ReadTool) -> str
# ... 13 more tool handlers

async execute_tool(tool: AgentTools) -> str  # Dispatcher using match
```

### 2. `agent_runtime.py` - Shared Agent Logic
**Responsibilities:**
- Core agent state management (`AgentState`)
- Agent execution loop logic
- Sub-agent handling
- Callback system for UI updates
- No UI code - pure business logic

**Key Classes:**
```python
@dataclass
class AgentState:
    messages: list[Message]          # Conversation history
    todos: list[TodoItem]            # Todo list (not used yet)
    interrupt_requested: bool        # Interrupt flag
    current_iteration: int           # Tracking
    current_depth: int               # Sub-agent nesting level

@dataclass  
class AgentCallbacks:
    on_iteration: Callable           # When iteration starts
    on_tool_start: Callable          # Before tool executes
    on_tool_result: Callable         # After tool completes
    on_agent_reply: Callable         # When agent replies to user
    on_status_update: Callable       # Status changes
    on_sub_agent_start: Callable     # Sub-agent launches
    on_sub_agent_complete: Callable  # Sub-agent finishes

class AgentRuntime:
    def __init__(state, callbacks)
    async def execute_tool(tool, depth) -> str
    async def execute_sub_agent(tool, parent_depth) -> str
    async def run_iteration(depth) -> (bool, str)
    async def run_loop(user_message, max_iterations, depth) -> str
```

### 3. `tui.py` - Beautiful TUI Interface
**Responsibilities:**
- Textual/Rich-based UI components
- Widget rendering (StatusBar, AgentLog, TodoPanel, CommandInput)
- Event handling (keyboard shortcuts, input submission)
- Callback implementations that update UI
- No agent logic - just presentation

**Key Classes:**
```python
class StatusBar(Static)          # Shows dir, iteration, status
class TodoPanel(Static)          # Live todo list
class AgentLog(RichLog)          # Scrollable activity log
class CommandInput(Input)        # Command input field

class BAMMYApp(App):
    # Implements callbacks that update UI:
    async def on_iteration()
    async def on_tool_start()
    async def on_tool_result()
    async def on_sub_agent_start()
    async def on_sub_agent_complete()
    
    async def process_command()  # Delegates to AgentRuntime
```

## Data Flow

```
User Input
    ↓
┌─────────────────────────────────────────────┐
│  main.py (CLI) or tui.py (TUI)             │
│  - Parse input                              │
│  - Set up callbacks                         │
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  agent_runtime.py                           │
│  - AgentState (messages, todos, flags)      │
│  - AgentRuntime                             │
│    - run_loop()                             │
│      ├─ Call BAML async client             │
│      ├─ Trigger callbacks (UI updates)      │
│      ├─ Execute tools via main.py           │
│      └─ Handle sub-agents recursively       │
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  main.py - Tool Handlers                    │
│  - execute_bash()                           │
│  - execute_glob()                           │
│  - execute_read()                           │
│  - ... etc (16 tools total)                 │
│  - execute_tool() dispatcher (match)        │
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  BAML Client (async)                        │
│  - AgentLoop(state) -> Tools[] | Reply      │
└─────────────────────────────────────────────┘
```

## Benefits of This Architecture

### 1. **Separation of Concerns**
- Business logic in `agent_runtime.py`
- Tool implementations in `main.py`
- UI code in `tui.py`

### 2. **Code Reuse**
- Both CLI and TUI use the same `AgentRuntime`
- No duplicate agent loop logic
- Shared state management

### 3. **Easy Testing**
- Can test `AgentRuntime` without UI
- Can test tool handlers independently
- Mock callbacks for testing

### 4. **Maintainability**
- Single source of truth for agent logic
- Changes to agent behavior update both CLI and TUI
- Clear responsibilities for each module

### 5. **Extensibility**
- Easy to add new UIs (web interface, etc.)
- Easy to add new tools (just add to main.py)
- Easy to modify agent behavior (just edit agent_runtime.py)

## Async Architecture

All BAML calls use `baml_client.async_client`:

```python
from baml_client.async_client import b

# Fully async, non-blocking
response = await b.AgentLoop(state=messages)
```

Benefits:
- TUI stays responsive during agent execution
- Can interrupt at any time (Ctrl+X)
- Multiple async sleep points for UI updates
- Proper async sub-agent recursion

## Interrupt Handling

Interrupts are handled at multiple checkpoints:

```python
# Check before each iteration
if state.interrupt_requested:
    return "Interrupted"

# Check after BAML call
if state.interrupt_requested:
    return "Interrupted"

# Check before each tool
if state.interrupt_requested:
    return "Interrupted"
```

User presses Ctrl+X → Sets `state.interrupt_requested = True` → Agent stops at next checkpoint

## Sub-Agent Design

### Preventing Infinite Recursion

Sub-agents use a different BAML function (`SubAgentLoop`) that has restricted tool access:

```python
# Main agent (agent.baml)
function AgentLoop(state, working_dir) -> AgentTools[] | ReplyString
  # AgentTools includes all tools + AgentTool
  # Comprehensive prompt with task management, security, and best practices

# Sub-agent (agent.baml)
function SubAgentLoop(goal, state, working_dir) -> SubAgentTools[] | ReplyString
  # SubAgentTools excludes AgentTool - no nested sub-agents!
  # Focused prompt for specific task completion
```

**Prompt Features:**
- **Task Management**: Extensive use of TodoWrite/TodoRead tools
- **Security**: Refuses malicious code, follows security best practices
- **Code Quality**: Follows existing conventions, runs lint/typecheck
- **Communication**: Concise, direct responses without unnecessary explanations
- **Proactiveness**: Takes appropriate actions while avoiding surprises
- **Tool Usage**: Parallel tool execution, batched operations

**Tool Sets:**
- `AgentTools` = `SubAgentTools | AgentTool` (can spawn sub-agents)
- `SubAgentTools` = All tools EXCEPT AgentTool (cannot spawn sub-agents)

**Benefits:**
- Prevents accidental infinite sub-agent spawning
- Sub-agents focused on specific tasks
- Main agent delegates complex tasks to focused sub-agents
- Clear responsibility separation

### Visualization

Sub-agents use indentation and compact formatting:

```
Main Agent:
  🔧 Tool: Glob
  ✅ Result: ...

  🔄 Launching Sub-agent (Level 1)
    └─ Sub-agent Iteration 1
      └─ 🔧 Read (1/2)
         ✓ File contents...
      └─ 🔧 Grep (2/2)
         ✓ Matches found...
    ✓ Sub-agent L1 Complete

  🔧 Tool: Edit
  ✅ Result: ...
```

Features:
- Depth-based indentation (2 spaces per level)
- Tool progress: `(2/5)` = tool 2 of 5
- Status bar shows: `[Sub-agent L{depth}]`
- Compact output for sub-agents to reduce clutter

## Conversation History

Conversation history is maintained in `AgentState.messages`:

```python
# First command
User: "List files"
Agent: [uses Glob tool]
Agent: "I found 10 files..."

# Second command (context preserved)
User: "What's in main.py?"
Agent: [remembers which directory, reads main.py]
Agent: "The file contains..."

# Reset with Ctrl+R
[messages cleared, fresh start]
```

This enables natural multi-turn conversations where the agent remembers context.

## Shared State vs. Tool-Local State

**Shared across all commands:**
- `AgentState.messages` - Full conversation history
- `_todo_store` - Global todo list (in main.py)

**Sub-agent isolated:**
- Sub-agents get their own message context
- Don't pollute main conversation history
- Return results to parent agent

## Future Enhancements

Potential improvements with this architecture:

1. **Persistent State** - Save `AgentState` to disk/database
2. **Web Interface** - Add FastAPI + React using same `AgentRuntime`
3. **Streaming** - Stream tool results as they execute
4. **Multiple Agents** - Run multiple `AgentRuntime` instances concurrently
5. **Better Interrupts** - Cancel mid-tool-execution
6. **Replay/Debug** - Record and replay agent sessions
7. **Custom Callbacks** - Add logging, metrics, etc.

The callback architecture makes all of these straightforward to implement!

