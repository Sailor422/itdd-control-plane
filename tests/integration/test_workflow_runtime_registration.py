import hashlib, json
from pathlib import Path
import pytest
from skills.runtime import SkillRuntime, SkillRuntimeError

ROOT = Path(__file__).parents[2]

def test_controller_workflow_registration_is_complete_and_ordered():
    workflow = SkillRuntime(ROOT).discover_workflow()
    assert [s["name"] for s in workflow["steps"]] == ["wayfinder", "to-spec", "to-tickets", "implement", "tdd", "code-review"]
    assert workflow["worker_boundary"]["skills_authority"] is False

def test_workflow_acceptance_is_controller_only_and_non_mutating():
    runtime = SkillRuntime(ROOT)
    req = {"project_id": ROOT.name, "execution_id":"exec-16", "role":"controller", "baseline_sha":"a"*40, "candidate_sha":"b"*40, "steps":["wayfinder","to-spec","to-tickets","implement","tdd","code-review"], "approved_contract":"ticket-16"}
    assert runtime.validate_workflow_acceptance(req)["lifecycle_effect"] == "none"
    req["role"] = "BUILD"
    with pytest.raises(SkillRuntimeError): runtime.validate_workflow_acceptance(req)
