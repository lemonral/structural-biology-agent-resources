"""Cluster-paired bootstrap demonstration; not a model evaluation result."""
from collections import defaultdict
import json
from pathlib import Path
import numpy as np

def paired_cluster_bootstrap(rows,system_a,system_b,n_resamples=5000,seed=20261101):
    """Mean repeats within task; equal task weights within cluster; equal clusters."""
    grouped=defaultdict(lambda:defaultdict(lambda:defaultdict(dict)))
    for row in rows:
        if row['system_id'] not in {system_a,system_b}:continue
        score=float(row['scientific_pass'])
        if not np.isfinite(score) or not 0<=score<=1:raise ValueError('Scores must lie in [0,1]')
        records=grouped[row['object_group']][row['task_id']][row['system_id']]
        if row['repeat_id'] in records:raise ValueError('Duplicate independent-run identifier')
        records[row['repeat_id']]=score
    if len(grouped)<2:
        return {'status':'insufficient_clusters','object_groups':len(grouped),
                'reason':'One AdK family cannot support a cross-object generalization interval.'}
    deltas=[]
    for tasks in grouped.values():
        task_deltas=[]
        for systems in tasks.values():
            if set(systems)!={system_a,system_b} or set(systems[system_a])!=set(systems[system_b]):
                raise ValueError('Paired tasks and repeat IDs must match; failed runs remain in data')
            task_deltas.append(float(np.mean(list(systems[system_b].values()))-np.mean(list(systems[system_a].values()))))
        deltas.append(float(np.mean(task_deltas)))
    rng=np.random.default_rng(seed);values=np.array(deltas)
    # A common sampled cluster index couples both systems through their delta.
    sampled=rng.integers(0,len(values),size=(n_resamples,len(values)))
    draws=values[sampled].mean(1)
    return {'status':'ok','difference':'B minus A','mean_difference':float(values.mean()),
            'percentile_interval_95':np.quantile(draws,[.025,.975]).tolist(),
            'object_groups':len(values),'resamples':n_resamples,'seed':seed,
            'weighting':'mean repeats per task, equal tasks per cluster, equal clusters',
            'limit':'Percentile bootstrap is illustrative; few clusters, dependence and chosen target population limit interpretation.'}

def main():
    rows=[]
    for g in range(8):
        for task in range(3):
            for repeat in range(2):
                for system in ['A','B']:
                    score=int((g+task+repeat)%4!=0) if system=='A' else int((g+2*task+repeat)%5!=0)
                    rows.append({'object_group':f'abstract_cluster_{g}','task_id':f'{g}_{task}',
                                 'repeat_id':repeat,'system_id':system,'scientific_pass':score})
    out=Path(__file__).resolve().parent/'statistics_demo';out.mkdir(exist_ok=True)
    (out/'SIMULATED_rows.json').write_text(json.dumps({'label':'SIMULATED_ABSTRACT_TEACHING_DATA_NO_AGENT_RUNS','rows':rows},indent=2)+'\n')
    report=paired_cluster_bootstrap(rows,'A','B');report['label']='SIMULATED_ABSTRACT_TEACHING_DATA_NO_AGENT_RUNS'
    (out/'SIMULATED_bootstrap.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
