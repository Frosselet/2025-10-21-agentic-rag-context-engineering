"""
CLI entry point for TATty Agent

This module provides the command-line interface, extracted from the original
main.py file to maintain backward compatibility while enabling the package
structure.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from ..core.runtime import AgentRuntime
from ..core.state import AgentState, AgentCallbacks


class CLICallbacks(AgentCallbacks):
    """CLI-specific callbacks for agent execution"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        super().__init__()

    async def on_iteration(self, iteration: int, depth: int):
        """Handle iteration updates"""
        if self.verbose:
            indent = "  " * depth
            print(f"{indent}🔄 Iteration {iteration} (depth {depth})")

    async def on_tool_start(self, tool_name: str, params: dict, tool_idx: int, total_tools: int, depth: int):
        """Handle tool execution start"""
        indent = "  " * depth
        print(f"{indent}🛠️  Executing {tool_name}...")
        if self.verbose and params:
            for key, value in params.items():
                if value is not None:
                    print(f"{indent}   {key}: {value}")

    async def on_tool_result(self, result: str, depth: int):
        """Handle tool execution result"""
        indent = "  " * depth
        print(f"{indent}✅ Tool completed")
        if self.verbose and result:
            # Truncate long results in verbose mode
            display_result = result[:200] + "..." if len(result) > 200 else result
            print(f"{indent}📄 Result: {display_result}")

    async def on_agent_reply(self, message: str):
        """Handle agent reply to user"""
        print(f"🤖 Agent: {message}")

    async def on_status_update(self, status: str, iteration: int):
        """Handle status updates"""
        if self.verbose:
            print(f"📊 Status: {status} (iteration {iteration})")


async def agent_loop(user_message: str, max_iterations: int = 20, working_dir: str = ".", verbose: bool = False) -> str:
    """Run the agent loop with CLI callbacks"""
    state = AgentState(working_dir=working_dir)
    callbacks = CLICallbacks(verbose=verbose)
    runtime = AgentRuntime(state, callbacks)

    return await runtime.run_loop(user_message, max_iterations)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TATty Agent - Agentic RAG Context Engineering Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single command
  tatty-agent "What files are in this directory?"

  # Interactive mode - keeps asking for commands
  tatty-agent --interactive
  tatty-agent "Start" --interactive  # conventional way to start interactive mode

  # TUI mode - beautiful text interface (no initial query needed)
  tatty-agent --tui
  tatty-agent "Start" --tui  # conventional way to start TUI

  # TUI mode with initial query
  tatty-agent "List files" --tui

  # Specify a working directory
  tatty-agent "Find all Python files" --dir /path/to/project
        """
    )

    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default=None,
        help="The query or task for the agent to perform (optional in TUI mode)"
    )

    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Working directory for the agent (defaults to current directory)"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode (keep asking for commands)"
    )

    parser.add_argument(
        "--tui",
        "-t",
        action="store_true",
        help="Run in TUI mode (beautiful text user interface)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Launch TUI mode if requested
    if args.tui:
        from ..tui.app import run_tui

        work_dir = None
        if args.dir:
            work_dir = Path(args.dir).resolve()
            if not work_dir.exists():
                print(f"❌ Error: Directory does not exist: {work_dir}")
                sys.exit(1)
            if not work_dir.is_dir():
                print(f"❌ Error: Not a directory: {work_dir}")
                sys.exit(1)
            work_dir = str(work_dir)

        run_tui(working_dir=work_dir, initial_query=args.query)
        return

    # Set working directory for CLI mode
    if args.dir:
        work_dir = str(Path(args.dir).resolve())
        work_dir_path = Path(work_dir)
        if not work_dir_path.exists():
            print(f"❌ Error: Directory does not exist: {work_dir}")
            sys.exit(1)
        if not work_dir_path.is_dir():
            print(f"❌ Error: Not a directory: {work_dir}")
            sys.exit(1)

        os.chdir(work_dir)
        print(f"📁 Working directory: {work_dir}")
    else:
        work_dir = os.getcwd()
        print(f"📁 Working directory: {work_dir}")

    # Require query in non-interactive/non-TUI mode
    if not args.query and not args.interactive:
        parser.error("query is required unless using --interactive mode")

    # Print header
    print("🤖 TATty Agent - Agentic RAG Context Engineering Demo")
    print("=" * 60)

    # Interactive loop or single command
    first_query = args.query

    while True:
        try:
            if first_query:
                query = first_query
                first_query = None  # Only use the first query once
            else:
                print("\n" + "=" * 60)
                query = input("📝 Enter your command (or 'exit' to quit): ").strip()

                if not query:
                    continue

                if query.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break

            # Skip generic startup commands that don't provide meaningful tasks
            if query.strip().lower() in ["start", "begin", "go"]:
                print(f"\n📝 Query: {query}")
                print("🚀 TATty Agent ready! Please enter a specific command or task.")
                print("💡 Examples: 'List files', 'Search for Python functions', 'Explain this code'")
                if not args.interactive:
                    break  # In non-interactive mode, exit after showing help
                continue  # In interactive mode, ask for another command

            print(f"\n📝 Query: {query}")
            print("🔄 Running agent...")
            print("=" * 60)

            # Run the agent
            result = asyncio.run(agent_loop(query, max_iterations=20, working_dir=work_dir, verbose=args.verbose))

            print(f"\n{'='*60}")
            print(f"✅ Final result:\n{result}")
            print(f"{'='*60}")

            # If not in interactive mode, exit after first query
            if not args.interactive:
                break

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            if args.interactive:
                continue  # Go back to prompt
            else:
                sys.exit(130)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            if not args.interactive:
                sys.exit(1)
            # In interactive mode, continue to next query


def cli_main():
    """Entry point for the tatty-agent command-line script"""
    # Load .env file with override=True to override shell environment variables
    load_dotenv(override=True)

    # Print loaded keys for verification
    openai_key = os.getenv("OPENAI_API_KEY")
    boundary_key = os.getenv("BOUNDARY_API_KEY")

    print(f"🔑 OpenAI API Key loaded: {openai_key[-6:] if openai_key else 'Not found'}")
    print(f"🔑 Boundary API Key loaded: {boundary_key[-6:] if boundary_key else 'Not found'}")

    main()


if __name__ == "__main__":
    cli_main()