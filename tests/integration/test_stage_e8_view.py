import json
from pathlib import Path

from control.view import open_visualization
from control.human import HumanGateStore
from tests.integration.test_stage_e4_verification import setup


def test_view_regenerates_projection_without_authoritative_transition(tmp_path: Path):
    setup(tmp_path)
    events = (tmp_path / ".idd/state/events.jsonl").read_text()
    head = json.loads((tmp_path / ".idd/state/events.head.json").read_text())

    dashboard, opened = open_visualization(tmp_path, launch=False)

    assert dashboard == tmp_path / ".idd/views/dashboard.md"
    assert opened is False
    assert "ITDD-DERIVED" in dashboard.read_text()
    assert "REQ-001" in (tmp_path / ".idd/views/intent.md").read_text()
    assert (tmp_path / ".idd/views/graph.md").exists()
    assert (tmp_path / ".idd/views/timeline.md").exists()
    dashboard.write_text("manual edit must not become authority")
    open_visualization(tmp_path, launch=False)
    assert "manual edit must not become authority" not in dashboard.read_text()
    assert (tmp_path / ".idd/state/events.jsonl").read_text() == events
    assert json.loads((tmp_path / ".idd/state/events.head.json").read_text()) == head
    assert HumanGateStore(tmp_path).reconstruct() == {}
