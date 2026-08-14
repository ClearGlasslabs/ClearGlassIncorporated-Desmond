#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = "/blog/graph-topology-multi-agent-research-workflow.html"

shutil.copy2(ROOT / "data/seo/page-intents.json", "/tmp/intents-before.json")
subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)

before_doc = json.loads(Path("/tmp/intents-before.json").read_text(encoding="utf-8"))
after_doc = json.loads((ROOT / "data/seo/page-intents.json").read_text(encoding="utf-8"))
before = {row["route"]: row for row in before_doc["pages"]}
after = {row["route"]: row for row in after_doc["pages"]}
mode = sys.argv[1]

if mode == "headers":
    raise SystemExit(0 if before_doc["site"] == after_doc["site"] and before_doc["generated_from"] == after_doc["generated_from"] else 1)
if mode == "routes":
    raise SystemExit(0 if set(after) - set(before) == {GRAPH} and not (set(before) - set(after)) else 1)
if mode == "existing":
    raise SystemExit(0 if all(before[route] == after[route] for route in before) else 1)
if mode == "graph":
    expected = {
        "route": GRAPH,
        "intent": "Graph Topology Beats One Giant Context",
        "title": "Graph Topology Beats One Giant Context | ClearGlass Intelligence",
        "description": "A practical planner-worker-verifier workflow for multi-agent research: isolated contexts, evidence boundaries, benchmark caveats, and copy-ready prompts.",
        "canonical": "https://www.clearglassinc.com/blog/graph-topology-multi-agent-research-workflow.html",
        "h1": "Graph Topology Beats One Giant Context",
    }
    raise SystemExit(0 if after.get(GRAPH) == expected else 1)
raise SystemExit(2)
