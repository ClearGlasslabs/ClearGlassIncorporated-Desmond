#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
INTENTS = ROOT / "data/seo/page-intents.json"
GRAPH = "/blog/graph-topology-multi-agent-research-workflow.html"


def sitemap_rows(raw: str) -> list[tuple[str, str]]:
    root = ET.fromstring(raw)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [
        (
            node.findtext("s:loc", default="", namespaces=ns),
            node.findtext("s:lastmod", default="", namespaces=ns),
        )
        for node in root.findall("s:url", ns)
    ]


def intent_doc(raw: str) -> dict:
    return json.loads(raw)


def main() -> int:
    mode = sys.argv[1]
    before_sitemap_raw = SITEMAP.read_text(encoding="utf-8")
    before_intents_raw = INTENTS.read_text(encoding="utf-8")
    subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)
    after_sitemap_raw = SITEMAP.read_text(encoding="utf-8")
    after_intents_raw = INTENTS.read_text(encoding="utf-8")

    before_sitemap = sitemap_rows(before_sitemap_raw)
    after_sitemap = sitemap_rows(after_sitemap_raw)
    before_map = dict(before_sitemap)
    after_map = dict(after_sitemap)

    before_doc = intent_doc(before_intents_raw)
    after_doc = intent_doc(after_intents_raw)
    before_pages = {row["route"]: row for row in before_doc["pages"]}
    after_pages = {row["route"]: row for row in after_doc["pages"]}

    if mode == "sitemap-urls":
        return 0 if set(before_map) == set(after_map) else 1
    if mode == "sitemap-lastmods":
        return 0 if before_map == after_map else 1
    if mode == "sitemap-order":
        return 0 if [u for u, _ in before_sitemap] == [u for u, _ in after_sitemap] else 1
    if mode == "sitemap-bytes":
        return 0 if before_sitemap_raw == after_sitemap_raw else 1
    if mode == "intent-header":
        return 0 if {k: before_doc[k] for k in ("site", "generated_from")} == {k: after_doc[k] for k in ("site", "generated_from")} else 1
    if mode == "intent-routes":
        return 0 if set(before_pages) == set(after_pages) else 1
    if mode == "intent-records":
        return 0 if before_pages == after_pages else 1
    if mode == "intent-order":
        return 0 if [r["route"] for r in before_doc["pages"]] == [r["route"] for r in after_doc["pages"]] else 1
    if mode == "intent-graph":
        return 0 if before_pages.get(GRAPH) == after_pages.get(GRAPH) else 1
    if mode == "intent-bytes":
        return 0 if before_intents_raw == after_intents_raw else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
