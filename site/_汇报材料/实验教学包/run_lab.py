#!/usr/bin/env python3
"""Run one frozen offline teaching configuration. No provider or model API."""
from argparse import ArgumentParser
from pathlib import Path
import hashlib,json
from domain import ROOT
from runner import run_case,versions
from score import score_cases

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.exists():raise SystemExit('Use a new output directory; existing run evidence is immutable.')
    args.output.mkdir(parents=True)
    config=ROOT/'cases.json';cases=json.loads(config.read_text())['cases']
    for case in cases:run_case(case,args.output,ROOT/'assets')
    # Evaluation occurs only after all fixed-policy executions finish.
    key=json.loads((ROOT/'evaluation_key.json').read_text())
    score=score_cases(cases,args.output,ROOT/'assets',key)
    evidence={'label':score['label'],'contains_llm':False,'versions':versions(),
              'configuration_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
              'code_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(ROOT.glob('*.py'))},
              'asset_manifest':json.loads((ROOT/'assets/manifest.json').read_text()),
              'config_scope':'4 actual coordinate operations plus labelled semantic and failure fixtures; one object family',
              'independent_run_count':score['independent_run_count'],'tool_attempt_count':score['tool_attempt_count'],
              'valid_scientific':score['valid_scientific'],'protocol_fixture':score['protocol_fixture'],
              'result_files':{str(f.relative_to(args.output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(args.output.rglob('*')) if f.is_file()}}
    (args.output/'execution_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in evidence.items() if k not in {'result_files','asset_manifest'}},indent=2))

if __name__=='__main__':main()
