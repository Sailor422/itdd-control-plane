import tempfile, shutil, json
from pathlib import Path
from control.skills import create_clarification_proposal, SkillContractError
from control.authorization.capabilities import CapabilityIssuer
from skills.runtime import *
def cap(root): return CapabilityIssuer(root).issue({"capability_id":"CAP-001","schema_version":1,"project_id":"project-1","role":"CONVERSATIONAL","execution_id":"EXEC-1","issued_at":"2026-09-20T10:00:00Z","baseline_sha":"a"*40,"allowed_reads":["CONTEXT.md"],"allowed_writes":[".idd/skills"],"allowed_executes":[],"allowed_operations":["REQUEST_CLARIFICATION","CREATE_ARTIFACT"],"forbidden_operations":["INTENT_APPROVAL","STATE_TRANSITION"],"allowed_request_types":["clarification"],"scope_bindings":{"intent_id":"I-001","intent_version":1},"version":1},event_id="evt-cap-001",timestamp="2026-09-20T10:00:00Z")
def req(src): return {"project_id":"project-1","execution_id":"EXEC-1","intent_id":"I-001","intent_version":1,"baseline_sha":"a"*40,"source_inputs":[src],"terms":[],"assumptions":[],"open_questions":[]}
for src in ["../outside-secret", "/etc/passwd"]:
 with tempfile.TemporaryDirectory() as d:
  p=Path(d); c=cap(p); before={str(x.relative_to(p)):x.read_bytes() for x in p.rglob("*") if x.is_file()}
  try: create_clarification_proposal(p,request=req(src),capability=c,actor_type="human",actor_id="operator-1",timestamp="2026-09-20T10:01:00Z",event_id="evt-proposal-001"); print("controller",src,"UNEXPECTED_PASS")
  except Exception as e: print("controller",src,"rejected",type(e).__name__)
  print("unchanged",before=={str(x.relative_to(p)):x.read_bytes() for x in p.rglob("*") if x.is_file()})
