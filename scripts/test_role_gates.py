#!/usr/bin/env python3
"""Role RACI gates for Decision actions."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "app" / "server.py"


def _load_server():
    spec = importlib.util.spec_from_file_location("server_under_test", SERVER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Avoid binding the HTTP server on import side effects beyond module body.
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "app"))
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    mod = _load_server()
    roles = mod.ROLE_ACTIONS
    assert roles["accountant"] == set()
    assert "accept" in roles["fund_admin"]
    assert "reject" in roles["fund_admin"]
    assert "override" in roles["fund_admin"]
    assert "sign_off" in roles["fund_admin"]
    assert "accept" in roles["fund_manager"]
    assert "override" in roles["fund_manager"]
    assert "sign_off" in roles["fund_manager"]
    assert "reject" not in roles["fund_manager"]
    print("OK: role RACI gates")


if __name__ == "__main__":
    main()
