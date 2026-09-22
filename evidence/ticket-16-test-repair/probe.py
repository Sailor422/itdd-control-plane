import sys,json,tempfile,shutil,subprocess,os
from pathlib import Path
from skills.runtime import *
ROOT=Path.cwd()
def files(p): return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
def reject(label, fn):
 try: fn(); print(label+': UNEXPECTED_PASS'); return False
 except Exception as e: print(label+': PASS '+type(e).__name__+' '+str(e)); return True
r=SkillRuntime(ROOT)
print('workflow', [x['name'] for x in r.discover_workflow()['steps']])
req={'project_id':ROOT.name,'execution_id':'exec-16','role':'controller','baseline_sha':'a'*40,'candidate_sha':'b'*40,'steps':['wayfinder','to-spec','to-tickets','implement','tdd','code-review'],'approved_contract':'ticket-16'}
print('accept',r.validate_workflow_acceptance(req))
# acceptance boundaries
for label,mut in [('wrong_role',lambda q:q.update(role='BUILD')),('missing',lambda q:q.pop('approved_contract')),('extra',lambda q:q.update(extra=1)),('stale_baseline',lambda q:q.update(baseline_sha='c'*40)),('forbidden_lifecycle',lambda q:q.update(lifecycle='PROMOTE'))]:
 q=dict(req); mut(q); reject('accept_'+label,lambda q=q:r.validate_workflow_acceptance(q))
# runtime isolated
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'proj'; shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('.git','.idd','__pycache__','.worktrees'))
 rt=SkillRuntime(p); g=CapabilityGrant(p.name,'exec-1',p,frozenset({'project.artifact.write'}))
 def inv(project=p.name,execution='exec-1',role='human',inputs=None,draft='draft-1'):
  return SkillInvocation(project,execution,draft,role,inputs or {'project_id':project,'execution_id':execution,'draft_id':draft,'source_inputs':[{'source_id':'CONTEXT.md','text':' Hello world'}]})
 # ordered authority/binding
 for label,iv,gr in [
 ('wrong_project',inv('other'),g),('wrong_execution',inv(p.name,'other'),g),
 ('root_mismatch',inv(),CapabilityGrant(p.name,'exec-1',p.parent,frozenset({'project.artifact.write'}))),
 ('worker',inv(role='BUILD'),g),
 ('cap_extra',inv(),CapabilityGrant(p.name,'exec-1',p,frozenset({'project.artifact.write','lifecycle.advance'}))),
 ('cap_missing',inv(),CapabilityGrant(p.name,'exec-1',p,frozenset())),
 ('extra_input',inv(inputs={'project_id':p.name,'execution_id':'exec-1','draft_id':'draft-1','source_inputs':[{'source_id':'x','text':'x'}],'extra':1}),g),
 ('source_escape',inv(inputs={'project_id':p.name,'execution_id':'exec-1','draft_id':'draft-1','source_inputs':[{'source_id':'../outside','text':'x'}]}),g),
 ('source_abs',inv(inputs={'project_id':p.name,'execution_id':'exec-1','draft_id':'draft-1','source_inputs':[{'source_id':'/tmp/out','text':'x'}]}),g),
 ('bad_id',inv(inputs={'project_id':p.name,'execution_id':'exec-1','draft_id':'draft-1','source_inputs':[{'source_id':'x/y','text':'x'}]}),g),
 ]:
  b=files(p); ok=reject('invoke_'+label,lambda iv=iv,gr=gr:rt.invoke('itdd.grill-with-docs',iv,gr)); print(label+'_unchanged',b==files(p))
 # valid then tamper artifact and event
 out=rt.invoke('itdd.grill-with-docs',inv(),g); print('valid',out['status'],out['authority'])
 art=p/'.idd/skills/artifacts/exec-1.json'; old=art.read_bytes(); d=json.loads(old); d['status']='APPROVED'; art.write_text(json.dumps(d)); reject('tamper_artifact',lambda: json.loads(art.read_text())['status']=='PROPOSAL_ONLY')
 # fresh reconstruction identity
 code='from pathlib import Path; from skills.runtime import SkillRuntime; print([s["name"] for s in SkillRuntime(Path.cwd()).discover_workflow()["steps"]])'
 x=subprocess.run([sys.executable,'-c',code],cwd=p,capture_output=True,text=True); print('fresh_process',x.returncode,x.stdout.strip())
