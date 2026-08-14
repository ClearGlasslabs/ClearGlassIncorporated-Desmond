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


def internal(mode: str) -> int:
    module = load_internal_links()
    if mode == "validate":
        return 1 if module.validate() else 0
    if mode == "report":
        return 0 if module.REPORT_PATH.read_text(encoding="utf-8") == module.build_report() else 1
    if mode == "blocks":
        for page in module.PAGES:
            text = (ROOT / page).read_text(encoding="utf-8", errors="surrogateescape")
            match = module.BLOCK_RE.search(text)
            if not match or match.group(0) != module.build_block(page):
                return 1
        return 0
    if mode == "classification":
        discovered = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*.html")
            if not module.NON_SITE_DIRS & set(path.parts)
        }
        classified = set(module.PAGES) | set(module.EXCLUDED_PAGES) | set(module.NATIVE_JOURNEY_PAGES)
        return 0 if discovered == classified else 1
    if mode == "mapped-files":
        return 0 if all((ROOT / page).is_file() for page in module.PAGES) else 1
    if mode == "native-files":
        return 0 if all((ROOT / page).is_file() for page in module.NATIVE_JOURNEY_PAGES) else 1
    if mode == "clusters":
        clustered: set[str] = set()
        for cluster in module.CLUSTERS.values():
            for page in [cluster["pillar"], *cluster["members"]]:
                if page in clustered and page != "index.html":
                    return 1
                clustered.add(page)
                if page not in module.PAGES:
                    return 1
        return 0 if clustered == set(module.PAGES) else 1
    if mode == "extra-links":
        for source, targets in module.EXTRA_LINKS.items():
            for page in [source, *targets]:
                if page not in module.PAGES:
                    return 1
        return 0
    if mode == "overlaps":
        mapped = set(module.PAGES)
        excluded = set(module.EXCLUDED_PAGES)
        native = set(module.NATIVE_JOURNEY_PAGES)
        return 0 if not (mapped & excluded or mapped & native or excluded & native) else 1
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
