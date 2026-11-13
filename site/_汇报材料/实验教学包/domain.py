"""Frozen coordinate contract and a deterministic scientific capability.

This module contains no language model, API client or credentials.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol
import json
import numpy as np
from Bio.PDB import MMCIFParser

ROOT = Path(__file__).resolve().parent
REGIONS = {
    'ALL': list(range(1, 215)),
    'CORE': list(range(1, 30)) + list(range(60, 122)) + list(range(160, 215)),
    'NMP': list(range(30, 60)),
    'LID': list(range(122, 160)),
}
TOOLS = {'inspect_coordinates@1', 'map_residues@1', 'calculate_rmsd@1', 'select_contact_atoms@1', 'calculate_contacts@1'}

def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()

def canonical_hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class ContractError(ValueError):
    def __init__(self, code: str, message: str, state: str = 'REJECTED'):
        super().__init__(message)
        self.code, self.state = code, state

@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    question: str
    reference: str
    moving: str | None
    chain: str | None
    mode: str
    units: str = 'angstrom'
    model_index: int = 0
    mapping: str = 'same_auth_residue_and_name'
    region_policy: str = 'MDAnalysis_AdK_tutorial_v1'
    ligand: str = 'AP5'
    cutoff_A: float = 4.0

    @classmethod
    def from_dict(cls, obj: dict) -> 'TaskSpec':
        allowed = set(cls.__dataclass_fields__)
        if set(obj) - allowed:
            raise ContractError('UNKNOWN_FIELD', 'Unexpected task fields')
        try:
            task = cls(**obj)
        except TypeError as error:
            raise ContractError('SCHEMA', str(error)) from error
        for key in ['task_id', 'question', 'reference', 'mode', 'units', 'mapping', 'region_policy','ligand']:
            if not isinstance(getattr(task, key), str) or not getattr(task, key):
                raise ContractError('SCHEMA', f'{key} must be a nonempty string')
        if task.chain is not None and not isinstance(task.chain, str):
            raise ContractError('SCHEMA', 'chain must be string or null')
        if type(task.model_index) is not int:
            raise ContractError('SCHEMA', 'model_index must be integer')
        if task.moving is not None and not isinstance(task.moving,str):
            raise ContractError('SCHEMA', 'moving must be string or null')
        if type(task.cutoff_A) not in {int,float} or not np.isfinite(task.cutoff_A) or task.cutoff_A<=0:
            raise ContractError('SCHEMA', 'cutoff must be a positive finite number')
        return task

@dataclass(frozen=True)
class Step:
    step_id: str
    tool_id: str
    depends_on: tuple[str, ...]

@dataclass(frozen=True)
class Plan:
    version: int
    steps: tuple[Step, ...]

class Planner(Protocol):
    """Future model planners must propose Plan; Executor never trusts raw shell."""
    def propose(self, task: TaskSpec, observations: dict) -> Plan: ...

class FixedPlanner:
    """Teaching baseline. This is hand-written control, not an Agent."""
    def propose(self, task: TaskSpec, observations: dict) -> Plan:
        if task.mode=='contacts':
            return Plan(1,(Step('inspect','inspect_coordinates@1',()),Step('selection','select_contact_atoms@1',('inspect',)),Step('measure','calculate_contacts@1',('selection',))))
        return Plan(1, (Step('inspect', 'inspect_coordinates@1', ()),
                        Step('mapping', 'map_residues@1', ('inspect',)),
                        Step('measure', 'calculate_rmsd@1', ('mapping',))))

def compile_plan(plan: Plan) -> None:
    if len({step.step_id for step in plan.steps}) != len(plan.steps):
        raise ContractError('PLAN_DUPLICATE', 'Step identifiers must be unique')
    seen = set()
    for step in plan.steps:
        if step.tool_id not in TOOLS:
            raise ContractError('PLAN_TOOL', 'Unregistered tool')
        # Requiring topological order rejects cycles and unavailable dependencies.
        if not set(step.depends_on) <= seen:
            raise ContractError('PLAN_DEPENDENCY', 'Missing, forward or cyclic dependency')
        seen.add(step.step_id)
    if [s.tool_id for s in plan.steps] not in [
        ['inspect_coordinates@1', 'map_residues@1', 'calculate_rmsd@1'],
        ['inspect_coordinates@1', 'select_contact_atoms@1', 'calculate_contacts@1']]:
        raise ContractError('PLAN_SCOPE', 'This capability supports one declared pipeline')

def inspect(task: TaskSpec, asset_root: Path = ROOT/'assets') -> tuple[dict, dict]:
    if task.mode not in {'global', 'local', 'core_reference','contacts'}:
        raise ContractError('UNSUPPORTED_OPERATION', 'Supported modes: global/local/core_reference/contacts')
    if task.mode!='contacts' and not task.moving:
        raise ContractError('MISSING_INPUT','Comparisons need a moving structure')
    if task.mode=='contacts' and task.moving is not None:
        raise ContractError('UNARY_OPERATION','Contact calculation takes one structure; moving must be null')
    if task.units != 'angstrom':
        raise ContractError('UNSUPPORTED_UNIT', 'This capability only emits angstrom; nm itself is a valid unit')
    if task.model_index != 0 or task.mapping != 'same_auth_residue_and_name':
        raise ContractError('UNSUPPORTED_OBJECT_POLICY', 'Only frozen first-model, same-ID mapping is implemented')
    if task.region_policy != 'MDAnalysis_AdK_tutorial_v1':
        raise ContractError('UNSUPPORTED_REGION_POLICY', 'Region definition must be the registered AdK policy')
    manifest = json.loads((asset_root/'manifest.json').read_text())
    structures, identities = {}, {}
    parser = MMCIFParser(QUIET=True, auth_chains=True, auth_residues=True)
    for role in (['reference'] if task.mode=='contacts' else ['reference', 'moving']):
        name = getattr(task, role)
        if name not in manifest['files']:
            raise ContractError('MISSING_INPUT', 'Input is absent from the frozen asset registry')
        file = asset_root/manifest['files'][name]['filename']
        if not file.is_file() or digest(file) != manifest['files'][name]['sha256']:
            raise ContractError('INPUT_IDENTITY', 'Input bytes differ from the frozen registry')
        structure = parser.get_structure(name, str(file))
        model = structure[0]
        available = sorted(ch.id for ch in model if any(r.id[0] == ' ' and 'CA' in r for r in ch))
        if task.chain is None or task.chain == '':
            raise ContractError('CHAIN_REQUIRED', f'Choose auth chain from {available}', 'NEEDS_INPUT')
        if task.chain not in available:
            raise ContractError('UNKNOWN_CHAIN', f'Requested auth chain is not in {available}')
        structures[role] = model[task.chain]
        identities[role] = {'entry': name, 'sha256': digest(file), 'model_index': 0,
                            'chain_namespace': 'auth', 'chain': task.chain, 'atom': 'heavy' if task.mode=='contacts' else 'CA'}
    return structures, identities

def select_contacts(task: TaskSpec, chains: dict) -> dict:
    chain=chains['reference']
    ligands=[r for r in chain if r.resname==task.ligand]
    if len(ligands)!=1:
        raise ContractError('LIGAND_IDENTITY','Expected exactly one named ligand in selected auth chain')
    heavy=lambda r:[a for a in r if a.element.strip().upper() not in {'H','D'}]
    protein=[(r.id[1],r.resname,heavy(r)) for r in chain if r.id[0]==' ']
    return {'protein':protein,'ligand':ligands[0],'ligand_atoms':heavy(ligands[0])}

def calculate_contacts(task: TaskSpec, selected: dict, identities: dict) -> dict:
    ligand=np.array([a.coord for a in selected['ligand_atoms']],dtype=float)
    rows=[]
    for number,name,atoms in selected['protein']:
        if not atoms: continue
        protein=np.array([a.coord for a in atoms],dtype=float)
        distance=np.linalg.norm(protein[:,None,:]-ligand[None,:,:],axis=2)
        if distance.min()<=task.cutoff_A:
            rows.append({'auth_residue':number,'resname':name,'min_distance':float(distance.min()),
                         'atom_pairs_within_cutoff':int(np.sum(distance<=task.cutoff_A))})
    return {'schema':'contact-result.v1','task_id':task.task_id,'objects':identities,'units':'angstrom',
            'method':'heavy_atom_Euclidean_distance_inclusive_cutoff@1','cutoff_A':task.cutoff_A,
            'ligand':{'name':task.ligand,'auth_residue':selected['ligand'].id[1],'chain':task.chain,
                      'heavy_atoms':len(selected['ligand_atoms'])},'contact_residues':rows,
            'interpretation_limit':'Geometric contact under a declared cutoff, not binding affinity or causal functional evidence.'}

def mapping_for(chains: dict) -> dict:
    selected = {}
    for role, chain in chains.items():
        residues = {}
        for residue in chain:
            if residue.id[0] != ' ' or 'CA' not in residue:
                continue
            if residue.id[2].strip():
                raise ContractError('INSERTION_UNSUPPORTED', 'This teaching capability excludes insertion codes')
            residues[residue.id[1]] = residue
        selected[role] = residues
    ids = sorted(set(selected['reference']) & set(selected['moving']))
    if ids != REGIONS['ALL']:
        raise ContractError('COVERAGE', 'Frozen AdK example expects residues 1..214; no silent intersection trimming')
    if any(selected['reference'][i].resname != selected['moving'][i].resname for i in ids):
        raise ContractError('MAPPING', 'Residue names disagree under same-ID mapping')
    return selected

def fit(moving: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cm, cr = moving.mean(0), reference.mean(0)
    u, _, vt = np.linalg.svd((moving-cm).T @ (reference-cr))
    d = np.eye(3); d[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ d @ vt
    return rotation, cr-cm @ rotation

def rmsd(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.sum((a-b)**2, axis=1))))

def calculate(task: TaskSpec, selected: dict, identities: dict) -> dict:
    xyz = {role: np.array([selected[role][i]['CA'].coord for i in REGIONS['ALL']], dtype=np.float64)
           for role in ['reference', 'moving']}
    fit_names = ['ALL'] if task.mode == 'global' else ['CORE', 'NMP', 'LID'] if task.mode == 'local' else ['CORE']
    metrics = []
    for fit_name in fit_names:
        ix = np.array(REGIONS[fit_name])-1
        rotation, translation = fit(xyz['moving'][ix], xyz['reference'][ix])
        aligned = xyz['moving'] @ rotation + translation
        evaluate = ['ALL'] if task.mode == 'global' else [fit_name] if task.mode == 'local' else ['CORE', 'NMP', 'LID']
        for region in evaluate:
            ev = np.array(REGIONS[region])-1
            metrics.append({'fit_region': fit_name, 'evaluation_region': region, 'matched_atoms': len(ev),
                            'rmsd': rmsd(aligned[ev], xyz['reference'][ev]),
                            'rotation_row_vector': rotation.tolist(), 'translation': translation.tolist()})
    return {'schema': 'coordinate-result.v1', 'task_id': task.task_id, 'objects': identities,
            'units': 'angstrom', 'method': 'Kabsch_SVD_right_handed_no_trimming@1',
            'region_policy': task.region_policy, 'region_residue_ids': REGIONS,
            'mapping': [{'auth_residue': i, 'resname': selected['reference'][i].resname, 'atom': 'CA'} for i in REGIONS['ALL']],
            'metrics': metrics,
            'interpretation_limit': 'Static coordinate geometry only; no transition kinetics, free energy or ligand causality.'}
