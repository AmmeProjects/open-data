import os
import runpy
import sys


def module_name_from_path(relative_path: str) -> str:
    if relative_path.endswith(".py"):
        relative_path = relative_path[:-3]
    normalized = relative_path.replace("/", ".").replace("\\", ".")
    return normalized.strip(".")


if len(sys.argv) != 2:
    print("Usage: python run_as_module.py <relative-path-to-module.py>", file=sys.stderr)
    sys.exit(1)

# Ensure the workspace root is on sys.path so package roots like src are importable.
workspace_root = os.getcwd()
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

module_name = module_name_from_path(sys.argv[1])
runpy.run_module(module_name, run_name="__main__")
