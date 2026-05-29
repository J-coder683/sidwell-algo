import os
import ast
from pathlib import Path

def test_engine_purity_no_inference_imports():
    """
    CI GUARD: The deterministic engine (sidwell/engine/) must never import
    any inference or network libraries (google.generativeai, openai, anthropic, requests, etc).
    This test statically analyzes the AST of all Python files in sidwell/engine/.
    """
    banned_imports = {
        "google.generativeai",
        "google.genai",
        "anthropic",
        "openai",
        "boto3",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "selenium",
        "playwright",
        "bs4",
        "pdfplumber",
        "PyPDF2"
    }

    engine_dir = Path(__file__).parent.parent / "sidwell" / "engine"
    if not engine_dir.exists():
        return # Engine not built yet

    violations = []

    for py_file in engine_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    for banned in banned_imports:
                        if name.name == banned or name.name.startswith(banned + "."):
                            violations.append(f"{py_file.name}: import {name.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for banned in banned_imports:
                        if node.module == banned or node.module.startswith(banned + "."):
                            violations.append(f"{py_file.name}: from {node.module} import ...")

    assert not violations, f"CRITICAL: Inference/Network imports found in deterministic engine!\n" + "\n".join(violations)
