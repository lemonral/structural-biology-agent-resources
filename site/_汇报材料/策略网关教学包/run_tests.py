#!/usr/bin/env python3
"""Run real unittest cases and record evidence without subprocess dependencies."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import platform
import unittest
from run_policy_lab import run_cases

ROOT = Path(__file__).resolve().parent


def main():
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    cases, _ = run_cases()
    evidence = {'generated_at': datetime.now(timezone.utc).isoformat(),
                'runtime': {'python': platform.python_version(), 'standard_library_only': True},
                'command': 'python3 run_tests.py',
                'unittest': {'tests_run': result.testsRun, 'failures': len(result.failures),
                             'errors': len(result.errors), 'skipped': len(result.skipped),
                             'successful': result.wasSuccessful()},
                'scenario_checks': {'total': len(cases), 'passed': sum(c['passed'] for c in cases)},
                'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(ROOT.rglob('*.py'))},
                'output': stream.getvalue(),
                'claim_boundary': 'Fixture and single-process unit evidence only; no model, scientific computation, file executor, production authentication, OS sandbox or multi-worker persistence was tested.'}
    (ROOT/'test_evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(stream.getvalue(), end='')
    return 0 if result.wasSuccessful() and all(c['passed'] for c in cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())
