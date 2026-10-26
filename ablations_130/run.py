import argparse,collections,concurrent.futures,hashlib,json,math,random,time,traceback
from pathlib import Path
import kernel as s
P=Path(__file__).parent
OUT=P/'output'
PROBES=[4096.]
for i in range(23):PROBES.append(PROBES[-1]+20*[1,1.1,1.05,1.2,1,1.15][i%6])
def noise(seed,n,j,p,label,ordinal,occ):
    # Common random field: unrelated missing pulses cannot shift the draws.
    ident=f'{seed}:{n}:{j}:{p}:{label}:{occ if label is not None else ordinal}'.encode()
    rng=random.Random(int.from_bytes(hashlib.blake2b(ident,digest_size=16).digest(),'big'))
    return rng.gauss(0,1),rng.uniform(-math.sqrt(3),math.sqrt(3))

def run(c):
    dest=OUT/(c['name']+'.json')
    if dest.exists():return {'name':c['name'],'cached':True}
    start=time.monotonic();parents=[[(8.*i,i) for i in range(128)]+[(t,128+i) for i,t in enumerate(PROBES)]]+[[] for _ in range(11)]
    records=[];layers=[]
    try:
        for n in range(1,c.get('depth',130)+1):
            row=[];lc=[]
            for j in range(12):
                trains=[]
                for p,k in enumerate([(j-1)%12,j,(j+1)%12]):
                    train=[];counts=collections.Counter()
                    for ordinal,(t,label) in enumerate(parents[k]):
                        occ=counts[label];counts[label]+=1
                        z,u=noise(c['seed'],n,j,p,label,ordinal,occ)
                        perturbed=c['noise_phase']=='all' or t>=4096
                        sig=c.get('sigma',.1) if perturbed else 0.
                        amp=math.exp(sig*z-sig*sig/2)
                        jitter=c.get('jitter',.03) if perturbed else 0.
                        arrival=t+.1+jitter*u
                        assert arrival>=t
                        train.append((arrival,label,amp,s.A,1.))
                    train.sort();trains.append(train)
                pars=[[4,s.LM0,s.LS0,s.LE0,s.M0] for _ in range(3)]
                initial={'z':list(map(math.log,[.3,1.2,.3])),'q':.1,'b':.08}
                if c.get('reference_solver'):
                    import reference_kernel
                    assert c['rule']=='normal' and not c.get('freeze_after_training')
                    events,info=reference_kernel.cell(trains,pars,initial)
                else:
                    events,info=s.cell(trains,pars,initial,rule=c['rule'],freeze_at=4096. if c.get('freeze_after_training') else math.inf)
                row.append(events)
                probe=[(t,label) for t,label in events if t>=4096]
                rec={'layer':n,'lane':j,'probe_events':probe,'training_count':sum(t<4096 for t,l in events),'before':info['after_training'],'after':info['after_probes'],'probe_gain_moves':info['probe_gain_moves']}
                records.append(rec);lc.append(rec)
            parents=row
            layers.append({'layer':n,'training_count':sum(x['training_count'] for x in lc),'probe_count':sum(len(x['probe_events']) for x in lc)})
        result={'status':'OK_POINT_NOT_CERTIFIED','case':c,'source_probes':PROBES,'cells':records,'layers':layers,'seconds':time.monotonic()-start}
    except Exception as e:result={'status':'UNSUPPORTED_OR_ERROR','case':c,'layer':n,'lane':j,'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.monotonic()-start}
    tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result,separators=(',',':')));tmp.replace(dest)
    return {'name':c['name'],'status':result['status'],'seconds':round(result['seconds'],2),'error':result.get('error')}

def cases():
    cs=[]
    for seed in range(20):
        for rule in ['normal','none','ungated']:
            cs.append({'name':f'all_{rule}_{seed}','rule':rule,'noise_phase':'all','seed':seed})
        cs.append({'name':f'probe_normal_{seed}','rule':'normal','noise_phase':'probes','seed':seed})
    # Quiet controls isolate failure to train from noise sensitivity.
    for rule in ['normal','none','ungated']:
        cs.append({'name':f'quiet_{rule}','rule':rule,'noise_phase':'all','seed':0,'sigma':0.,'jitter':0.})
    # A secondary ablation freezes the actually learned gains AND b at testing.
    for seed in range(20):cs.append({'name':f'frozen_learned_{seed}','rule':'normal','noise_phase':'all','seed':seed,'freeze_after_training':True})
    return cs

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--pilot',action='store_true');a=ap.parse_args()
    OUT.mkdir(exist_ok=True);cs=cases()
    if a.pilot:cs=[c for c in cs if c['name'] in ['all_normal_0','all_none_0','all_ungated_0','quiet_none','quiet_ungated']]
    (P/'cases.json').write_text(json.dumps(cases(),indent=2))
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
        futures={ex.submit(run,c):c for c in cs}
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):print(json.dumps({'done':i,'total':len(cs),**f.result()}),flush=True)
