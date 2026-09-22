import json, tempfile, shutil, subprocess, sys
from pathlib import Path
from skills.runtime import *
ROOT=Path.cwd()
def snap(p): return sorted(str(x.relative_to(p)) for x in p.rglob('*') if x.is_file())
def expect(label, fn):
 try: fn(); print(label+": UNEXPECTED_PASS")
 except Exception as e: print(label+": rejected "+type(e).__name__+": "+str(e))
r=SkillRuntime(ROOT); print("workflow", [x["name"] for x in r.discover_workflow()["steps"]])
req={"project_id":ROOT.name,"execution_id":"exec-16","role":"controller","baseline_sha":"a"*40,"candidate_sha":"b"*40,"steps":["wayfinder","to-spec","to-tickets","implement","tdd","code-review"],"approved_contract":"ticket-16"}
print("accept",r.validate_workflow_acceptance(req))
for label,mut in [("wrong_role",lambda q:q.update(role="BUILD")),("missing",lambda q:q.pop("approved_contract")),("extra",lambda q:q.update(extra=1)),("stale_sha",lambda q:q.update(candidate_sha="c")),("wrong_steps",lambda q:q.update(steps=["wayfinder"]))]:
 q=dict(req); mut(q); expect(label,lambda q=q:r.validate_workflow_acceptance(q))
# runtime valid and hostile invocations in isolated copies
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('.git','.idd','__pycache__','.worktrees'))
 rt=SkillRuntime(p); g=CapabilityGrant("exec-1",p,frozenset({"project.artifact.write"}))
 base=SkillInvocation(p.name,"exec-1","draft-1","human",{"project_id":p.name,"execution_id":"exec-1","draft_id":"draft-1","source_inputs":[{"source_id":"src-1","text":" Hello "+"world"}]})
 out=rt.invoke("itdd.grill-with-docs",base,g); print("invoke",out["status"],out["authority"],out["artifact_type"])
 for label,inv,grant in [("wrong_project",SkillInvocation("other", "exec-1","draft-2","human",{"project_id":"other","execution_id":"exec-1","draft_id":"draft-2","source_inputs":[{"source_id":"s","text":"x"}]}),g),("wrong_execution",base,CapabilityGrant("other",p,frozenset({"project.artifact.write"}))),("worker_role",SkillInvocation(p.name,"exec-1","d","BUILD",base.inputs),g),("extra_input",SkillInvocation(p.name,"exec-1","d","human",{**base.inputs,"extra":1}),g),("bad_source_id",SkillInvocation(p.name,"exec-1","d","human",{"project_id":p.name,"execution_id":"exec-1","draft_id":"d","source_inputs":[{"source_id":"../escape","text":"x"}]}),g)]:
  before=snap(p); expect(label,lambda inv=inv,grant=grant:rt.invoke("itdd.grill-with-docs",inv,grant)); print(label+"_unchanged",before==snap(p))
# malformed manifest/identity/paths in isolated copies
for label,edit in [("missing_workflow",lambda m:m.pop("workflows")),("extra_workflow",lambda m:m["workflows"].update(extra=1)),("stale_skill_id",lambda m:m["skills"][0].update(id="stale"))]:
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/"proj"; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('.git','.idd','__pycache__','.worktrees')); mp=p/'skills/manifest.json'; m=json.loads(mp.read_text()); edit(m); mp.write_text(json.dumps(m)); expect(label,lambda p=p:SkillRuntime(p).discover_workflow() if label!="stale_skill_id" else SkillRuntime(p).discover())
# fresh process reconstruction
code='from pathlib import Path; from skills.runtime import SkillRuntime; print([s["name"] for s in SkillRuntime(Path.cwd()).discover_workflow()["steps"]])'
x=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True); print("fresh_process",x.returncode,x.stdout.strip(),x.stderr.strip())
