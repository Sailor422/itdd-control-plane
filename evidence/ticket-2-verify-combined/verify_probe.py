import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from control.skills import create_clarification_proposal, ClarificationProposalStore, SkillContractError
from control.authorization.capabilities import CapabilityIssuer
from skills.runtime import *

def snap(root):
 return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
def cap(root):
 return CapabilityIssuer(root).issue({"capability_id":"CAP-001","schema_version":1,"project_id":"project-1","role":"CONVERSATIONAL","execution_id":"EXEC-1","issued_at":"2026-09-20T10:00:00Z","baseline_sha":"a"*40,"allowed_reads":["CONTEXT.md"],"allowed_writes":[".idd/skills"],"allowed_executes":[],"allowed_operations":["REQUEST_CLARIFICATION","CREATE_ARTIFACT"],"forbidden_operations":["INTENT_APPROVAL","STATE_TRANSITION"],"allowed_request_types":["clarification"],"scope_bindings":{"intent_id":"I-001","intent_version":1},"version":1},event_id="evt-cap-001",timestamp="2026-09-20T10:00:00Z")
def req(**kw):
 x={"project_id":"project-1","execution_id":"EXEC-1","intent_id":"I-001","intent_version":1,"baseline_sha":"a"*40,"source_inputs":["CONTEXT.md"],"terms":[],"assumptions":[],"open_questions":[]}; x.update(kw); return x
root=Path(tempfile.mkdtemp(prefix="independent-direct-")); (root/"CONTEXT.md").write_text("x")
p=create_clarification_proposal(root,request=req(),capability=cap(root),actor_type="human",actor_id="op",timestamp="2026-09-20T10:01:00Z",event_id="evt-proposal-001")
assert p==ClarificationProposalStore(root).reconstruct()[p["proposal_id"]]
# child fresh reconstruction
code='from control.skills import ClarificationProposalStore; import json,sys; print(json.dumps(ClarificationProposalStore(sys.argv[1]).reconstruct(),sort_keys=True))'
r=subprocess.run([sys.executable,"-c",code,str(root)],capture_output=True,text=True,check=True)
assert p["proposal_id"] in r.stdout
before=snap(root)
for bad in [req(source_inputs=["../outside"]),req(project_id="project-2"),req(execution_id="EXEC-2"),req(baseline_sha="b"*40)]:
 try: create_clarification_proposal(root,request=bad,capability=cap(root),actor_type="human",actor_id="op",timestamp="2026-09-20T10:01:00Z",event_id="bad")
 except Exception: pass
 else: raise AssertionError("hostile accepted")
assert snap(root)==before
# tamper artifact
path=ClarificationProposalStore(root)._path(p["proposal_id"],1); d=json.loads(path.read_text()); d["status"]="APPROVED"; path.write_text(json.dumps(d))
try: ClarificationProposalStore(root).reconstruct()
except Exception: pass
else: raise AssertionError("tamper accepted")
# runtime positive + binding
rr=Path(tempfile.mkdtemp(prefix="independent-runtime-")); shutil.copytree(Path("skills"),rr/"skills"); runtime=SkillRuntime(rr); grant=CapabilityGrant("project-1","EXEC-1",rr,frozenset({"project.artifact.write"})); inv=SkillInvocation("project-1","EXEC-1","DRAFT-1","human",{"project_id":"project-1","execution_id":"EXEC-1","draft_id":"DRAFT-1","source_inputs":[{"source_id":"CONTEXT.md","text":"Terms"}]}); out=runtime.invoke("itdd.grill-with-docs",inv,grant); assert out["authority"]=="none"
before=snap(rr)
for bad in [SkillInvocation("project-2","EXEC-1","DRAFT-1","human",inv.inputs),SkillInvocation("project-1","EXEC-2","DRAFT-1","human",inv.inputs),SkillInvocation("project-1","EXEC-1","DRAFT-1","agent",inv.inputs)]:
 try: runtime.invoke("itdd.grill-with-docs",bad,grant)
 except SkillRuntimeError: pass
 else: raise AssertionError("runtime hostile accepted")
assert snap(rr)==before
print(json.dumps({"result":"PASS","direct_root":str(root),"runtime_root":str(rr),"proposal_id":p["proposal_id"]},sort_keys=True))
