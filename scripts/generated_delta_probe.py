#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_ROUTE = "/blog/graph-topology-multi-agent-research-workflow.html"
GRAPH_URL = "https://www.clearglassinc.com" + GRAPH_ROUTE

GROUPS = {
    "blog": lambda route: route.startswith("/blog/"),
    "offers": lambda route: route.startswith("/offers/") or route.startswith("/checkout/") or route in {"/pricing.html", "/plans.html", "/store.html"},
    "legal": lambda route: route.startswith("/legal/") or route in {"/aegis.html", "/banking-law-advisor.html", "/corporate-legal-advisor.html", "/tax.html"},
    "ops": lambda route: route.startswith("/operations/") or route.startswith("/apps/") or route.startswith("/investors/"),
    "products": lambda route: route.startswith("/products/") or route.startswith("/opal/") or route in {"/products.html", "/smb.html", "/workspace.html", "/workspace-email.html", "/workspace-migration.html", "/workspace-security.html", "/workspace-vs.html"},
    "root": lambda route: route.count("/") == 1 and not route.startswith("/blog/"),
}


def generate() -> None:
    shutil.copy2(ROOT / "sitemap.xml", "/tmp/sitemap-before.xml")
    shutil.copy2(ROOT / "data/seo/page-intents.json", "/tmp/intents-before.json")
    subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)


def sitemap_map(path: str | Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    result = {}
    for node in root.findall("s:url", ns):
        loc = node.findtext("s:loc", default="", namespaces=ns)
        lastmod = node.findtext("s:lastmod", default="", namespaces=ns)
        result[loc] = lastmod
    return result


def intent_map(path: str | Path) -> dict[str, dict]:
    return {row["route"]: row for row in json.loads(Path(path).read_text(encoding="utf-8"))}


def group_matches(route: str, group: str) -> bool:
    predicate = GROUPS[group]
    return predicate(route)


def main() -> int:
    mode = sys.argv[1]
    generate()
    if mode.startswith("sitemap-"):
        before = sitemap_map("/tmp/sitemap-before.xml")
        after = sitemap_map(ROOT / "sitemap.xml")
        if mode == "sitemap-urls":
            return 0 if set(before) == set(after) else 1
        if mode == "sitemap-lastmods":
            common = set(before) & set(after)
            return 0 if all(before[url] == after[url] for url in common) else 1
        if mode == "sitemap-graph":
            return 0 if after.get(GRAPH_URL) == "2026-08-14" else 1
        if mode == "sitemap-bytes":
            return 0 if Path("/tmp/sitemap-before.xml").read_bytes() == (ROOT / "sitemap.xml").read_bytes() else 1
        if mode.startswith("sitemap-group-"):
            group = mode.removeprefix("sitemap-group-")
            changed = {
                url.removeprefix("https://www.clearglassinc.com") or "/"
                for url in set(before) & set(after)
                if before[url] != after[url]
            }
            return 1 if any(group_matches(route, group) for route in changed) else 0
    if mode.startswith("intent-"):
        before = intent_map("/tmp/intents-before.json")
        after = intent_map(ROOT / "data/seo/page-intents.json")
        if mode == "intent-routes":
            return 0 if set(after) - set(before) == {GRAPH_ROUTE} and not (set(before) - set(after)) else 1
        if mode == "intent-existing":
            return 0 if all(before[route] == after[route] for route in before if route in after) else 1
        if mode == "intent-graph":
            expected = {
                "route": GRAPH_ROUTE,
                "intent": "Graph Topology Beats One Giant Context",
                "title": "Graph Topology Beats One Giant Context | ClearGlass Intelligence",
                "description": "A practical planner-worker-verifier workflow for multi-agent research: isolated contexts, evidence boundaries, benchmark caveats, and copy-ready prompts.",
                "canonical": GRAPH_URL,
                "h1": "Graph Topology Beats One Giant Context",
            }
            return 0 if after.get(GRAPH_ROUTE) == expected else 1
        if mode.startswith("intent-group-"):
            group = mode.removeprefix("intent-group-")
            changed = {
                route
                for route in set(before) & set(after)
                if before[route] != after[route]
            }
            added = set(after) - set(before)
            removed = set(before) - set(after)
            delta = changed | added | removed
            return 1 if any(group_matches(route, group) for route in delta) else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
