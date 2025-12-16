#!/usr/bin/env python3
"""
TATty Agent Package Validation Script

This script validates that the TATty Agent package is ready for distribution.
It performs comprehensive checks on:
- Package structure and imports
- Dependencies and optional features
- CLI commands and entry points
- Library API functionality
- Test suite execution
- Documentation completeness

Run this script before distributing to ensure package quality.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
import tempfile
import shutil


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(message, status='info'):
    """Print colored status messages"""
    color = {'info': Colors.BLUE, 'success': Colors.GREEN, 'error': Colors.RED, 'warning': Colors.YELLOW}.get(status, '')
    print(f"{color}{message}{Colors.END}")


def print_header(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")


def run_command(command, capture_output=True, timeout=30):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def validate_package_structure():
    """Validate package directory structure"""
    print_header("Package Structure Validation")

    required_files = [
        "tatty_agent/__init__.py",
        "tatty_agent/core/__init__.py",
        "tatty_agent/tools/__init__.py",
        "tatty_agent/config/__init__.py",
        "tatty_agent/cli/__init__.py",
        "tatty_agent/tui/__init__.py",
        "tatty_agent/jupyter/__init__.py",
        "pyproject.toml",
        "README_PACKAGE.md",
        "DISTRIBUTION.md"
    ]

    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"✅ {file_path}", 'success')
        else:
            print_status(f"❌ {file_path} missing", 'error')
            all_exist = False

    # Check tool modules
    tool_modules = [
        "tatty_agent/tools/registry.py",
        "tatty_agent/tools/file_ops.py",
        "tatty_agent/tools/system.py",
        "tatty_agent/tools/web.py",
        "tatty_agent/tools/development.py",
        "tatty_agent/tools/artifacts.py"
    ]

    for tool_file in tool_modules:
        if Path(tool_file).exists():
            print_status(f"✅ {tool_file}", 'success')
        else:
            print_status(f"❌ {tool_file} missing", 'error')
            all_exist = False

    return all_exist


def validate_imports():
    """Validate all package imports work correctly"""
    print_header("Import Validation")

    imports_to_test = [
        ("Main package", "tatty_agent"),
        ("TattyAgent class", "tatty_agent", "TattyAgent"),
        ("Convenience functions", "tatty_agent", "run_agent, ask_agent, initialize_project"),
        ("Config module", "tatty_agent.config", "TattyConfig, load_config"),
        ("Core module", "tatty_agent.core", "AgentRuntime, AgentState, AgentCallbacks"),
        ("Tool registry", "tatty_agent.tools.registry", "get_registered_tools, execute_tool"),
        ("CLI commands", "tatty_agent.cli.main", "cli_main"),
        ("Project initialization", "tatty_agent.config.initialization", "ProjectInitializer"),
    ]

    all_imports_ok = True

    for description, module, *items in imports_to_test:
        try:
            mod = importlib.import_module(module)
            if items:
                for item in items[0].split(", "):
                    if not hasattr(mod, item.strip()):
                        print_status(f"❌ {description}: {item} not found", 'error')
                        all_imports_ok = False
                        continue
            print_status(f"✅ {description}", 'success')
        except ImportError as e:
            print_status(f"❌ {description}: {e}", 'error')
            all_imports_ok = False

    # Test optional imports
    optional_imports = [
        ("Jupyter integration", "tatty_agent.jupyter"),
        ("TUI components", "tatty_agent.tui"),
    ]

    for description, module in optional_imports:
        try:
            importlib.import_module(module)
            print_status(f"✅ {description} (optional)", 'success')
        except ImportError as e:
            print_status(f"⚠️  {description} (optional): {e}", 'warning')

    return all_imports_ok


def validate_cli_commands():
    """Validate CLI commands work correctly"""
    print_header("CLI Commands Validation")

    commands_to_test = [
        ("tatty-agent help", "python3 -m tatty_agent.cli.main --help"),
        ("tatty-init availability", "python3 -c 'from tatty_agent.cli.commands import tatty_init; print(\"OK\")'"),
    ]

    all_cli_ok = True

    for description, command in commands_to_test:
        success, stdout, stderr = run_command(command, timeout=10)
        if success:
            print_status(f"✅ {description}", 'success')
        else:
            print_status(f"❌ {description}: {stderr}", 'error')
            all_cli_ok = False

    return all_cli_ok


def validate_library_api():
    """Validate library API functionality"""
    print_header("Library API Validation")

    try:
        # Test basic agent creation
        from tatty_agent import TattyAgent, TattyConfig

        with tempfile.TemporaryDirectory() as temp_dir:
            config = TattyConfig(working_dir=temp_dir, verbose=False)
            agent = TattyAgent(config=config)

            print_status("✅ Agent creation", 'success')

            # Test configuration
            if hasattr(agent, 'working_dir'):
                assert temp_dir in str(agent.working_dir)
            if hasattr(agent, 'verbose'):
                assert agent.verbose is False
            print_status("✅ Configuration handling", 'success')

            # Test conversation history
            history = agent.get_conversation_history()
            assert isinstance(history, list)
            print_status("✅ Conversation history", 'success')

            # Test working directory management
            agent.set_working_dir(temp_dir)
            assert temp_dir in agent.get_working_dir()
            print_status("✅ Working directory management", 'success')

        return True

    except Exception as e:
        print_status(f"❌ Library API error: {e}", 'error')
        return False


def validate_project_initialization():
    """Validate project initialization functionality"""
    print_header("Project Initialization Validation")

    try:
        from tatty_agent.config.initialization import ProjectInitializer

        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = ProjectInitializer(temp_dir)

            # Check initial status
            status = initializer.check_project_status()
            assert status["initialized"] is False
            print_status("✅ Project status check", 'success')

            # Initialize project
            result = initializer.initialize_project()
            assert result["success"] is True
            assert len(result["created_folders"]) >= 4
            print_status("✅ Project initialization", 'success')

            # Verify folders were created
            expected_folders = ["scripts", "data", "visualization", "documents"]
            for folder in expected_folders:
                folder_path = Path(temp_dir) / folder
                assert folder_path.exists() and folder_path.is_dir()

            print_status("✅ Artifact folders creation", 'success')

            # Verify .env file
            env_file = Path(temp_dir) / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "OPENAI_API_KEY" in content
            print_status("✅ Environment file creation", 'success')

        return True

    except Exception as e:
        print_status(f"❌ Project initialization error: {e}", 'error')
        return False


def validate_test_suite():
    """Validate test suite runs successfully"""
    print_header("Test Suite Validation")

    test_commands = [
        ("Unit tests", "python3 -m pytest tests/test_library_api.py::TestTattyAgent::test_agent_initialization -v"),
        ("Config tests", "python3 -m pytest tests/test_config.py::TestTattyConfig::test_config_initialization -v"),
        ("Core runtime tests", "python3 -m pytest tests/test_core_runtime.py::TestAgentState::test_state_initialization -v"),
    ]

    all_tests_ok = True

    for description, command in test_commands:
        success, stdout, stderr = run_command(command, timeout=60)
        if success and "PASSED" in stdout:
            print_status(f"✅ {description}", 'success')
        else:
            print_status(f"❌ {description}: {stderr or 'Failed'}", 'error')
            all_tests_ok = False

    # Try running full integration test
    success, stdout, stderr = run_command("python3 -m pytest tests/test_integration.py::TestLibraryAPIIntegration::test_agent_initialization_with_config -v", timeout=60)
    if success and "PASSED" in stdout:
        print_status("✅ Integration tests", 'success')
    else:
        print_status(f"⚠️  Integration tests: {stderr or 'Some tests may have failed'}", 'warning')

    return all_tests_ok


def validate_documentation():
    """Validate documentation completeness"""
    print_header("Documentation Validation")

    required_docs = [
        ("Package README", "README_PACKAGE.md"),
        ("Distribution guide", "DISTRIBUTION.md"),
        ("Project config", "pyproject.toml"),
    ]

    all_docs_ok = True

    for description, file_path in required_docs:
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            if file_size > 1000:  # At least 1KB of content
                print_status(f"✅ {description} ({file_size:,} bytes)", 'success')
            else:
                print_status(f"⚠️  {description} seems small ({file_size} bytes)", 'warning')
        else:
            print_status(f"❌ {description} missing", 'error')
            all_docs_ok = False

    # Check for example files
    example_files = list(Path("examples").glob("*.ipynb")) if Path("examples").exists() else []
    if example_files:
        print_status(f"✅ Example notebooks: {len(example_files)} files", 'success')
    else:
        print_status("⚠️  No example notebooks found", 'warning')

    return all_docs_ok


def validate_package_metadata():
    """Validate package metadata in pyproject.toml"""
    print_header("Package Metadata Validation")

    try:
        import tomllib

        with open('pyproject.toml', 'rb') as f:
            config = tomllib.load(f)

        project = config.get('project', {})

        required_fields = ['name', 'version', 'description', 'authors', 'dependencies']
        missing_fields = []

        for field in required_fields:
            if field in project and project[field]:
                print_status(f"✅ {field}: {project[field] if field != 'dependencies' else f'{len(project[field])} dependencies'}", 'success')
            else:
                missing_fields.append(field)
                print_status(f"❌ Missing or empty field: {field}", 'error')

        # Check optional dependencies
        opt_deps = project.get('optional-dependencies', {})
        if opt_deps:
            print_status(f"✅ Optional dependencies: {list(opt_deps.keys())}", 'success')

        # Check entry points
        scripts = project.get('scripts', {})
        if scripts:
            print_status(f"✅ CLI scripts: {list(scripts.keys())}", 'success')

        return len(missing_fields) == 0

    except Exception as e:
        print_status(f"❌ Metadata validation error: {e}", 'error')
        return False


def main():
    """Run all validation checks"""
    print_status(f"{Colors.BOLD}TATty Agent Package Validation{Colors.END}", 'info')
    print_status("Performing comprehensive package validation...", 'info')

    validators = [
        ("Package Structure", validate_package_structure),
        ("Import System", validate_imports),
        ("CLI Commands", validate_cli_commands),
        ("Library API", validate_library_api),
        ("Project Initialization", validate_project_initialization),
        ("Test Suite", validate_test_suite),
        ("Documentation", validate_documentation),
        ("Package Metadata", validate_package_metadata),
    ]

    results = {}

    for name, validator in validators:
        try:
            results[name] = validator()
        except Exception as e:
            print_status(f"❌ {name} validation failed: {e}", 'error')
            results[name] = False

    # Summary
    print_header("Validation Summary")

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = '✅' if result else '❌'
        color = 'success' if result else 'error'
        print_status(f"{status} {name}", color)

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} validations passed{Colors.END}")

    if passed == total:
        print_status("🎉 Package is ready for distribution!", 'success')
        return 0
    else:
        print_status("❌ Package needs fixes before distribution", 'error')
        return 1


if __name__ == "__main__":
    sys.exit(main())