#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
LOCAL_ACTIONS = ROOT / ".github" / "actions"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def actions_audit(start: int, end: int) -> int:
    audit = load_module("audit_probe", ROOT / "scripts" / "audit_github_actions.py")
    for path in paths()[start:end]:
        result = audit.load(path)
        audit.audit(result)
        if result.errors:
            return 1
    return 0


def doctor(start: int, end: int) -> int:
    module = load_module("doctor_probe", ROOT / "scripts" / "workflow_doctor.py")
    for path in paths()[start:end]:
        text = path.read_text(encoding="utf-8")
        if module.unpinned_external_actions(path, text):
            return 1
        _, error = module.load_yaml(path)
        if error:
            return 1
    return 0


def doctor_local() -> int:
    module = load_module("doctor_local_probe", ROOT / "scripts" / "workflow_doctor.py")
    if not LOCAL_ACTIONS.exists():
        return 0
    for path in sorted(LOCAL_ACTIONS.glob("**/action.y*ml")):
        text = path.read_text(encoding="utf-8")
        if module.unpinned_external_actions(path, text):
            return 1
        _, error = module.load_yaml(path)
        if error:
            return 1
    return 0


def main() -> int:
    mode = sys.argv[1]
    if mode == "doctor-local":
        return doctor_local()
    start, end = int(sys.argv[2]), int(sys.argv[3])
    if mode == "actions":
        return actions_audit(start, end)
    if mode == "doctor":
        return doctor(start, end)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
