"""External scoring. It rechecks result files; runtime's 'passed' is not truth."""
from pathlib import Path
import hashlib,json,math
from reference import validate

class InvalidEvaluation(RuntimeError):
    """The reference/configuration is invalid; do not assign an Agent error."""

def check_evaluation_inputs(cases,assets,answer_key):
    registry=json.loads((assets/'manifest.json').read_text())['files']
    for name,record in registry.items():
        file=assets/record['filename']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=record['sha256']:
            raise InvalidEvaluation('Frozen evaluation input unavailable or changed: '+name)
    for case in cases:
        if case['case_id'] not in answer_key:
            raise InvalidEvaluation('Missing answer-key row: '+case['case_id'])
        if not {'stratum','expected_state','object_cluster'} <= set(answer_key[case['case_id']]):
            raise InvalidEvaluation('Incomplete answer-key row: '+case['case_id'])

def readable_candidate(task,result):
    """Reject unsafe JSON shapes before the numerical oracle; do not catch oracle faults."""
    if not isinstance(result,dict):return False
    if task['mode']=='contacts':
        rows=result.get('contact_residues')
        return (isinstance(rows,list) and all(isinstance(r,dict) and isinstance(r.get('auth_residue'),int)
                and isinstance(r.get('resname'),str) for r in rows))
    mapping=result.get('mapping');metrics=result.get('metrics')
    if not isinstance(mapping,list) or not all(isinstance(r,dict) and isinstance(r.get('auth_residue'),int) for r in mapping):return False
    if not isinstance(metrics,list):return False
    for m in metrics:
        if not isinstance(m,dict) or not isinstance(m.get('fit_region'),str) or not isinstance(m.get('evaluation_region'),str):return False
        rot=m.get('rotation_row_vector');tran=m.get('translation')
        numeric=lambda value:type(value) in {int,float} and math.isfinite(value)
        if not isinstance(rot,list) or len(rot)!=3 or not all(isinstance(row,list) and len(row)==3 and all(numeric(v) for v in row) for row in rot):return False
        if not isinstance(tran,list) or len(tran)!=3 or not all(numeric(v) for v in tran):return False
    return True

def score_cases(cases:list[dict],output:Path,assets:Path,answer_key:dict)->dict:
    try:
        check_evaluation_inputs(cases,assets,answer_key)
    except (InvalidEvaluation,FileNotFoundError,KeyError,json.JSONDecodeError) as error:
        (output/'evaluation_invalid.json').write_text(json.dumps({'status':'INVALID_EVALUATION','reason':str(error)},indent=2)+'\n')
        raise InvalidEvaluation(str(error)) from error
    rows=[]
    for case in cases:
        key=answer_key[case['case_id']]
        errors=[]
        runfile=output/case['case_id']/'run.json'
        try:
            run=json.loads(runfile.read_text())
            if not isinstance(run,dict) or not isinstance(run.get('state'),str):
                raise ValueError('Run must contain a state')
        except FileNotFoundError:
            run={'state':'MISSING_RUN_RECORD'};errors.append('MISSING_RUN_RECORD')
        except (json.JSONDecodeError,ValueError):
            run={'state':'INVALID_RUN_RECORD'};errors.append('INVALID_RUN_RECORD')
        scientific_pass=False if key['stratum']=='valid_scientific' else None
        candidate=output/case['case_id']/'result.json'
        if candidate.exists():
            if key['stratum'] in {'ambiguous_input','invalid_or_unsupported'}:
                scientific_pass=False;errors.append('UNEXPECTED_SCIENTIFIC_OUTPUT_FOR_BOUNDARY_CASE')
            else:
                try:
                    result=json.loads(candidate.read_text())
                except json.JSONDecodeError:
                    result=None;errors.append('INVALID_RESULT_JSON')
                if not readable_candidate(case['task'],result):
                    scientific_pass=False;errors.append('INVALID_RESULT_SHAPE')
                else:
                    # Environmental/oracle exceptions propagate, never counted as model failure.
                    scientific_pass=validate(case['task'],result,assets)['passed']
        elif key['stratum']=='valid_scientific':errors.append('MISSING_RESULT')
        attempts=run.get('tool_attempt_count')
        if type(attempts) is not int or attempts<0:
            attempts=None;errors.append('MISSING_OR_INVALID_ATTEMPT_COST')
        rows.append({'case_id':case['case_id'],'object_cluster':key['object_cluster'],'stratum':key['stratum'],
                     'state':run['state'],'expected_state':key['expected_state'],
                     'protocol_outcome_matches':run['state']==key['expected_state'] and 'UNEXPECTED_SCIENTIFIC_OUTPUT_FOR_BOUNDARY_CASE' not in errors,
                     'scientific_pass':scientific_pass,
                     'scientific_completion':run['state']=='COMPLETED' and scientific_pass is True,
                     'tool_attempt_count':attempts,
                     'actual_scientific_calculations':run.get('actual_scientific_calculations'),
                     'simulated_external_submissions':run.get('simulated_external_submissions'),
                     'scoring_errors':errors})
    ordinary=[r for r in rows if r['stratum']=='valid_scientific']
    summary={'label':'OFFLINE_FIXED_POLICY_TEACHING_ONLY_NOT_AGENT_PERFORMANCE',
             'independent_run_count':len(rows),'tool_attempt_count':sum(r['tool_attempt_count'] or 0 for r in rows),
             'attempt_cost_records_available':sum(r['tool_attempt_count'] is not None for r in rows),
             'attempt_cost_records_required':len(rows),
             'valid_scientific':{'denominator_runs':len(ordinary),
                                 'numerator_scientific_completions':sum(r['state']=='COMPLETED' and r['scientific_pass'] is True for r in ordinary)},
             'protocol_fixture':{'denominator_runs':len(rows)-len(ordinary),
                                 'outcomes_matching_predeclared_protocol':sum(r['protocol_outcome_matches'] for r in rows if r not in ordinary)},
             'object_cluster_count':len({r['object_cluster'] for r in rows}),
             'generalization_interval':'insufficient_clusters; all cases derive from one AdK object family',
             'external_scoring_boundary':'Answer key is absent from runner imports. Runtime validator and scorer share validate(), so this lab does NOT establish independent evaluation validity.',
             'rows':rows}
    (output/'scores.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary
