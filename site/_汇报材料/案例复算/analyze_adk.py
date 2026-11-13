"""Reproducible coordinate example. This is an analysis, not an Agent run."""
from pathlib import Path
import json, hashlib, sys
import numpy as np
import Bio
from Bio.PDB import MMCIFParser, Superimposer
from Bio.SeqUtils import seq1

B=Path(__file__).resolve().parent
parser=MMCIFParser(QUIET=True, auth_chains=True, auth_residues=True)
chains={c:parser.get_structure(c,str(B/'assets'/f'{c}.cif'))[0]['A'] for c in ['4AKE','1AKE']}
def selected(chain):
    return {r.id[1]:r for r in chain if r.id[0]==' ' and 'CA' in r}
res={c:selected(ch) for c,ch in chains.items()}
ids=sorted(res['4AKE'].keys()&res['1AKE'].keys())
assert ids==list(range(1,215))
assert all(res['4AKE'][i].resname==res['1AKE'][i].resname for i in ids)
xyz={c:np.array([res[c][i]['CA'].coord for i in ids],dtype=np.float64) for c in res}
regions={'ALL':ids,'CORE':[i for i in ids if i<=29 or 60<=i<=121 or i>=160], 'NMP':list(range(30,60)), 'LID':list(range(122,160))}
def fit(moving,target):
    mc=moving.mean(0);tc=target.mean(0)
    U,S,Vt=np.linalg.svd((moving-mc).T@(target-tc))
    D=np.eye(3);D[-1,-1]=np.linalg.det(U@Vt)
    R=U@D@Vt;t=tc-mc@R
    return R,t
def rms(a,b):return float(np.sqrt(np.mean(np.sum((a-b)**2,axis=1))))
rows=[]
for fitname,fitids in regions.items():
    ix=np.array(fitids)-1
    R,t=fit(xyz['1AKE'][ix],xyz['4AKE'][ix])
    aligned=xyz['1AKE']@R+t
    check=Superimposer();check.set_atoms([res['4AKE'][i]['CA'] for i in fitids],[res['1AKE'][i]['CA'] for i in fitids])
    assert abs(check.rms-rms(aligned[ix],xyz['4AKE'][ix]))<1e-8
    rows.append({'fit_region':fitname,'fit_n':len(ix),'evaluation_rmsd_A':{name:rms(aligned[np.array(js)-1],xyz['4AKE'][np.array(js)-1]) for name,js in regions.items()}})
    if fitname=='CORE':
        per_res=np.linalg.norm(aligned-xyz['4AKE'],axis=1).tolist()
        core_R,core_t=R.tolist(),t.tolist()
result={'description':'Direct coordinate analysis, not end-to-end Agent execution or benchmark',
 'reference':'4AKE','moving':'1AKE','model':'first deposited model','auth_chain':'A','atom':'CA',
 'selection':'standard amino-acid ATOM residues; retain parser-selected alternate conformer for CA; exclude hetero/water',
 'mapping':'identical residue number and residue name, 1..214','matched_CA':214,'sequence_identity':1.0,
 'units':'angstrom','alignment':'Kabsch SVD, right-handed rotation, no trimming/outlier rejection',
 'domain_definition_source':'https://docs.mdanalysis.org/stable/_modules/MDAnalysis/analysis/rms.html',
 'regions':regions,'rows':rows,'per_residue_displacement_after_CORE_fit_A':per_res,
 'CORE_transform_1AKE_to_4AKE':{'rotation_row_vector':core_R,'translation_A':core_t},
 'files':{c:{'url':f'https://files.rcsb.org/download/{c}.cif','sha256':hashlib.sha256((B/'assets'/f'{c}.cif').read_bytes()).hexdigest()} for c in chains},
 'checks':{'BioPDB_Superimposer_agrees_with_numpy_Kabsch':True},
 'versions':{'numpy':np.__version__,'biopython':Bio.__version__,'python':sys.version.split()[0]},
 'interpretation_limit':'Two static crystal models support geometric comparison only. These values do not measure transition kinetics, free energy, or establish ligand causality.'}
(B/'adk_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'matched':214,'rows':rows},indent=2))
