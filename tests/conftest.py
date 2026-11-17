import os
import sys

# Make `import main` and `import modules.*` work when running `pytest` from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(autouse=True)
def isolated_global_ledger(tmp_path, monkeypatch):
    """Never let tests touch the real ~/.historical_oddities spend ledger."""
    path = str(tmp_path / "global_ledger.jsonl")
    monkeypatch.setenv("HO_SPEND_LEDGER", path)
    import modules.costs
    monkeypatch.setattr(modules.costs, "GLOBAL_LEDGER_PATH", path)
    return path
