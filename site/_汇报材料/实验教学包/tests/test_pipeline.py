from pathlib import Path
import copy,json,shutil,sys,tempfile,unittest
import numpy as np
LAB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(LAB))
from domain import TaskSpec,ContractError,FixedPlanner,Plan,Step,compile_plan,fit,rmsd,inspect
from runner import run_case,Journal
from score import score_cases,InvalidEvaluation
from paired_bootstrap import paired_cluster_bootstrap
from reference import validate

CASES=json.loads((LAB/'cases.json').read_text())['cases']
BY_ID={c['case_id']:c for c in CASES}
KEY=json.loads((LAB/'evaluation_key.json').read_text())

class PipelineTests(unittest.TestCase):
    def run_fixture(self,name):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        output=Path(temp.name)/'run';output.mkdir()
        result=run_case(BY_ID[name],output,LAB/'assets')
        return result,output

    def test_rmsd_reference_known_values(self):
        result,out=self.run_fixture('global')
        self.assertEqual(result['state'],'COMPLETED')
        self.assertAlmostEqual(json.loads((out/'global/result.json').read_text())['metrics'][0]['rmsd'],7.130700222878167,places=7)

    def test_common_rigid_transform_invariance(self):
        rng=np.random.default_rng(17);a=rng.normal(size=(12,3));b=a+rng.normal(scale=.2,size=(12,3))
        r,t=fit(a,b);before=rmsd(a@r+t,b)
        q,_=np.linalg.qr(rng.normal(size=(3,3)))
        if np.linalg.det(q)<0:q[:,0]*=-1
        translated_a=a@q+np.array([100,30,-50]);translated_b=b@q+np.array([100,30,-50])
        r,t=fit(translated_a,translated_b)
        self.assertAlmostEqual(before,rmsd(translated_a@r+t,translated_b),places=10)

    def test_missing_chain_requires_input_unknown_chain_rejected(self):
        self.assertEqual(self.run_fixture('chain_missing')[0]['state'],'NEEDS_INPUT')
        self.assertEqual(self.run_fixture('chain_unknown')[0]['state'],'REJECTED')

    def test_declared_unit_capability_rejects_unsupported(self):
        result,_=self.run_fixture('unit_unsupported')
        self.assertEqual((result['state'],result['reason']),('REJECTED','UNSUPPORTED_UNIT'))

    def test_corrupt_identity_value_and_unit_caught(self):
        for name,code in [('wrong_object','OBJECT_IDENTITY'),('wrong_metric','NUMERIC'),('wrong_unit','UNIT')]:
            with self.subTest(name=name):
                result,out=self.run_fixture('fixture_'+name)
                v=json.loads((out/('fixture_'+name)/'validation.json').read_text())
                self.assertEqual(result['state'],'FAILED');self.assertIn(code,v['failure_codes'])

    def test_duplicate_delivery_does_not_repeat_calculation(self):
        result,out=self.run_fixture('fixture_duplicate_delivery')
        self.assertEqual(result['actual_scientific_calculations'],1)
        self.assertEqual(result['tool_attempt_count'],3)
        events=[json.loads(line) for line in (out/'fixture_duplicate_delivery/events.jsonl').read_text().splitlines()]
        self.assertEqual(sum(e['event']=='DUPLICATE_RESULT_IGNORED' for e in events),1)

    def test_unknown_submission_never_blindly_retried(self):
        result,_=self.run_fixture('fixture_unknown_unresolved')
        self.assertEqual((result['state'],result['simulated_external_submissions'],result['actual_scientific_calculations']),('UNKNOWN',1,0))

    def test_unconfirmed_cancellation_is_not_cancelled(self):
        result,_=self.run_fixture('fixture_cancel_unconfirmed')
        self.assertEqual(result['state'],'CANCEL_REQUESTED')

    def test_frozen_input_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            assets=Path(temp)/'assets';shutil.copytree(LAB/'assets',assets)
            with (assets/'4AKE.cif').open('a') as f:f.write('\n# tampered\n')
            with self.assertRaises(ContractError) as context:inspect(TaskSpec.from_dict(BY_ID['global']['task']),assets)
            self.assertEqual(context.exception.code,'INPUT_IDENTITY')

    def test_plan_rejects_unknown_tools_and_forward_dependencies(self):
        for plan in [Plan(1,(Step('x','unregistered',()),)),Plan(1,(Step('x','inspect_coordinates@1',('later',)),))]:
            with self.assertRaises(ContractError):compile_plan(plan)

    def test_external_scorer_ignores_forged_runtime_pass(self):
        case=BY_ID['fixture_wrong_metric'];result,out=self.run_fixture(case['case_id'])
        file=out/case['case_id']/'validation.json';v=json.loads(file.read_text());v['passed']=True;file.write_text(json.dumps(v))
        summary=out/case['case_id']/'run.json';run=json.loads(summary.read_text());run['state']='COMPLETED';summary.write_text(json.dumps(run))
        scored=score_cases([case],out,LAB/'assets',KEY)
        self.assertFalse(scored['rows'][0]['scientific_pass'])

    def test_immutable_artifact_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            journal=Journal(Path(temp)/'new','test');journal.artifact('x.json',{'v':1},'a')
            with self.assertRaises(RuntimeError):journal.artifact('x.json',{'v':2},'a')

    def test_contact_selection_and_scalar_distance_agree(self):
        result,out=self.run_fixture('ligand_contacts');value=json.loads((out/'ligand_contacts/result.json').read_text())
        self.assertEqual(result['state'],'COMPLETED');self.assertEqual(value['ligand']['heavy_atoms'],57)
        self.assertEqual(len(value['contact_residues']),34)
        self.assertEqual(sum(r['atom_pairs_within_cutoff'] for r in value['contact_residues']),234)

    def test_single_object_bootstrap_refused(self):
        rows=[{'object_group':'adk','task_id':str(t),'repeat_id':0,'system_id':s,'scientific_pass':1} for t in range(4) for s in ['A','B']]
        self.assertEqual(paired_cluster_bootstrap(rows,'A','B')['status'],'insufficient_clusters')

    def test_correct_scalar_with_corrupt_transform_is_rejected(self):
        _,out=self.run_fixture('global')
        result=json.loads((out/'global/result.json').read_text())
        result['metrics'][0]['translation'][0]+=1
        checked=validate(BY_ID['global']['task'],result,LAB/'assets')
        self.assertIn('TRANSFORM_CONSISTENCY',checked['failure_codes'])

    def test_missing_run_keeps_preallocated_row(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            scored=score_cases([BY_ID['global']],out,LAB/'assets',KEY)
            self.assertEqual(scored['independent_run_count'],1)
            self.assertEqual(scored['valid_scientific']['denominator_runs'],1)
            self.assertEqual(scored['rows'][0]['state'],'MISSING_RUN_RECORD')
            self.assertFalse(scored['rows'][0]['scientific_pass'])

    def test_malformed_candidate_keeps_preallocated_row(self):
        for content in ['not json','[]']:
            _,out=self.run_fixture('global')
            (out/'global/result.json').write_text(content)
            scored=score_cases([BY_ID['global']],out,LAB/'assets',KEY)
            self.assertEqual(scored['valid_scientific']['denominator_runs'],1)
            self.assertFalse(scored['rows'][0]['scientific_pass'])

    def test_global_reference_tamper_invalidates_evaluation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'out';out.mkdir();assets=Path(temp)/'assets';shutil.copytree(LAB/'assets',assets)
            with (assets/'4AKE.cif').open('a') as f:f.write('\n# altered\n')
            with self.assertRaises(InvalidEvaluation):score_cases([BY_ID['global']],out,assets,KEY)
            self.assertEqual(json.loads((out/'evaluation_invalid.json').read_text())['status'],'INVALID_EVALUATION')

    def test_boundary_candidate_is_wrong_response_not_oracle_crash(self):
        _,out=self.run_fixture('chain_missing')
        (out/'chain_missing/result.json').write_text('{}')
        scored=score_cases([BY_ID['chain_missing']],out,LAB/'assets',KEY)
        self.assertFalse(scored['rows'][0]['protocol_outcome_matches'])
        self.assertFalse(scored['rows'][0]['scientific_completion'])

    def test_missing_answer_key_invalidates_evaluation(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(InvalidEvaluation):score_cases([BY_ID['global']],Path(temp),LAB/'assets',{})

if __name__=='__main__':unittest.main()
