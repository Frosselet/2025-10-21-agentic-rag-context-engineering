# Performance Optimizations for BAMMY Agent

## Quick Wins (Immediate Impact)

### 1. Reduce Max Iterations
**Current**: 999 iterations
**Fix**: Change to 20-50 iterations

```python
# In tui.py:431 and main.py:716
result = await self.agent_runtime.run_loop(query, max_iterations=20, depth=0)
```

### 2. Add Web Operation Timeouts
**Current**: 30s web fetch, unlimited web search
**Fix**: Reduce to 10s max

```python
# In execute_web_fetch()
response = requests.get(tool.url, timeout=10)

# In execute_web_search()
search_results = list(ddgs.text(
    tool.query,
    max_results=5,
    timeout=10  # Add timeout
))
```

### 3. Use Faster Models for Simple Tasks
**Current**: gpt-5 for everything
**Fix**: Use gpt-5-mini or claude-haiku for non-complex tasks

```baml
// In agent.baml - switch to faster model
function AgentLoop(state: Message[], working_dir: string) -> AgentTools | ReplyToUser {
  client "openai-responses/gpt-5-mini"  // Much faster
  // ... rest unchanged
}
```

## Medium Impact Changes

### 4. Enable Parallel Tool Execution
**Problem**: "Execute ONE tool at a time" constraint
**Fix**: Allow parallel tools when safe

```baml
# In agent.baml, update guidance:
# Tool Usage
- Execute multiple independent tools in parallel when possible
- Only execute sequentially when tools depend on each other
- Web searches and file reads can run in parallel
```

### 5. Implement Async Web Operations
**Current**: Synchronous requests
**Fix**: Use aiohttp for web fetch, async search

```python
import aiohttp
import asyncio

async def execute_web_fetch_async(tool: types.WebFetchTool) -> str:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.get(tool.url) as response:
            html = await response.text()
            # ... rest of processing
```

### 6. Add Response Caching
**Problem**: Repeated web searches/fetches
**Fix**: Cache results for 5-15 minutes

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_web_search(query: str, timestamp: int) -> str:
    # timestamp ensures cache expires every 5 minutes
    return execute_web_search_impl(query)

# Use: cached_web_search(query, int(time.time() // 300))
```

## Advanced Optimizations

### 7. Smart Iteration Detection
**Problem**: Agent loops unnecessarily
**Fix**: Stop when no progress is being made

```python
# Track last N responses, stop if repeating
def is_agent_stuck(last_responses: list) -> bool:
    if len(last_responses) >= 3:
        return all(r.startswith("Tool:") for r in last_responses[-3:])
    return False
```

### 8. Streaming Responses
**Problem**: Wait for complete response
**Fix**: Stream partial results to UI

### 9. Prompt Optimization
**Problem**: Verbose prompts cause slow processing
**Fix**: Reduce system prompt length, use more focused instructions

## Expected Performance Gains

| Optimization | Expected Speedup | Effort |
|-------------|------------------|---------|
| Reduce iterations | 3-5x faster | 5 minutes |
| Web timeouts | 2-3x faster | 10 minutes |
| Faster model | 2-4x faster | 5 minutes |
| Parallel tools | 2-3x faster | 1 hour |
| Async web ops | 1.5-2x faster | 2 hours |
| Response caching | 3-5x for repeated queries | 30 minutes |

## Implementation Priority

1. **Immediate (5 minutes)**:
   - Reduce max_iterations to 20
   - Add 10s timeouts to web operations
   - Switch to gpt-5-mini

2. **Short term (1 hour)**:
   - Enable parallel tool execution in BAML prompt
   - Add basic response caching

3. **Medium term (half day)**:
   - Implement async web operations
   - Add smart iteration detection

## Testing the Fixes

```bash
# Before optimization
time uv run python main.py "Search for Python web frameworks and list top 5"

# After optimization
time uv run python main.py "Search for Python web frameworks and list top 5"

# Should see 3-5x speedup
```

---

**Bottom Line**: With just the quick wins (15 minutes of changes), you should see **3-5x faster responses**. The agent will feel much more responsive and usable.