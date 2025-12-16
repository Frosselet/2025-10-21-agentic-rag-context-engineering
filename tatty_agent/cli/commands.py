"""
Initialization and utility commands for TATty Agent

This module contains commands like:
- tatty-init: Initialize project with artifact folders and BAML setup
- tatty-tui: Launch TUI mode directly
- tatty-status: Check project initialization status
"""
import argparse
import sys
import os
from pathlib import Path

from ..config import ProjectInitializer, load_config


def tatty_init():
    """Initialize a project with TATty Agent artifact folders and BAML setup"""
    parser = argparse.ArgumentParser(
        prog="tatty-init",
        description="Initialize a project with TATty Agent artifact folders and configuration"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=".",
        help="Directory to initialize (default: current directory)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check initialization status without making changes"
    )

    args = parser.parse_args()

    # Resolve the target directory
    project_dir = Path(args.dir).resolve()
    if not project_dir.exists():
        print(f"❌ Error: Directory does not exist: {project_dir}")
        sys.exit(1)

    if not project_dir.is_dir():
        print(f"❌ Error: Not a directory: {project_dir}")
        sys.exit(1)

    # Initialize the project initializer
    initializer = ProjectInitializer(project_dir)

    # Check status if requested
    if args.status:
        print(f"📁 Checking status for: {project_dir}")
        print()

        status = initializer.check_project_status()

        if status["initialized"]:
            print("✅ Project is properly initialized with TATty Agent")
        else:
            print("⚠️  Project is not fully initialized")

        print("\n📂 Artifact Folders:")
        for folder, info in status["folders"].items():
            status_icon = "✅" if info["exists"] else "❌"
            file_count = f"({info['file_count']} files)" if info["exists"] else ""
            print(f"  {status_icon} {folder}/ {file_count}")
            if not info["exists"]:
                print(f"      {info['description']}")

        print("\n📄 Configuration Files:")
        for file, info in status["files"].items():
            status_icon = "✅" if info["exists"] else "❌"
            print(f"  {status_icon} {file}")
            if not info["exists"]:
                print(f"      {info['description']}")

        if status["missing"]:
            print(f"\n⚠️  Missing items: {len(status['missing'])}")
            for item in status["missing"]:
                print(f"  - {item}")

        if status["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in status["recommendations"]:
                print(f"  - {rec}")

        return

    # Perform initialization
    print(f"🚀 Initializing TATty Agent project in: {project_dir}")
    print()

    if args.force:
        print("⚠️  Force mode: Will overwrite existing files")
        print()

    results = initializer.initialize_project(force=args.force)

    if results["success"]:
        print("✅ Project initialization completed successfully!")
        print()

        if results["created_folders"]:
            print("📂 Created folders:")
            for folder in results["created_folders"]:
                print(f"  - {folder}/")

        if results["created_files"]:
            print("📄 Created files:")
            for file in results["created_files"]:
                print(f"  - {file}")

        if results["existing_files"]:
            print("📄 Existing files (not modified):")
            for file in results["existing_files"]:
                print(f"  - {file}")

        print()
        print("🎉 Your project is ready!")
        print("Next steps:")
        print("  1. Edit .env with your API keys")
        print("  2. Run 'tatty-agent \"Hello world\"' to test")
        print("  3. Run 'tatty-tui' for the interactive interface")

    else:
        print("❌ Project initialization failed!")
        if results["errors"]:
            print("Errors:")
            for error in results["errors"]:
                print(f"  - {error}")
        sys.exit(1)


def tatty_tui():
    """Launch TUI mode directly"""
    parser = argparse.ArgumentParser(
        prog="tatty-tui",
        description="Launch TATty Agent TUI (Terminal User Interface)"
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=".",
        help="Working directory (default: current directory)"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Initial query to start with"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(working_dir=args.dir)

    print("🚀 Launching TATty Agent TUI...")

    try:
        # Import and launch TUI
        from ..tui.app import run_tui
        run_tui(working_dir=config.working_dir, initial_query=args.query)
    except ImportError as e:
        print(f"❌ Error: Could not import TUI module: {e}")
        print("TUI will be available in Phase 4")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 TUI closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running TUI: {e}")
        sys.exit(1)


def tatty_status():
    """Check project initialization status"""
    parser = argparse.ArgumentParser(
        prog="tatty-status",
        description="Check TATty Agent project status"
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=".",
        help="Directory to check (default: current directory)"
    )

    args = parser.parse_args()

    # This is essentially the same as tatty-init --status
    sys.argv = ["tatty-init", "--status", "--dir", args.dir]
    tatty_init()


def main():
    """Main entry point for command routing"""
    if len(sys.argv) < 2:
        print("TATty Agent Commands:")
        print("  tatty-init   - Initialize project")
        print("  tatty-tui    - Launch TUI interface")
        print("  tatty-status - Check project status")
        print()
        print("Run with --help for detailed usage")
        return

    command = sys.argv[1]
    # Remove the command from argv so subcommands can parse their own args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "init":
        tatty_init()
    elif command == "tui":
        tatty_tui()
    elif command == "status":
        tatty_status()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: init, tui, status")
        sys.exit(1)


if __name__ == "__main__":
    main()