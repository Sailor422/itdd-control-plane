import json
import subprocess
import sys
from pathlib import Path

from control.models.store import StageCStore
from tests.integration.test_stage_c_store import approve, draft, graph


def test_fresh_process_reconstructs_approved_intent_and_graph_history(tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    store.create_graph(graph(), event_id="evt-graph-created", timestamp="2026-09-19T18:02:00Z", actor_type="agent", actor_id="planner")
    store.revise_graph(graph(2, "evt-graph-revised", [{"from": "EU-001", "to": "EU-002"}]), event_id="evt-graph-revised", timestamp="2026-09-19T18:04:00Z", actor_type="agent", actor_id="planner")
    script = """
import json, sys
from control.models.store import StageCStore
state = StageCStore(sys.argv[1]).reconstruct()
print(json.dumps({'intent': state['approved_intent']['intent_id'] + '-v' + str(state['approved_intent']['version']), 'active': state['active_graph']['graph_id'] + '-v' + str(state['active_graph']['version']), 'history': sorted([key[0] + '-v' + str(key[1]) for key in state['graphs']])}, sort_keys=True))
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == {"intent": "I-001-v1", "active": "G-001-v2", "history": ["G-001-v1", "G-001-v2"]}

