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


def root_partition(mode: str, pages: set[str]) -> int:
    roots = {page for page in pages if "/" not in page}
    if mode.startswith("classification-root-prefix-"):
        prefix = mode.removeprefix("classification-root-prefix-").lower()
        return 1 if any(page.lower().startswith(prefix) for page in roots) else 0
    if mode.startswith("classification-root-second-"):
        letters = mode.removeprefix("classification-root-second-")
        return 1 if any(page[:1].lower() == "d" and len(page) > 1 and page[1].lower() in letters for page in roots) else 0
    if mode == "classification-root-second-other":
        return 1 if any(page[:1].lower() == "d" and (len(page) < 2 or not page[1].lower().isalpha()) for page in roots) else 0
    if mode.startswith("classification-root-letter-"):
        letters = mode.removeprefix("classification-root-letter-")
        return 1 if any(page[:1].lower() in letters for page in roots) else 0
    ranges = {
        "classification-root-a-f": "abcdef",
        "classification-root-g-l": "ghijkl",
        "classification-root-m-r": "mnopqr",
        "classification-root-s-z": "stuvwxyz",
    }
    if mode == "classification-root-other":
        return 1 if any(not page[:1].lower().isalpha() for page in roots) else 0
    return 1 if any(page[:1].lower() in ranges[mode] for page in roots) else 0


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
    if mode.startswith("classification"):
        discovered, classified = inventory(module)
        delta = (discovered - classified) | (classified - discovered)
        if mode == "classification":
            return 0 if not delta else 1
        if mode == "classification-blog":
            return 1 if any(page.startswith("blog/") for page in delta) else 0
        if mode == "classification-root":
            return 1 if any("/" not in page for page in delta) else 0
        if mode == "classification-nested":
            return 1 if any("/" in page and not page.startswith("blog/") for page in delta) else 0
        if mode.startswith("classification-root-"):
            return root_partition(mode, delta)
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
