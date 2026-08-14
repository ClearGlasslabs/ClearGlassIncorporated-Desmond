#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.clearglassinc.com"
ROUTES = {
    "app": "/apps/command-center/index.html",
    "investors": "/investors/index.html",
    "client": "/operations/client-onboarding.html",
    "federal": "/operations/federal-supplier-handoff.html",
    "hubspot": "/operations/hubspot-handoff.html",
    "ontario": "/operations/ontario-incorporation-handoff.html",
    "procurement": "/operations/procurement-readiness.html",
    "stripe": "/operations/stripe-handoff.html",
}

def parse(path: str | Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return {
        node.findtext("s:loc", default="", namespaces=ns): node.findtext("s:lastmod", default="", namespaces=ns)
        for node in root.findall("s:url", ns)
    }

shutil.copy2(ROOT / "sitemap.xml", "/tmp/sitemap-before.xml")
subprocess.run([sys.executable, "tools/generate_search_assets.py"], cwd=ROOT, check=True)
before = parse("/tmp/sitemap-before.xml")
after = parse(ROOT / "sitemap.xml")
url = BASE + ROUTES[sys.argv[1]]
raise SystemExit(0 if before.get(url) == after.get(url) else 1)
