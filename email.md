Hello First Name,

This week's 🦄 ai that works session was all about Agentic RAG.

The full recording is now on [YouTube](https://www.youtube.com/watch?v=grGSFfyejA0), and all the code is available on [GitHub](https://github.com/ai-that-works/ai-that-works/tree/main/2025-10-21-agentic-rag-context-engineering).

We started with a hot take: Most people shouldn't build agentic RAG systems. Then we proceed to build one from scratch to show exactly why—and when—you actually might want one.

**What we learned building a coding agent in 3 hours:**

1. **The agent loop is the easy part** (30 minutes). The hard part? Tool implementation details that make or break your system. e.g. using relative paths instead of absolute paths in grep results alone can save thousands of tokens.

2. **UI matters more than the agent logic**. We spent more time building a good debugging TUI (Terminal UI) than on the actual agent loop. Without proper visibility into tool sequences and iterations, you're flying blind.

3. **Small optimizations compound dramatically**. Save 20 tokens per grep call × 30 calls = 600 tokens saved. In a system making hundreds of tool calls, every character counts. This is a massive accuracy win (and also cost, but more importantly accuracy).

4. **Traditional RAG vs Agentic RAG is about control**. Traditional RAG: Your code decides what context to fetch every time. Agentic RAG: The model decides if it needs context at all. One is fast and predictable, the other is flexible but slow.

5. **Build from first principles to truly understand**. Using frameworks seems fasts, but writing the code yourself reveals where complexity actually lives and what optimizations actually matter. Its not that hard. Go build your own agent.

**The implementation details:**
- Use ripgrep (rg) instead of standard grep
- Track and inject the working directory into prompts
- Add clear truncation notices with line numbers (e.g. "truncated, lines 30-500 omitted")
- Render tools in simplified format, not full JSON
- Use `[Dir]` and `[File]` prefixes in ls output

**If you remember one thing from this session:**

Agentic RAG isn't technically hard—you can build one in 3 hours. The hard part is deciding if you actually need one. As we discovered: "Most problems are not so wide that you need an agentic rag system." Start with deterministic RAG. Only go agentic when your problem space is truly unbounded and flexibility matters more than speed.

**Next Session: Ralph Wiggum under the hood - Coding Agent Power Tools (Oct 28th)**

We've talked a lot about context engineering for coding agents. Next week, we're diving deep on the Ralph Wiggum Technique and why this totally different approach can change how you code. We'll explore using ralph for greenfield projects, refactoring, and generating specifications. Surprise surprise, the answer is better context engineering.

Sign up here: https://lu.ma/ralphloop

If you have questions about this episode, reply to this email or ask on [Discord](https://boundaryml.com/discord). We read everything!

Happy coding 🧑‍💻

Vaibhav & Dex