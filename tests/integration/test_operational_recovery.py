import subprocess
from pathlib import Path

import pytest

from control.models.store import StageCStore
from control.operational import OperationalController, OperationalError


def setup_building(root):
    (root / "src").mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    (root / "src/base.py").write_text("x=1\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@e", "commit", "-m", "base"], cwd=root, check=True, capture_output=True)
    ts="2026-09-24T00:00:00Z"; store=StageCStore(root)
    store.create_intent_draft({"intent_id":"I-001","version":1,"status":"DRAFT","created_at":ts,"created_by":"human","project_id":"demo","title":"t","purpose":"p","requirements":[{"requirement_id":"REQ-001","text":"r"}],"constraints":[],"acceptance_summary":"a","source_event_id":"i-created","schema_version":1},event_id="i-created",timestamp=ts,actor_type="human",actor_id="human")
    store.approve_intent("I-001",1,event_id="i-approved",timestamp=ts,actor_type="human",actor_id="human")
    c=OperationalController(root)
    graph={"graph_id":"G-001","version":1,"project_id":"demo","intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":ts,"created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"r","source_event_id":"g-created","schema_version":1}
    item=c.propose_plan(operation_id="OP-001",project_id="demo",graph=graph,eu_paths={"EU-001":["src/base.py"]},timestamp=ts,event_prefix="op")
    item.update(status="BUILDING",execution_id="EXEC-OLD",worktree=str(root/".idd/build_workspaces/OP-001/EU-001"))
    c.operations.write(item,event_id="run-building",event_type="eu.building",timestamp=ts)
    workspace=Path(item["worktree"]); workspace.mkdir(parents=True)
    (workspace/"valuable.txt").write_text("preserve")
    return c,workspace,ts


def test_recovery_decline_and_confirmed_retry_preserve_workspace_and_history(tmp_path):
    c,workspace,ts=setup_building(tmp_path)
    before=len(c.operations.events.verify())
    args=dict(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-1",old_execution_id="EXEC-OLD",fresh_execution_id="EXEC-NEW",workspace=workspace,timestamp=ts)
    with pytest.raises(OperationalError): c.recover_building_run(**args,confirm_worker_stopped=False)
    assert len(c.operations.events.verify())==before and workspace.exists()
    result=c.recover_building_run(**args,confirm_worker_stopped=True)
    assert result["status"]=="READY" and result["execution_id"]=="EXEC-NEW"
    quarantine=tmp_path/".idd/quarantine/REC-1"
    assert (quarantine/"valuable.txt").read_text()=="preserve"
    events=c.operations.events.verify()
    types=[e["event_type"] for e in events]
    assert types[-2:]==["eu.abandoned","eu.recovery_ready"]
    assert c.recover_building_run(**args,confirm_worker_stopped=True)==result


def test_recovery_rejects_workspace_escape_without_side_effects(tmp_path):
    c,workspace,ts=setup_building(tmp_path)
    outside=tmp_path/"outside"; outside.mkdir()
    before=c.operations.events.verify()
    with pytest.raises(OperationalError):
        c.recover_building_run(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-2",old_execution_id="EXEC-OLD",fresh_execution_id="EXEC-NEW",workspace=outside,confirm_worker_stopped=True,timestamp=ts)
    assert c.operations.events.verify()==before and outside.exists() and not (tmp_path/".idd/recoveries/REC-2.json").exists()


def test_recovery_revokes_stale_builder_capability_at_public_authorizer(tmp_path):
    from control.authorization import CapabilityIssuer, ControllerAuthorizer, AccessType
    c, workspace, ts = setup_building(tmp_path)
    envelope = {"capability_id":"CAP-901", "schema_version":1, "project_id":"demo", "role":"BUILDER",
        "execution_id":"EXEC-OLD", "issued_at":ts, "baseline_sha":"a"*40, "allowed_reads":[],
        "allowed_writes":[], "allowed_executes":[], "allowed_operations":[AccessType.READ],
        "forbidden_operations":[], "allowed_request_types":[], "scope_bindings":{}, "version":1, "issued_by":"controller"}
    CapabilityIssuer(tmp_path).issue(envelope, event_id="cap-issue", timestamp=ts)
    item=c.operations.read("OP-001"); item["builder_capability_id"]="CAP-901"
    c.operations.write(item,event_id="builder-bound",event_type="worker.execution.completed",timestamp=ts)
    c.recover_building_run(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-901",
        old_execution_id="EXEC-OLD",fresh_execution_id="EXEC-NEW",workspace=workspace,
        confirm_worker_stopped=True,timestamp=ts)
    decision=ControllerAuthorizer(tmp_path).authorize("CAP-901",
        {"request_id":"r","project_id":"demo","execution_id":"EXEC-OLD","baseline_sha":"a"*40,"role":"BUILDER","operation":"READ"},
        {"project_root":str(tmp_path),"project_id":"demo","execution_id":"EXEC-OLD","baseline_sha":"a"*40})
    assert decision.reason == "DENY_NO_CAPABILITY"


def test_recovery_refuses_preexisting_quarantine_without_mutation(tmp_path):
    c,workspace,ts=setup_building(tmp_path)
    destination=tmp_path/".idd/quarantine/REC-COLLISION"
    destination.mkdir(parents=True)
    (destination/"unknown.txt").write_text("do not touch")
    before=c.operations.events.verify()
    with pytest.raises(OperationalError):
        c.recover_building_run(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-COLLISION",
            old_execution_id="EXEC-OLD",fresh_execution_id="EXEC-NEW",workspace=workspace,
            confirm_worker_stopped=True,timestamp=ts)
    assert c.operations.events.verify()==before
    assert workspace.exists() and (destination/"unknown.txt").read_text()=="do not touch"
    assert not (tmp_path/".idd/recoveries/REC-COLLISION.json").exists()


def test_cli_decline_does_not_create_recovery_state(tmp_path, monkeypatch, capsys):
    from control.recover import main
    c,workspace,ts=setup_building(tmp_path)
    before=c.operations.events.verify()
    monkeypatch.setattr("builtins.input", lambda prompt: "NO")
    result=main([str(tmp_path),"OP-001","EU-001","REC-DECLINE","EXEC-OLD","EXEC-NEW",str(workspace)])
    assert result == 1
    assert "Cancelled" in capsys.readouterr().out
    assert c.operations.events.verify()==before and workspace.exists()
    assert not (tmp_path/".idd/recoveries/REC-DECLINE.json").exists()


def test_recovery_binding_rejects_reuse_for_changed_request(tmp_path):
    c,workspace,ts=setup_building(tmp_path)
    args=dict(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-BIND",old_execution_id="EXEC-OLD",
        fresh_execution_id="EXEC-NEW",workspace=workspace,confirm_worker_stopped=True,timestamp=ts)
    first=c.recover_building_run(**args)
    assert c.recover_building_run(**args)==first
    altered=dict(args); altered["fresh_execution_id"]="EXEC-OTHER"
    with pytest.raises(OperationalError): c.recover_building_run(**altered)
    assert c.operations.read("OP-001")==first
    assert [e["event_type"] for e in c.operations.events.verify()][-2:]==["eu.abandoned","eu.recovery_ready"]


def test_cli_confirm_recovers_and_does_not_launch_builder(tmp_path, monkeypatch, capsys):
    from control.recover import main
    c,workspace,ts=setup_building(tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "YES")
    result=main([str(tmp_path),"OP-001","EU-001","REC-CLI","EXEC-OLD","EXEC-NEW",str(workspace)])
    assert result == 0
    output=capsys.readouterr().out
    assert "Recovery ready" in output and "builder not launched" in output
    assert c.operations.read("OP-001")["status"] == "READY"
    assert not workspace.exists() and (tmp_path/".idd/quarantine/REC-CLI").exists()


def test_recovery_retries_after_expected_abandoned_append_failure(tmp_path, monkeypatch):
    from control.events import EventLog
    c,workspace,ts=setup_building(tmp_path)
    args=dict(operation_id="OP-001",eu_id="EU-001",recovery_id="REC-RETRY",old_execution_id="EXEC-OLD",
        fresh_execution_id="EXEC-NEW",workspace=workspace,confirm_worker_stopped=True,timestamp=ts)
    original=EventLog.append
    def fail_once(log,event):
        if event["event_id"] == "REC-RETRY-abandoned":
            monkeypatch.setattr(EventLog,"append",original)
            raise OSError("injected append failure")
        return original(log,event)
    monkeypatch.setattr(EventLog,"append",fail_once)
    with pytest.raises(OSError): c.recover_building_run(**args)
    result=c.recover_building_run(**args)
    assert result["status"] == "READY"
    assert [e["event_type"] for e in c.operations.events.verify()][-2:]==["eu.abandoned","eu.recovery_ready"]
