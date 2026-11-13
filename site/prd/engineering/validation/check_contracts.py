from pathlib import Path
import sys,json,copy,hashlib,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'.build/validation-deps'))
import jsonschema,yaml
from openapi_spec_validator import validate_spec
from pglast import parse_sql,ast
C=R/'contracts';load=lambda f:json.loads((C/f).read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError('Nonfinite JSON constant: '+x)))
o=load('openapi.json');validate_spec(o)
api=load('api-contracts.schema.json');w=load('worker-protocol.schema.json');cap=load('capability.schema.json');fc=jsonschema.FormatChecker();cases=[]
def check(name,schema,obj,accepted=True):
 errors=list(jsonschema.Draft202012Validator(schema,format_checker=fc).iter_errors(obj))
 assert bool(errors)!=accepted,(name,[e.message for e in errors[:4]])
 cases.append({'name':name,'expected':'accept'if accepted else'reject','passed':True})
for name,sc in o['components']['schemas'].items():jsonschema.Draft202012Validator.check_schema(sc)
for sc in [api,w,cap]:jsonschema.Draft202012Validator.check_schema(sc)
def api_schema(name):return {'$schema':'https://json-schema.org/draft/2020-12/schema','$ref':'#/$defs/'+name,'$defs':api['$defs']}
for fname,docname,prodname in [('task_spec.example.json','FrozenTaskSpecContractExample','FrozenTaskSpec'),('result_manifest.example.json','ResultManifestContractExample','ResultManifest')]:
 obj=load(fname);check(fname+' document',api_schema(docname),obj);check(fname+' rejected as raw production DTO',api_schema(prodname),obj,False)
 raw={k:v for k,v in obj.items()if k not in ['synthetic','evidence_status']};check(fname+' production shape without document metadata',api_schema(prodname),raw)
for fname in sorted(p.name for p in C.glob('worker-*.example.json')):
 obj=load(fname);check(fname,w,obj)
 bad=copy.deepcopy(obj);bad['role']='owner';check(fname+' unexpected authority field',w,bad,False)
 bad=copy.deepcopy(obj);bad['context']['lease_epoch']=-1;check(fname+' negative fencing epoch',w,bad,False)
 bad=copy.deepcopy(obj);bad['context']['run_id']='not-a-uuid';check(fname+' bad run UUID',w,bad,False)
 bad=copy.deepcopy(obj);bad['context']['lease_epoch']=9007199254740992;check(fname+' unsafe wire integer',w,bad,False)
bad=load('worker-dispatch.example.json');bad['context']['plan_id']=None;bad['context']['frozen_spec_id']=None;bad['context']['step_id']=None
check('scientific dispatch cannot use preflight-null identity',w,bad,False)
for n,obj in enumerate(cap.get('examples',[])):
 check('capability example '+str(n),cap,obj)
 bad=copy.deepcopy(obj);bad['shell']='arbitrary';check('capability rejects arbitrary shell field '+str(n),cap,bad,False)
meta=json.loads((R/'engineering-spec.json').read_text())['api']
for key,typ in [('task_request','TaskRequest'),('create_run','CreateRunRequest'),('request_error','ErrorEnvelope')]:check(key,api_schema(typ),meta['examples'][key])
for ex in meta.get('http_examples',[]):
 check(ex['id']+' request',api_schema(ex['request_schema']),ex['request_body'])
 check(ex['id']+' response',api_schema(ex['response_schema']),ex['response_body'])
for key in ['task_request','create_run']:
 typ='TaskRequest'if key=='task_request'else'CreateRunRequest';bad=copy.deepcopy(meta['examples'][key]);bad['actor_id']='00000000-0000-4000-8000-000000000001';check(key+' cannot self grant actor',api_schema(typ),bad,False)
# Regression for distinct defect/non-defect resolution semantics: do not fabricate fixes.
feedback={'expected_version':1,'status':'RESOLVED','reason':'Contract example: reviewed evidence','evidence_refs':[{'artifact_id':'00000000-0000-4000-8000-000000000001','field_pointer':'/validation'}]}
for resolution in ['NOT_A_DEFECT','DUPLICATE']:
 obj=dict(feedback,resolution_type=resolution);check('feedback '+resolution+' resolves without fabricated fix',api_schema('FeedbackPatch'),obj)
fixed=dict(feedback,resolution_type='FIXED',regression_case_id='regression-001',fix_version='0.1.1');check('feedback FIXED with regression and version',api_schema('FeedbackPatch'),fixed)
check('feedback FIXED rejects missing fix evidence',api_schema('FeedbackPatch'),dict(feedback,resolution_type='FIXED'),False)
check('feedback RESOLVED rejects missing resolution type',api_schema('FeedbackPatch'),feedback,False)
check('feedback resolution rejects absent evidence',api_schema('FeedbackPatch'),dict(feedback,resolution_type='NOT_A_DEFECT',evidence_refs=[]),False)
metrics={'input_tokens','output_tokens','model_calls','cpu_ms','tool_attempts','money_microunits'}
assert set(o['components']['schemas']['BudgetMetric']['enum'])==metrics
assert set(w['$defs']['BudgetRef']['properties']['metric']['enum'])=={'cpu_ms','tool_attempts'}  # CPU child gets only its own reservations; model adapter owns LLM usage.
cfg=yaml.safe_load((R/'ops/config.example.yaml').read_text());assert cfg['runtime']['active_agent_api_enabled']is False and cfg['runtime']['mode']=='design_only';assert cfg['dispatcher']['fencing_field']=='lease_epoch';assert cfg['worker']['network']=='none'
sql=(C/'001_core.sql').read_text();tree=parse_sql(sql);tables=[t.stmt.relation.relname for t in tree if isinstance(t.stmt,ast.CreateStmt)]
assert len(tables)==29 and set(tables)=={x['table']for x in json.loads((R/'engineering-spec.json').read_text())['storage']['tables']}
assert set(['projects','runs','attempts','budget_accounts','budget_reservations','usage_entries','run_queue','feedback_issues'])<=set(tables)
source_sql_validation=load('001_core.validation.json');assert source_sql_validation['sql_sha256']==hashlib.sha256(sql.encode()).hexdigest()
# Validate links against real requirement identifiers; declared routes are docs only.
base=json.loads((R/'requirements.json').read_text());fr={x['id']for x in base['requirements']};ac={x['id']for x in base['acceptance']}
ops=[]
for path,item in o['paths'].items():
 for method,op in item.items():
  if method.lower()not in ['get','post','put','patch','delete','head','options']:continue
  assert set(op['x-requirement-ids'])<=fr and set(op['x-acceptance-ids'])<=ac
  ops.append((method,path))
assert len(ops)==22 and len(set(ops))==22
report={'status':'static_contract_checks_pass','checked_on':'2026-11-04','openapi':{'version':o['openapi'],'operations':len(ops),'schemas':len(o['components']['schemas']),'validation':'openapi-spec-validator + Draft202012 schema checks'},'schema_examples':{'positive_cases':sum(c['expected']=='accept'for c in cases),'negative_cases':sum(c['expected']=='reject'for c in cases),'all_passed':True},'sql':{'parser':'pglast','statements':len(tree),'tables':len(tables),'foreign_keys_checked_by_ast':source_sql_validation['foreign_key_count'],'database_executed':False},'config':{'yaml_parsed':True,'agent_runtime_enabled':False,'contains_credentials':False},'invariants':{'budget_metrics':sorted(metrics),'fencing':'lease_epoch','uuid_format_checks':True,'wire_integer_max':9007199254740991,'fr_ac_references':'resolved'},'not_verified':['PostgreSQL server migration, PL/pgSQL runtime, FK/trigger negative tests, transactions and concurrency','Real API/Worker implementation, authentication, OS isolation and cancellation','LLM planning/repair quality, scientific acceptance of new implementation, performance and provider charges'],'detailed_cases':cases,'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for folder in ['contracts','ops']for p in sorted((R/folder).rglob('*'))if p.is_file()}}
(R/'local_contract_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['files','detailed_cases']},ensure_ascii=False,indent=2))
