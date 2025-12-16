# BAMMY Agent TUI Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ BAMMY Agent                                                          🕐 14:30:21     │ HEADER
├─────────────────────────────────────────────────────────────────────────────────────┤
│ 📁 /path/to/project  |  🔄 Iteration: 3  |  📊 Processing...                       │ STATUS
├──────────────────────────────────────────────────────┬──────────────────────────────┤
│                                                      │                              │
│  ┌────────────────────────────────────────────────┐ │  ┌────────────────────────┐ │
│  │ 👤 User Query                                  │ │  │ 📋 Todos               │ │
│  │                                                │ │  │                        │ │
│  │ What files are in this directory?             │ │  │ ✓ Setup complete       │ │
│  └────────────────────────────────────────────────┘ │  │ → Processing files     │ │
│                                                      │  │ ○ Generate report      │ │
│  ══════════════════════════════════════════════════ │  └────────────────────────┘ │
│  Iteration 1                                         │                              │
│  ══════════════════════════════════════════════════ │                              │
│                                                      │                              │
│  ┌────────────────────────────────────────────────┐ │                              │
│  │ 🔧 Tool: LS                                    │ │                              │
│  │                                                │ │                              │
│  │ path: /path/to/project                        │ │                              │
│  └────────────────────────────────────────────────┘ │                              │
│                                                      │                              │ MAIN
│  ┌────────────────────────────────────────────────┐ │                              │ AREA
│  │ ✅ Result                                       │ │                              │
│  │                                                │ │                              │
│  │ DIR  src                                       │ │                              │
│  │ DIR  tests                                     │ │                              │
│  │ FILE main.py                                   │ │                              │
│  │ FILE README.md                                 │ │                              │
│  └────────────────────────────────────────────────┘ │                              │
│                                                      │                              │
│  ══════════════════════════════════════════════════ │                              │
│  Iteration 2                                         │                              │
│  ══════════════════════════════════════════════════ │                              │
│                                                      │                              │
│  ┌────────────────────────────────────────────────┐ │                              │
│  │ 🤖 Agent Reply                                  │ │                              │
│  │                                                │ │                              │
│  │ I found 2 directories (src, tests) and 2      │ │                              │
│  │ files (main.py, README.md) in the current     │ │                              │
│  │ directory.                                     │ │                              │
│  └────────────────────────────────────────────────┘ │                              │
│                                                      │                              │
├──────────────────────────────────────────────────────┴──────────────────────────────┤
│ Enter your command... (Ctrl+C to exit)                                              │ INPUT
│ █                                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ ^C Quit  ^R Reset Chat  ^X Interrupt                                               │ FOOTER
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Color Scheme

- **Blue panels**: User queries
- **Magenta panels**: Tool executions
- **Green panels**: Results and agent replies
- **Yellow text**: Status indicators (iterations, in-progress todos)
- **Cyan**: Headers and working directory
- **Red panels**: Errors
- **Dim/Gray**: Separator lines and completed todos

## Features

### Status Bar (Top)
- 📁 Current working directory
- 🔄 Current iteration number
- 📊 Agent status (Ready, Processing, Thinking, Executing...)

### Main Log Area (Left, 3/4 width)
- Scrollable content area
- Pretty-formatted panels for:
  - User queries (blue)
  - Tool calls with parameters (magenta)
  - Tool results (green)
  - Agent replies (green)
  - Errors (red)
- Automatic scrolling to latest content
- Line wrapping for long content

### Todo Panel (Right, 1/4 width)
- Live updates as agent modifies todos
- Status icons: ✓ (completed), → (in progress), ○ (pending)
- Color-coded by status
- Shows first 10 todos + count of additional
- Auto-refreshes after each tool execution

### Input Box (Bottom)
- Always visible at bottom
- Placeholder text: "Enter your command... (Ctrl+C to exit)"
- Submit with Enter key
- Auto-clears after submission
- Auto-focuses after command completion

### Keyboard Shortcuts
- **Enter**: Submit command
- **Ctrl+R**: Reset conversation history (start fresh)
- **Ctrl+X**: Interrupt agent execution (graceful stop at next checkpoint)
- **Ctrl+C**: Exit application
- **Scroll**: Mouse wheel or arrow keys in log area

### Conversation History
- The agent maintains full conversation context across multiple commands
- This allows you to have natural multi-turn conversations
- Example: "List files" → "What's in main.py?" (agent remembers the context)
- Press Ctrl+R to clear history and start fresh if needed

## Implementation Details

Built with:
- `textual` - Modern TUI framework
- `rich` - Beautiful terminal formatting
- `asyncio` for non-blocking UI updates
- BAML async client for non-blocking agent calls
- CSS-like styling for layout

### Technical Features
- **Async BAML Client**: Uses `baml_client.async_client` for fully async, non-blocking agent execution
- **Interrupt Support**: The agent checks `interrupt_requested` flag at multiple checkpoints
- **Real-time Updates**: UI refreshes after each tool execution with `await asyncio.sleep(0.01)`
- **Conversation Persistence**: Full message history maintained in `self.messages` across commands
- **Graceful Shutdown**: Ctrl+C now works properly since the UI thread is never blocked
- **Sub-agent Visualization**: Nested agents shown with indentation and depth indicators
  - Each level indented by 2 spaces
  - Status bar shows `[Sub-agent L{depth}]` 
  - Tool progress indicators: `(2/5)` = tool 2 of 5
  - Compact output format for sub-agents
  - Recursive depth tracking with `parent_depth` parameter

The TUI maintains the same agent loop as CLI mode but with non-blocking execution and real-time visual feedback.

