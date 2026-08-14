#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,"tools/generate_search_assets.py"],cwd=ROOT,check=True)
root=ET.parse(ROOT/"sitemap.xml").getroot(); ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
value=""
for node in root.findall("s:url",ns):
    if node.findtext("s:loc",default="",namespaces=ns)=="https://www.clearglassinc.com/operations/federal-supplier-handoff.html":
        value=node.findtext("s:lastmod",default="",namespaces=ns); break
raise SystemExit(0 if value==sys.argv[1] else 1)
