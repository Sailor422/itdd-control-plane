import json,tempfile,shutil,subprocess,sys
from pathlib import Path
from skills.runtime import *
ROOT=Path.cwd()
def snap(p): return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob("*") if x.is_file()}
def reject(label,fn):
 try: fn(); print(label+": UNEXPECTED_PASS"); return False
 except Exception as e: print(label+": "+type(e).__name__+": "+str(e)); return True
def clone():
 td=tempfile.TemporaryDirectory(); p=Path(td.name)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns(".git",".idd","__pycache__",".worktrees")); return td,p
r=SkillRuntime(ROOT); assert [x["name"] for x in r.discover_workflow()["steps"]]==["wayfinder","to-spec","to-tickets","implement","tdd","code-review"]
req={"project_id":ROOT.name,"execution_id":"exec-16","role":"controller","baseline_sha":"a"*40,"candidate_sha":"b"*40,"steps":["wayfinder","to-spec","to-tickets","implement","tdd","code-review"],"approved_contract":"ticket-16"}; assert r.validate_workflow_acceptance(req)["lifecycle_effect"]=="none"
for label,mut in [("wrong_role",lambda q:q.update(role="BUILD")),("missing",lambda q:q.pop("approved_contract")),("extra",lambda q:q.update(extra=1)),("bad_sha",lambda q:q.update(candidate_sha="c")),("wrong_steps",lambda q:q.update(steps=["wayfinder"])),("wrong_project",lambda q:q.update(project_id="other"))]:
 q=dict(req); mut(q); assert reject("accept_"+label,lambda q=q:r.validate_workflow_acceptance(q))
# workflow tamper checks
for label,mut in [("workflow_skill_tamper",lambda m:m["workflows"]["steps"][0].update(skill="tdd")),("workflow_step_extra",lambda m:m["workflows"]["steps"][0].update(extra=1)),("registered_id_tamper",lambda m:m["skills"][0].update(id="itdd.other"))]:
 td,p=clone(); mp=p/"skills/manifest.json"; m=json.loads(mp.read_text()); mut(m); mp.write_text(json.dumps(m)); ok=reject(label,lambda p=p:SkillRuntime(p).discover_workflow()); print(label+"_rejected="+str(ok)); td.cleanup()
# contract tamper via discover
for label,field,val in [("contract_name_tamper","name","tampered"),("contract_skillid_tamper","skill_id","itdd.other")]:
 td,p=clone(); cp=p/"skills/grill_with_docs/skill.json"; c=json.loads(cp.read_text()); c[field]=val; cp.write_text(json.dumps(c)); assert reject(label,lambda p=p:SkillRuntime(p).discover()); td.cleanup()
# runtime valid + hostile
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns(".git",".idd","__pycache__",".worktrees")); rt=SkillRuntime(p); g=CapabilityGrant(p.name,"exec-1",p,frozenset({"project.artifact.write"})); inp={"project_id":p.name,"execution_id":"exec-1","draft_id":"draft-1","source_inputs":[{"source_id":"src-1","text":" Hello world"}]}; inv=SkillInvocation(p.name,"exec-1","draft-1","human",inp); out=rt.invoke("itdd.grill-with-docs",inv,g); assert out["status"]=="PROPOSAL_ONLY" and out["authority"]=="none"
 for label,i,gr in [("wrong_project",SkillInvocation("other","exec-1","draft-1","human",{**inp,"project_id":"other"}),g),("wrong_execution",inv,CapabilityGrant(p.name,"other",p,g.capabilities)),("wrong_root",inv,CapabilityGrant(p.name,"exec-1",Path(td),g.capabilities)),("worker",SkillInvocation(p.name,"exec-1","draft-1","BUILD",inp),g),("extra_input",SkillInvocation(p.name,"exec-1","draft-1","human",{**inp,"extra":1}),g),("dotdot_source",SkillInvocation(p.name,"exec-1","draft-1","human",{**inp,"source_inputs":[{"source_id":"..","text":"x"}]}),g),("absolute_source",SkillInvocation(p.name,"exec-1","draft-1","human",{**inp,"source_inputs":[{"source_id":"/tmp/x","text":"x"}]}),g),("cap_expand",inv,CapabilityGrant(p.name,"exec-1",p,frozenset({"project.artifact.write","lifecycle.advance"}))),("missing_cap",inv,CapabilityGrant(p.name,"exec-1",p,frozenset()))]:
  before=snap(p); ok=reject(label,lambda i=i,gr=gr:rt.invoke("itdd.grill-with-docs",i,gr)); assert ok and before==snap(p),label
print("ALL_INDEPENDENT_CHECKS_PASS")
