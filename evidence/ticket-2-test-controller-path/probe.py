import os,sys,json,hashlib,shutil,tempfile,subprocess
from pathlib import Path
from control.skills import create_clarification_proposal, ClarificationProposalStore, SkillContractError
from control.authorization.capabilities import CapabilityIssuer
from control.events import EventLogIntegrityError
from skills.runtime import CapabilityGrant, SkillInvocation, SkillRuntime, SkillRuntimeError

def files(root):
 p=root/'.idd'; return {str(x.relative_to(root)):x.read_bytes() for x in p.rglob('*') if x.is_file()} if p.exists() else {}
def cap(root, **kw):
 d={'capability_id':kw.pop('capability_id','CAP-001'),'schema_version':1,'project_id':'project-1','role':'CONVERSATIONAL','execution_id':'EXEC-1','issued_at':'2026-09-20T10:00:00Z','baseline_sha':'a'*40,'allowed_reads':['CONTEXT.md'],'allowed_writes':['.idd/skills'],'allowed_executes':[],'allowed_operations':['REQUEST_CLARIFICATION','CREATE_ARTIFACT'],'forbidden_operations':['INTENT_APPROVAL','STATE_TRANSITION'],'allowed_request_types':['clarification'],'scope_bindings':{'intent_id':'I-001','intent_version':1},'version':1}; d.update(kw); return CapabilityIssuer(root).issue(d,event_id='evt-cap-'+d['capability_id'],timestamp='2026-09-20T10:00:00Z')
def req(**kw):
 d={'project_id':'project-1','execution_id':'EXEC-1','intent_id':'I-001','intent_version':1,'baseline_sha':'a'*40,'source_inputs':['CONTEXT.md'],'terms':[],'assumptions':[],'open_questions':[]}; d.update(kw); return d
def direct(root, name, request, capability=None, actor='human'):
 b=files(root)
 try:
  x=create_clarification_proposal(root,request=request,capability=capability or standard,actor_type=actor,actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-'+name)
  return {'probe':name,'actual':'ACCEPT','proposal':x,'pass':name=='positive','state_unchanged':files(root)==b,'before_files':len(b),'after_files':len(files(root))}
 except Exception as e: return {'probe':name,'actual':'REJECT '+type(e).__name__+': '+str(e),'pass':name!='positive','state_unchanged':files(root)==b,'before_files':len(b),'after_files':len(files(root))}
root=Path(tempfile.mkdtemp(prefix='ticket2-direct-'))
results=[]
standard=cap(root); r=direct(root,'positive',req()); results.append(r); print(json.dumps(r,sort_keys=True,default=str))
# fresh reconstruction
try:
 rec=ClarificationProposalStore(root).reconstruct(); r={'probe':'fresh-process reconstruction','actual':'local reconstruct','pass':bool(rec)}
 code='import json,sys; from control.skills import ClarificationProposalStore; print(json.dumps(ClarificationProposalStore(sys.argv[1]).reconstruct(),sort_keys=True))'
 q=subprocess.run([sys.executable,'-c',code,str(root)],capture_output=True,text=True,env={**os.environ,'PYTHONPATH':os.environ['PYTHONPATH']})
 r.update({'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'pass':q.returncode==0 and json.loads(q.stdout)==rec}); print(json.dumps(r,sort_keys=True)); results.append(r)
except Exception as e: print(json.dumps({'probe':'fresh-process reconstruction','actual':repr(e),'pass':False})); raise
cases=[('unauthorized role',req(),None,'agent'),('wrong project',req(project_id='project-2'),None,'human'),('wrong execution',req(execution_id='EXEC-2'),None,'human'),('wrong intent',req(intent_id='I-002'),None,'human'),('wrong intent version',req(intent_version=2),None,'human'),('stale baseline',req(baseline_sha='b'*40),None,'human'),('path escape source',req(source_inputs=['../outside-secret']),None,'human'),('absolute source',req(source_inputs=['/tmp/outside']),None,'human'),('missing input',dict(req(),terms=None),None,'human'),('extra input',{**req(), 'unexpected':'x'},None,'human'),('malformed source type',req(source_inputs=[3]),None,'human'),('capability expansion',req(),cap(root,capability_id='CAP-002',allowed_operations=['REQUEST_CLARIFICATION','CREATE_ARTIFACT','STATE_TRANSITION']),'human'),('forbidden authority missing',req(),cap(root,capability_id='CAP-003',forbidden_operations=['INTENT_APPROVAL']),'human')]
for name,request,cp,actor in cases:
 r=direct(root,name,request,cp,actor); print(json.dumps(r,sort_keys=True,default=str)); results.append(r)
 if not r['pass']: print('STOP'); break
# tampering only if reached
if all(x['pass'] for x in results):
 p=next((root/'.idd/skills/grill-with-docs').rglob('v1.json')); orig=p.read_bytes(); d=json.loads(orig); d['status']='APPROVED'; p.write_text(json.dumps(d));
 try: ClarificationProposalStore(root).reconstruct(); r={'probe':'tampered proposal','actual':'ACCEPT','pass':False}
 except Exception as e:r={'probe':'tampered proposal','actual':'REJECT '+type(e).__name__+': '+str(e),'pass':True}
 print(json.dumps(r)); results.append(r); p.write_bytes(orig)
# runtime separate
rr=Path(tempfile.mkdtemp(prefix='ticket2-runtime-')); shutil.copytree(Path(__file__).parents[2]/'skills',rr/'skills') if False else shutil.copytree(Path.cwd()/'skills',rr/'skills')
rt=SkillRuntime(rr); grant=CapabilityGrant('EXEC-1',rr,frozenset({'project.artifact.write'})); baseinv={'project_id':'project-1','execution_id':'EXEC-1','draft_id':'DRAFT-1','role':'human','inputs':{'project_id':'project-1','execution_id':'EXEC-1','draft_id':'DRAFT-1','source_inputs':[{'source_id':'CONTEXT.md','text':'Terms'}]}}
def runtime(name, inv, gr=grant):
 # hostile overrides target invocation envelope; mirror bindings inside required inputs
 if 'inputs' not in inv:
  outer={k:v for k,v in inv.items() if k in ('project_id','execution_id','draft_id','source_inputs')}
  inner=inv.get('inputs',outer)
  inv={**inv,'inputs':inner}
  for k in ('project_id','execution_id','draft_id','source_inputs'):
   if k in inv and k != 'inputs': inv['inputs'][k]=inv[k]
 b=files(rr)
 try: x=rt.invoke('itdd.grill-with-docs',SkillInvocation(**inv),gr); out={'probe':'runtime '+name,'actual':'ACCEPT','pass':name=='positive','state_unchanged':files(rr)==b}
 except Exception as e: out={'probe':'runtime '+name,'actual':'REJECT '+type(e).__name__+': '+str(e),'pass':name!='positive','state_unchanged':files(rr)==b}
 print(json.dumps(out,sort_keys=True)); return out
runtime('positive',baseinv)
for name,inv in [('unauthorized role',{**baseinv,'role':'agent'}),('wrong project',{**baseinv,'project_id':'project-2','inputs':{**baseinv['inputs'],'project_id':'project-2'}}),('wrong execution',{**baseinv,'execution_id':'EXEC-2','inputs':{**baseinv['inputs'],'execution_id':'EXEC-2'}}),('path traversal source id',{**baseinv,'inputs':{**baseinv['inputs'],'source_inputs':[{'source_id':'../outside','text':'x'}]}}),('malformed missing input',{**baseinv,'inputs':{'project_id':'project-1','execution_id':'EXEC-1','draft_id':'DRAFT-1'}}),('extra input',{**baseinv,'inputs':{**baseinv['inputs'],'extra':'x'}}),('malformed source',{**baseinv,'inputs':{**baseinv['inputs'],'source_inputs':['x']}}),('capability missing',{**baseinv})]:
 runtime(name,inv,CapabilityGrant('EXEC-1',rr,frozenset()) if name=='capability missing' else grant)
print(json.dumps({'roots':[str(root),str(rr)],'result_count':len(results)}))
