import json, tempfile, shutil, subprocess, sys, os
from pathlib import Path
from control.authorization.capabilities import CapabilityIssuer
from control.skills import create_clarification_proposal, ClarificationProposalStore, SkillContractError
from control.events import EventLogIntegrityError
from skills.runtime import CapabilityGrant, SkillInvocation, SkillRuntime, SkillRuntimeError

def snap(root):
 p=root/'.idd'
 if not p.exists(): return {}
 return {str(x.relative_to(root)):x.read_bytes().hex() for x in sorted(p.rglob('*')) if x.is_file()}
def cap(root, project='project-1', execution='EXEC-1', baseline='a'*40):
 return CapabilityIssuer(root).issue({'capability_id':'CAP-001','schema_version':1,'project_id':project,'role':'CONVERSATIONAL','execution_id':execution,'issued_at':'2026-09-20T10:00:00Z','baseline_sha':baseline,'allowed_reads':['CONTEXT.md'],'allowed_writes':['.idd/skills'],'allowed_executes':[],'allowed_operations':['REQUEST_CLARIFICATION','CREATE_ARTIFACT'],'forbidden_operations':['INTENT_APPROVAL','STATE_TRANSITION'],'allowed_request_types':['clarification'],'scope_bindings':{'intent_id':'I-001','intent_version':1},'version':1},event_id='evt-cap-001',timestamp='2026-09-20T10:00:00Z')
def req(**o):
 x={'project_id':'project-1','execution_id':'EXEC-1','intent_id':'I-001','intent_version':1,'baseline_sha':'a'*40,'source_inputs':['CONTEXT.md'],'terms':[],'assumptions':[],'open_questions':[]};x.update(o);return x
def run(name, fn, expect_reject=False):
 root=Path(tempfile.mkdtemp(prefix='ticket2-test-')); c=cap(root); before=snap(root)
 try:
  out=fn(root,c); ok=not expect_reject; detail='ACCEPT '+json.dumps(out,sort_keys=True)[:300]
 except Exception as e:
  ok=expect_reject; detail='REJECT '+type(e).__name__+': '+str(e)
 after=snap(root); unchanged=before==after if expect_reject else True
 print(json.dumps({'probe':name,'intended_boundary':'reject' if expect_reject else 'accept','actual':detail,'pass':ok and unchanged,'state_unchanged':unchanged,'before_files':len(before),'after_files':len(after)}))
 if not (ok and unchanged): raise SystemExit(3)
# positive direct
run('positive proposal creation',lambda r,c:create_clarification_proposal(r,request=req(),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-proposal-001'))
# fresh process reconstruction (in same root setup)
root=Path(tempfile.mkdtemp(prefix='ticket2-reconstruct-')); c=cap(root); p=create_clarification_proposal(root,request=req(),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-proposal-001'); code='import json,sys; from control.skills import ClarificationProposalStore; print(json.dumps(ClarificationProposalStore(sys.argv[1]).reconstruct(),sort_keys=True))'; rr=subprocess.run([sys.executable,'-c',code,str(root)],capture_output=True,text=True,check=False,env={**os.environ,'PYTHONPATH':os.getcwd()}); print(json.dumps({'probe':'fresh-process reconstruction','intended_boundary':'same proposal/event state','actual_returncode':rr.returncode,'pass':rr.returncode==0 and json.loads(rr.stdout)[p['proposal_id']]==p,'stdout':rr.stdout,'stderr':rr.stderr}))
# hostile sequence
run('unauthorized role',lambda r,c:create_clarification_proposal(r,request=req(),capability=c,actor_type='agent',actor_id='agent-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('wrong project',lambda r,c:create_clarification_proposal(r,request=req(project_id='project-2'),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('wrong execution',lambda r,c:create_clarification_proposal(r,request=req(execution_id='EXEC-2'),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('stale baseline',lambda r,c:create_clarification_proposal(r,request=req(baseline_sha='b'*40),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('path escape',lambda r,c:create_clarification_proposal(r,request=req(source_inputs=['../outside-secret']),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('malformed input',lambda r,c:create_clarification_proposal(r,request=req(terms='bad'),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('missing input',lambda r,c:create_clarification_proposal(r,request={k:v for k,v in req().items() if k!='terms'},capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('extra input',lambda r,c:create_clarification_proposal(r,request=req(extra='x'),capability=c,actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
run('capability expansion',lambda r,c:create_clarification_proposal(r,request=req(),capability={**c,'allowed_operations':c['allowed_operations']+['STATE_TRANSITION']},actor_type='human',actor_id='operator-1',timestamp='2026-09-20T10:01:00Z',event_id='evt-x'),True)
