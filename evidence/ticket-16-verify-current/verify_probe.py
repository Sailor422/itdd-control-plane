import json, shutil, tempfile, subprocess, sys, os
from pathlib import Path
from skills.runtime import *
ROOT=Path(sys.argv[1])
def snap(p): return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob("*") if x.is_file()}
def reject(label, fn):
 try: fn()
 except Exception as e: print(label+": PASS "+type(e).__name__+": "+str(e)); return
 print(label+": FAIL unexpected acceptance"); raise AssertionError(label)
def clone():
 td=tempfile.TemporaryDirectory(); p=Path(td.name)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns(".git",".idd","__pycache__",".worktrees")); return td,p
# clean constructor/discovery and exact six mapping
r=SkillRuntime(ROOT)
w=r.discover_workflow(); assert [(x["name"],x["skill"]) for x in w["steps"]]==[("wayfinder","wayfinder"),("to-spec","to-spec"),("to-tickets","to-tickets"),("implement","implement"),("tdd","tdd"),("code-review","code-review")]
assert w["controller_boundary"]=={"accepts":"approved-contract","owns":["routing","evidence","lifecycle","promotion"]}
assert w["worker_boundary"]=={"roles":["BUILD","TEST","VERIFY"],"isolated":True,"skills_authority":False}
print("mapping PASS")
# exact acceptance contract, controller-only, identity, no lifecycle/promotion
req={"project_id":ROOT.name,"execution_id":"exec-16","role":"controller","baseline_sha":"a"*40,"candidate_sha":"b"*40,"steps":["wayfinder","to-spec","to-tickets","implement","tdd","code-review"],"approved_contract":"ticket-16"}
out=r.validate_workflow_acceptance(req); assert out=={"decision":"OBSERVED","authority":"controller","lifecycle_effect":"none","promotion_effect":"none","execution_id":"exec-16","candidate_sha":"b"*40}
for label,mut in [("accept role",lambda q:q.update(role="BUILD")),("accept missing",lambda q:q.pop("approved_contract")),("accept extra",lambda q:q.update(extra=1)),("accept sha",lambda q:q.update(candidate_sha="x")),("accept steps",lambda q:q.update(steps=["wayfinder"]))]:
 q=dict(req); mut(q); reject(label,lambda q=q:r.validate_workflow_acceptance(q))
# registration tamper/malformed exactness
for label,mut in [("workflow skill",lambda m:m["workflows"]["steps"][0].update(skill="tdd")),("workflow extra",lambda m:m["workflows"]["steps"][0].update(extra=1)),("manifest id",lambda m:m["skills"][0].update(id="itdd.other")),("workflow missing",lambda m:m.pop("workflows"))]:
 td,p=clone(); mp=p/"skills/manifest.json"; m=json.loads(mp.read_text()); mut(m); mp.write_text(json.dumps(m)); reject(label,lambda p=p:SkillRuntime(p).discover_workflow()); td.cleanup()
# contract identity tamper
for field,val in [("name","tampered"),("skill_id","itdd.other")]:
 td,p=clone(); cp=p/"skills/grill_with_docs/skill.json"; c=json.loads(cp.read_text()); c[field]=val; cp.write_text(json.dumps(c)); reject("contract "+field,lambda p=p:SkillRuntime(p).discover()); td.cleanup()
# valid runtime and fresh child reconstruction
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns(".git",".idd","__pycache__",".worktrees")); rt=SkillRuntime(p); g=CapabilityGrant(p.name,"exec-1",p,frozenset({"project.artifact.write"})); inp={"project_id":p.name,"execution_id":"exec-1","draft_id":"draft-1","source_inputs":[{"source_id":"src-1","text":" Hello world"}]}; inv=SkillInvocation(p.name,"exec-1","draft-1","human",inp); out=rt.invoke("itdd.grill-with-docs",inv,g); assert out["status"]=="PROPOSAL_ONLY" and out["authority"]=="none" and not any(k in out for k in ("approval","promotion","lifecycle")); assert (p/".idd/skills/artifacts/exec-1.json").is_file()
 code='from pathlib import Path; from skills.runtime import SkillRuntime; import sys; print([x["name"] for x in SkillRuntime(Path(sys.argv[1])).discover_workflow()["steps"]])'
 cp=subprocess.run([sys.executable,"-c",code,str(p)],cwd=p,env={**os.environ,"PYTHONPATH":str(p)},capture_output=True,text=True); assert cp.returncode==0 and "code-review" in cp.stdout; print("fresh reconstruction PASS")
 # hostile direct/runtime cases, every rejection leaves bytes unchanged
 cases=[("wrong project",SkillInvocation("other","exec-1","draft-1","human",{**inp,"project_id":"other"}),g),("wrong execution",inv,CapabilityGrant(p.name,"other",p,g.capabilities)),("wrong root",inv,CapabilityGrant(p.name,"exec-1",Path(td),g.capabilities)),("worker",SkillInvocation(p.name,"exec-1","draft-1","BUILD",inp),g),("extra input",SkillInvocation(p.name,"exec-1","draft-1","human",{**inp,"extra":1}),g),("missing cap",inv,CapabilityGrant(p.name,"exec-1",p,frozenset())),("extra cap",inv,CapabilityGrant(p.name,"exec-1",p,frozenset({"project.artifact.write","lifecycle.advance"})))]
 for sid in ["..","foo/../bar","/etc/passwd","../outside-secret","foo\\bar"]: cases.append(("source "+sid,SkillInvocation(p.name,"exec-1","draft-1","human",{**inp,"source_inputs":[{"source_id":sid,"text":"x"}]}),g))
 for label,i,gr in cases:
  before=snap(p); reject(label,lambda i=i,gr=gr:rt.invoke("itdd.grill-with-docs",i,gr)); assert snap(p)==before,label
print("ALL INDEPENDENT CHECKS PASS")
