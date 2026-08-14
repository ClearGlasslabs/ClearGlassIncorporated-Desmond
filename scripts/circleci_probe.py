#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_internal_links():
    path = ROOT / "tools" / "internal_links.py"
    spec = importlib.util.spec_from_file_location("internal_links_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory(module):
    discovered = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*.html")
        if not module.NON_SITE_DIRS & set(path.parts)
    }
    classified = set(module.PAGES) | set(module.EXCLUDED_PAGES) | set(module.NATIVE_JOURNEY_PAGES)
    return discovered, classified


def internal(mode: str) -> int:
    module = load_internal_links()
    discovered, classified = inventory(module)
    unknown = discovered - classified
    missing = classified - discovered

    if mode.startswith("unknown-prefix-"):
        prefix = mode.removeprefix("unknown-prefix-").lower()
        return 1 if any("/" not in page and page.lower().startswith(prefix) for page in unknown) else 0
    if mode == "unknown-da-s-z":
        return 1 if any("/" not in page and page.lower().startswith("da") and len(page) > 2 and page[2].lower() in "stuvwxyz" for page in unknown) else 0
    if mode == "missing-da-s-z":
        return 1 if any("/" not in page and page.lower().startswith("da") and len(page) > 2 and page[2].lower() in "stuvwxyz" for page in missing) else 0
    if mode == "unknown-da-other":
        return 1 if any("/" not in page and page.lower().startswith("da") and (len(page) < 3 or not page[2].isalpha()) for page in unknown) else 0
    if mode == "missing-da-other":
        return 1 if any("/" not in page and page.lower().startswith("da") and (len(page) < 3 or not page[2].isalpha()) for page in missing) else 0
    if mode == "validate":
        return 1 if module.validate() else 0
    if mode == "classification":
        return 0 if discovered == classified else 1
    if mode == "report":
        return 0 if module.REPORT_PATH.read_text(encoding="utf-8") == module.build_report() else 1
    if mode == "blocks":
        for page in module.PAGES:
            text = (ROOT / page).read_text(encoding="utf-8", errors="surrogateescape")
            match = module.BLOCK_RE.search(text)
            if not match or match.group(0) != module.build_block(page):
                return 1
        return 0
    raise ValueError(mode)


def search_asset(target: str) -> int:
    subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)
    return subprocess.run(["git", "diff", "--quiet", "--", target], cwd=ROOT, check=False).returncode


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    kind, target = sys.argv[1:]
    if kind == "internal":
        return internal(target)
    if kind == "search":
        return search_asset(target)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
