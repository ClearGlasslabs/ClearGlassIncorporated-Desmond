#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_links():
    path = ROOT / "tools" / "internal_links.py"
    spec = importlib.util.spec_from_file_location("internal_links_final_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def links(mode: str) -> int:
    module = load_links()
    if mode == "validate":
        return 1 if module.validate() else 0
    if mode == "report":
        current = module.REPORT_PATH.read_text(encoding="utf-8")
        return 0 if current == module.build_report() else 1
    if mode == "blocks":
        for page in module.PAGES:
            text = (ROOT / page).read_text(encoding="utf-8", errors="surrogateescape")
            match = module.BLOCK_RE.search(text)
            if not match or match.group(0) != module.build_block(page):
                return 1
        return 0
    return 2


def search(target: str) -> int:
    subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)
    return subprocess.run(["git", "diff", "--quiet", "--", target], cwd=ROOT, check=False).returncode


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    kind, target = sys.argv[1:]
    if kind == "links":
        return links(target)
    if kind == "search":
        return search(target)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
