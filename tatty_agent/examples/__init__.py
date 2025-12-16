"""
TATty Agent Examples

This module contains example notebooks and usage patterns for TATty Agent.
After installation, you can access examples programmatically:

```python
from tatty_agent.examples import get_example_notebook, list_examples

# List available examples
examples = list_examples()
print(examples)

# Get path to specific example
notebook_path = get_example_notebook("jupyter_demo")
```

## Available Examples

- **hello_world.ipynb**: Quick 5-minute introduction 🚀
  - Basic agent usage and magic commands
  - Data analysis example
  - Perfect for getting started

- **tatty_agent_jupyter_demo.ipynb**: Comprehensive feature showcase 🎯
  - Interactive chat widget usage
  - Advanced magic commands (%tatty, %%tatty)
  - Live tool execution with progress tracking
  - Notebook variable access and manipulation
  - Rich display formatting examples

## Usage in Jupyter

```python
import tatty_agent.examples
tatty_agent.examples.show_jupyter_demo()
```
"""

import os
from pathlib import Path
from typing import List, Optional

def get_examples_dir() -> Path:
    """Get the examples directory path"""
    return Path(__file__).parent

def list_examples() -> List[str]:
    """List all available example files"""
    examples_dir = get_examples_dir()
    examples = []

    for file in examples_dir.glob("*.ipynb"):
        examples.append(file.stem)

    for file in examples_dir.glob("*.py"):
        if file.name != "__init__.py":
            examples.append(file.stem)

    return sorted(examples)

def get_example_notebook(name: str) -> Optional[Path]:
    """
    Get path to a specific example notebook.

    Args:
        name: Name of the example (without extension)

    Returns:
        Path to the example file, or None if not found
    """
    examples_dir = get_examples_dir()

    # Try .ipynb first
    notebook_path = examples_dir / f"{name}.ipynb"
    if notebook_path.exists():
        return notebook_path

    # Try .py
    py_path = examples_dir / f"{name}.py"
    if py_path.exists():
        return py_path

    return None

def show_hello_world():
    """Display information about the Hello World notebook"""
    hello_path = get_example_notebook("hello_world")

    if hello_path:
        print(f"🚀 TATty Agent Hello World")
        print(f"📍 Location: {hello_path}")
        print()
        print("Perfect for getting started! This 5-minute intro covers:")
        print("✅ Basic agent usage")
        print("✅ Magic commands (%tatty)")
        print("✅ Data analysis example")
        print("✅ Project understanding")
        print()
        print("Quick start:")
        print("  jupyter lab")
        print("  # Open hello_world.ipynb and run all cells")

        return str(hello_path)
    else:
        print("❌ Hello World notebook not found")
        return None

def show_jupyter_demo():
    """Display information about the comprehensive Jupyter demo notebook"""
    demo_path = get_example_notebook("tatty_agent_jupyter_demo")

    if demo_path:
        print(f"🎯 TATty Agent Comprehensive Demo")
        print(f"📍 Location: {demo_path}")
        print()
        print("Advanced features demonstration:")
        print("✅ Interactive chat widgets")
        print("✅ Live tool execution tracking")
        print("✅ Rich display formatting")
        print("✅ Notebook variable manipulation")
        print()
        print("After you've tried hello_world.ipynb!")

        return str(demo_path)
    else:
        print("❌ Jupyter demo notebook not found")
        return None

def copy_example(name: str, destination: str = ".") -> Optional[Path]:
    """
    Copy an example to a destination directory.

    Args:
        name: Name of the example to copy
        destination: Destination directory (default: current directory)

    Returns:
        Path to the copied file, or None if source not found
    """
    import shutil

    source = get_example_notebook(name)
    if not source:
        print(f"❌ Example '{name}' not found")
        return None

    dest_dir = Path(destination)
    dest_dir.mkdir(exist_ok=True)

    dest_path = dest_dir / source.name
    shutil.copy2(source, dest_path)

    print(f"✅ Copied {source.name} to {dest_path}")
    return dest_path

__all__ = [
    'get_examples_dir',
    'list_examples',
    'get_example_notebook',
    'show_hello_world',
    'show_jupyter_demo',
    'copy_example'
]