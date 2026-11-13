"""Independent result recomputation through a separate atom-table parser.

The oracle does NOT import runtime selection, domain arrays or Kabsch code.
It shares mmCIF input and Bio.PDB infrastructure; that limitation is disclosed.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json
import numpy as np
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.SVDSuperimposer import SVDSuperimposer

def reference_coordinates(file: Path, auth_chain: str) -> dict:
    atom = MMCIF2Dict(str(file))
    first_model = atom['_atom_site.pdbx_PDB_model_num'][0]
    choice = {}
    for i, name in enumerate(atom['_atom_site.label_atom_id']):
        if name != 'CA' or atom['_atom_site.group_PDB'][i] != 'ATOM': continue
        if atom['_atom_site.auth_asym_id'][i] != auth_chain: continue
        if atom['_atom_site.pdbx_PDB_model_num'][i] != first_model: continue
        if atom['_atom_site.pdbx_PDB_ins_code'][i] not in {'.', '?'}:
            raise ValueError('Insertion codes are outside this frozen reference')
        residue = int(atom['_atom_site.auth_seq_id'][i])
        xyz = np.array([float(atom[key][i]) for key in ['_atom_site.Cartn_x','_atom_site.Cartn_y','_atom_site.Cartn_z']])
        occupancy = float(atom['_atom_site.occupancy'][i])
        # Highest occupancy, first record on ties, matching the published policy.
        if residue not in choice or occupancy > choice[residue][2]:
            choice[residue] = (atom['_atom_site.auth_comp_id'][i], xyz, occupancy)
    if set(choice) != set(range(1, 215)): raise ValueError('Reference coverage differs')
    return choice

def oracle(task: dict, asset_root: Path) -> dict:
    registry = json.loads((asset_root/'manifest.json').read_text())['files']
    obj, coords = {}, {}
    for role in ['reference', 'moving']:
        file = asset_root/registry[task[role]]['filename']
        sha = sha256(file.read_bytes()).hexdigest()
        if sha != registry[task[role]]['sha256']: raise ValueError('Reference input hash differs')
        coords[role] = reference_coordinates(file, task['chain'])
        obj[role] = {'entry': task[role], 'sha256': sha, 'model_index': 0, 'chain_namespace': 'auth',
                     'chain': task['chain'], 'atom': 'CA'}
    if any(coords['moving'][i][0] != coords['reference'][i][0] for i in range(1,215)):
        raise ValueError('Reference sequence correspondence disagrees')
    regions = {'ALL': list(range(1,215)), 'CORE': list(range(1,30))+list(range(60,122))+list(range(160,215)),
               'NMP': list(range(30,60)), 'LID': list(range(122,160))}
    x = {r: np.array([coords[r][i][1] for i in range(1,215)]) for r in coords}
    fits = ['ALL'] if task['mode']=='global' else ['CORE','NMP','LID'] if task['mode']=='local' else ['CORE']
    metrics = {}
    for f in fits:
        fit_indices = np.array(regions[f])-1
        superimposer = SVDSuperimposer(); superimposer.set(x['reference'][fit_indices], x['moving'][fit_indices]); superimposer.run()
        rot, tran = superimposer.get_rotran()
        transformed = x['moving'] @ rot + tran
        es = ['ALL'] if task['mode']=='global' else [f] if task['mode']=='local' else ['CORE','NMP','LID']
        for e in es:
            ix = np.array(regions[e])-1
            metrics[(f,e)] = {'rmsd': float(np.linalg.norm(transformed[ix]-x['reference'][ix])/np.sqrt(len(ix))), 'n': len(ix)}
    return {'objects': obj, 'metrics': metrics, 'regions': regions}

def validate(task: dict, result: dict, asset_root: Path, tolerance: float=1e-5) -> dict:
    """Check real candidate output; tolerances do not define biological quality."""
    reasons = []
    if task['mode']=='contacts': return validate_contacts(task,result,asset_root,tolerance)
    expected = oracle(task, asset_root)
    if result.get('schema') != 'coordinate-result.v1': reasons.append('SCHEMA')
    if result.get('task_id') != task['task_id']: reasons.append('TASK_IDENTITY')
    if result.get('objects') != expected['objects']: reasons.append('OBJECT_IDENTITY')
    if result.get('units') != 'angstrom': reasons.append('UNIT')
    if result.get('method') != 'Kabsch_SVD_right_handed_no_trimming@1': reasons.append('METHOD')
    if result.get('region_policy') != 'MDAnalysis_AdK_tutorial_v1': reasons.append('REGION_POLICY')
    if result.get('region_residue_ids') != expected['regions']: reasons.append('REGION_SELECTION')
    mapping = result.get('mapping', [])
    if [r.get('auth_residue') for r in mapping] != list(range(1,215)) or any(r.get('atom')!='CA' for r in mapping):
        reasons.append('ATOM_MAPPING')
    # The mapping names are checked against a separately parsed reference table.
    table = reference_coordinates(asset_root/(task['reference']+'.cif'),task['chain'])
    if len(mapping)!=214 or any(r.get('resname') != table.get(r.get('auth_residue'),[None])[0] for r in mapping):
        reasons.append('RESIDUE_MAPPING')
    actual = {(m.get('fit_region'),m.get('evaluation_region')):m for m in result.get('metrics',[])}
    if set(actual)!=set(expected['metrics']) or len(actual)!=len(result.get('metrics',[])):
        reasons.append('METRIC_SELECTION')
    for key, reference in expected['metrics'].items():
        if key not in actual: continue
        candidate = actual[key]
        value = candidate.get('rmsd')
        if not isinstance(value,(int,float)) or not np.isfinite(value) or abs(value-reference['rmsd'])>tolerance:
            reasons.append('NUMERIC')
        if candidate.get('matched_atoms') != reference['n']: reasons.append('COVERAGE')
        rotation = np.array(candidate.get('rotation_row_vector',[]))
        if rotation.shape!=(3,3) or not np.allclose(rotation.T@rotation,np.eye(3),atol=1e-7) or not np.isclose(np.linalg.det(rotation),1,atol=1e-7):
            reasons.append('ROTATION')
        translation=np.array(candidate.get('translation',[]))
        if rotation.shape==(3,3) and translation.shape==(3,) and np.all(np.isfinite(translation)):
            cr=reference_coordinates(asset_root/(task['reference']+'.cif'),task['chain'])
            cm=reference_coordinates(asset_root/(task['moving']+'.cif'),task['chain'])
            ix=expected['regions'][key[1]]
            a=np.array([cm[i][1] for i in ix])@rotation+translation
            b=np.array([cr[i][1] for i in ix])
            transform_rmsd=float(np.linalg.norm(a-b)/np.sqrt(len(ix)))
            if not np.isfinite(transform_rmsd) or not isinstance(value,(int,float)) or abs(transform_rmsd-value)>tolerance:
                reasons.append('TRANSFORM_CONSISTENCY')
        else: reasons.append('TRANSLATION')
    return {'passed':not reasons,'failure_codes':sorted(set(reasons)),'numeric_tolerance_A':tolerance,
            'reference_implementation':'MMCIF2Dict atom-table + Bio.SVDSuperimposer',
            'independence_limit':'Separate selection and transform code, shared input files, mmCIF conventions and Bio.PDB dependency. Expert object review remains necessary.'}

def validate_contacts(task:dict,result:dict,asset_root:Path,tolerance:float)->dict:
    file=asset_root/(task['reference']+'.cif')
    registry=json.loads((asset_root/'manifest.json').read_text())['files'][task['reference']]
    if sha256(file.read_bytes()).hexdigest()!=registry['sha256']:raise ValueError('Reference file changed')
    atom=MMCIF2Dict(str(file)); chosen={}; model=atom['_atom_site.pdbx_PDB_model_num'][0]
    for i,symbol in enumerate(atom['_atom_site.type_symbol']):
        if symbol.upper() in {'H','D'} or atom['_atom_site.auth_asym_id'][i]!=task['chain']:continue
        if atom['_atom_site.pdbx_PDB_model_num'][i]!=model:continue
        name=atom['_atom_site.auth_comp_id'][i]
        if atom['_atom_site.group_PDB'][i]!='ATOM' and name!=task['ligand']:continue
        num=int(atom['_atom_site.auth_seq_id'][i]); key=(num,name,atom['_atom_site.auth_atom_id'][i]);occ=float(atom['_atom_site.occupancy'][i])
        xyz=np.array([float(atom[k][i]) for k in ['_atom_site.Cartn_x','_atom_site.Cartn_y','_atom_site.Cartn_z']])
        if key not in chosen or occ>chosen[key][1]:chosen[key]=(xyz,occ)
    ligand={k:v[0] for k,v in chosen.items() if k[1]==task['ligand']}
    protein={k:v[0] for k,v in chosen.items() if k[1]!=task['ligand']}
    expected={}
    # Deliberately use scalar pair iteration, distinct from runtime broadcasting.
    for (resnum,resname,_),xyz in protein.items():
        for other in ligand.values():
            distance=float(np.sqrt(sum((float(a)-float(b))**2 for a,b in zip(xyz,other))))
            if distance<=task['cutoff_A']:
                row=expected.setdefault((resnum,resname),{'min_distance':distance,'atom_pairs_within_cutoff':0})
                row['min_distance']=min(row['min_distance'],distance);row['atom_pairs_within_cutoff']+=1
    reasons=[]
    obj={'reference':{'entry':task['reference'],'sha256':registry['sha256'],'model_index':0,'chain_namespace':'auth','chain':task['chain'],'atom':'heavy'}}
    if result.get('objects')!=obj:reasons.append('OBJECT_IDENTITY')
    if result.get('task_id')!=task['task_id'] or result.get('schema')!='contact-result.v1':reasons.append('SCHEMA')
    if result.get('units')!='angstrom':reasons.append('UNIT')
    if result.get('method')!='heavy_atom_Euclidean_distance_inclusive_cutoff@1':reasons.append('METHOD')
    if result.get('cutoff_A')!=task['cutoff_A']:reasons.append('CUTOFF')
    target={'name':task['ligand'],'auth_residue':next(iter(ligand))[0],'chain':task['chain'],'heavy_atoms':len(ligand)}
    if result.get('ligand')!=target:reasons.append('LIGAND_IDENTITY')
    actual={(r.get('auth_residue'),r.get('resname')):r for r in result.get('contact_residues',[])}
    if set(actual)!=set(expected) or len(actual)!=len(result.get('contact_residues',[])):reasons.append('CONTACT_SET')
    for key,row in expected.items():
        if key not in actual:continue
        val=actual[key].get('min_distance')
        if not isinstance(val,(int,float)) or not np.isfinite(val) or abs(val-row['min_distance'])>tolerance:reasons.append('NUMERIC')
        if actual[key].get('atom_pairs_within_cutoff')!=row['atom_pairs_within_cutoff']:reasons.append('PAIR_COUNT')
    return {'passed':not reasons,'failure_codes':sorted(set(reasons)),'numeric_tolerance_A':tolerance,
            'reference_implementation':'mmCIF atom-table + scalar Euclidean pairs',
            'independence_limit':'Shares mmCIF semantics, input files and region/object assumptions. Geometric contact does not validate affinity.'}
