"""Self-created temporary objects only: no real structures, secrets or services."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from gateway import Action, ApprovalAuthority, Gateway, RunScope

OPERATIONS = frozenset({'inspect_structure', 'rmsd', 'contacts', 'analyze_batch',
                        'write_report', 'export_report'})


class Fixture:
    def __init__(self, hard_units=12, threshold=5):
        self.temp = TemporaryDirectory(prefix='policy-lab-')
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'authorized'
        self.outside = self.base / 'outside'
        self.root.mkdir()
        self.outside.mkdir()
        (self.root / 'exists.json').write_text('{}', encoding='utf-8')
        (self.root / 'outside_link').symlink_to(self.outside, target_is_directory=True)
        (self.root / 'inside_link').symlink_to(self.root, target_is_directory=True)
        self.scope = RunScope('run-demo-001', self.root, OPERATIONS,
                              frozenset({'adk_open', 'adk_closed', 'adk_third'}),
                              frozenset({'metrics_01'}),
                              frozenset({'project-review-vault'}), hard_units, threshold)
        self.now = [1000.0]
        self.authority = ApprovalAuthority(clock=lambda: self.now[0])
        self.gateway = Gateway(self.scope, self.authority)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.temp.cleanup()

    def gateway_for(self, **scope_changes):
        return Gateway(replace(self.scope, **scope_changes), self.authority)


def inspect():
    return Action('inspect_structure', {'object_id': 'adk_open'})


def write(path='results/report.json'):
    return Action('write_report', {'artifact_id': 'metrics_01', 'output_path': path})


def batch(count=2):
    return Action('analyze_batch', {'object_ids': ['adk_open', 'adk_closed', 'adk_third'][:count]})


def rmsd():
    return Action('rmsd', {'reference_id': 'adk_open', 'moving_id': 'adk_closed',
                         'fit_region': 'CORE', 'units': 'angstrom'})


def contacts(cutoff=4.0):
    return Action('contacts', {'object_id': 'adk_open', 'cutoff_A': cutoff})
