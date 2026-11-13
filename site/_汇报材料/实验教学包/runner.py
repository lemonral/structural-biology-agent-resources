"""Fixed-policy execution with actual coordinate tools and labelled fault fixtures."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import numpy as np
import Bio
from domain import (TaskSpec, FixedPlanner, ContractError, compile_plan, inspect, mapping_for,
                    calculate, select_contacts, calculate_contacts, canonical_hash)
from reference import validate

class StopRun(Exception):
    def __init__(self,state,reason):self.state,self.reason=state,reason

class Journal:
    def __init__(self,directory:Path,task_id:str):
        directory.mkdir(parents=True,exist_ok=False)
        self.directory,self.task_id,self.sequence=directory,task_id,0
    def event(self,kind:str,**fields):
        self.sequence+=1
        row={'sequence':self.sequence,'time_utc':datetime.now(timezone.utc).isoformat(),
             'run_id':self.task_id,'event':kind,**fields}
        with (self.directory/'events.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
    def artifact(self,name:str,value:dict,attempt_id:str)->dict:
        file=self.directory/name; identity=canonical_hash(value)
        if file.exists():
            if canonical_hash(json.loads(file.read_text()))!=identity:
                raise RuntimeError('Immutable artifact collision')
            self.event('DUPLICATE_RESULT_IGNORED',artifact=name,content_id=identity,attempt_id=attempt_id)
        else:
            file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
            self.event('ARTIFACT_CREATED',artifact=name,content_id=identity,attempt_id=attempt_id)
        return {'filename':name,'content_id':identity,'attempt_id':attempt_id}

def run_case(case:dict,output:Path,assets:Path)->dict:
    directory=output/case['case_id'];journal=Journal(directory,case['case_id'])
    summary={'case_id':case['case_id'],'task_id':case['task']['task_id'],
             'policy':'fixed_teaching_plan@1','contains_llm':False,'fault_fixture':case.get('fault'),
             'attempts':[],'artifacts':{},'state':'CREATED','reason':None,
             'actual_scientific_calculations':0,'simulated_external_submissions':0}
    journal.event('RUN_CREATED',policy=summary['policy'],contains_llm=False)
    active=None
    try:
        task=TaskSpec.from_dict(case['task']);plan=FixedPlanner().propose(task,{})
        compile_plan(plan)
        journal.artifact('task.json',asdict(task),'input')
        journal.artifact('plan.json',asdict(plan),'planner:fixed')
        journal.event('PLAN_COMPILED',version=plan.version)
        chains=identities=selected=None
        for step in plan.steps:
            active={'attempt_id':f"{case['case_id']}:{step.step_id}:1",'step_id':step.step_id,
                    'tool_id':step.tool_id,'state':'RUNNING'}
            summary['attempts'].append(active)
            journal.event('TOOL_STARTED',**active)
            if step.tool_id=='inspect_coordinates@1':
                chains,identities=inspect(task,assets)
                journal.artifact('objects.json',identities,active['attempt_id'])
            elif step.tool_id=='map_residues@1':
                selected=mapping_for(chains)
                journal.event('MAPPING_CHECKED',matched_CA=214,attempt_id=active['attempt_id'])
            elif step.tool_id=='select_contact_atoms@1':
                selected=select_contacts(task,chains)
                journal.event('CONTACT_SELECTION_CHECKED',ligand_heavy_atoms=len(selected['ligand_atoms']),attempt_id=active['attempt_id'])
            else:
                fault=case.get('fault')
                if fault=='simulated_timeout':
                    journal.event('FAULT_INJECTED',fault=fault,simulation=True,attempt_id=active['attempt_id'])
                    raise StopRun('FAILED','SIMULATED_TIMEOUT')
                if fault in {'unknown_reconciled','unknown_unresolved','cancel_unconfirmed'}:
                    summary['simulated_external_submissions']=1
                    journal.event('SIMULATED_SUBMISSION',operation_id=active['attempt_id'],simulation=True)
                    journal.event('SUBMIT_ACK_LOST',state='UNKNOWN',simulation=True)
                    if fault=='unknown_unresolved':
                        journal.event('RECONCILIATION_UNRESOLVED',simulation=True,resubmit=False)
                        raise StopRun('UNKNOWN','No unique external fact; no blind resubmission')
                    if fault=='cancel_unconfirmed':
                        journal.event('CANCEL_REQUESTED',simulation=True,confirmed=False)
                        raise StopRun('CANCEL_REQUESTED','Cancellation is requested, not confirmed')
                    journal.event('JOB_RECONCILED',simulation=True,job_id='simulated-job-1',unique_match=True,resubmit=False)
                result=(calculate_contacts(task,selected,identities) if task.mode=='contacts' else calculate(task,selected,identities))
                summary['actual_scientific_calculations']+=1
                if fault=='wrong_object':
                    result['objects']['reference']['chain']='B'
                elif fault=='wrong_metric':result['metrics'][0]['rmsd']+=1
                elif fault=='wrong_unit':result['units']='nm'
                if fault in {'wrong_object','wrong_metric','wrong_unit'}:
                    journal.event('FAULT_INJECTED',fault=fault,simulation=True,attempt_id=active['attempt_id'])
                summary['artifacts']['result']=journal.artifact('result.json',result,active['attempt_id'])
                if fault=='duplicate_delivery':
                    journal.event('FAULT_INJECTED',fault=fault,simulation=True)
                    journal.artifact('result.json',result,active['attempt_id'])
                verification=validate(asdict(task),result,assets)
                summary['artifacts']['validation']=journal.artifact('validation.json',verification,'validator:1')
                journal.event('RESULT_VALIDATED',passed=verification['passed'],failure_codes=verification['failure_codes'])
                if not verification['passed']:raise StopRun('FAILED','SCIENTIFIC_VALIDATION')
            active['state']='COMPLETED';journal.event('TOOL_COMPLETED',**active)
        summary['state']='COMPLETED'
    except ContractError as error:
        summary['state'],summary['reason']=error.state,error.code
        if active:active['state']='REJECTED'
        journal.event('CONTRACT_RESPONSE',state=error.state,code=error.code,detail=str(error))
    except StopRun as error:
        summary['state'],summary['reason']=error.state,error.reason
        if active:active['state']=error.state
        journal.event('RUN_STOPPED',state=error.state,reason=error.reason)
    except Exception as error:
        summary['state'],summary['reason']='FAILED',type(error).__name__+': '+str(error)
        if active:active['state']='FAILED'
        journal.event('UNEXPECTED_FAILURE',detail=summary['reason'])
    summary['tool_attempt_count']=len(summary['attempts'])
    journal.event('RUN_FINISHED',state=summary['state'],tool_attempt_count=len(summary['attempts']))
    (directory/'run.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary

def versions()->dict:
    return {'python':platform.python_version(),'numpy':np.__version__,'biopython':Bio.__version__}
