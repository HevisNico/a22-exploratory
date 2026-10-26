"""Reproducible full-training point experiments based on the supplied simulate.py.
Run python run_experiments.py --suite all --workers 8; analyze with analyze.py.
"""
import argparse,concurrent.futures,hashlib,json,math,random,time,traceback
from pathlib import Path
import extended_simulate as sim

ROOT=Path(__file__).parent
OUT=ROOT/'output'
def source_dates(case):
    # Irregular words detect fidelity beyond propagation of a periodic train.
    pattern=[1.,1.1,1.05,1.2,1.,1.15]
    dates=[4096.]
    for i in range(case.get('probes',24)-1):dates.append(dates[-1]+case.get('gap',20.)*pattern[i%len(pattern)])
    return dates

def topology(case):
    w=case.get('width',12);k=case.get('parents',3)
    rng=random.Random(case.get('topology_seed',90210))
    rows=[]
    for n in range(case.get('depth',18)):
        rows.append([rng.sample(range(w),k) if case.get('topology')=='random' else [(j+d)%w for d in range(-(k//2),k//2+1)] for j in range(w)])
    return rows

def run(case):
    start=time.monotonic();name=case['name'];path=OUT/(name+'.json')
    if path.exists():return {'name':name,'cached':True}
    rng=random.Random(case.get('seed',0));w=case.get('width',12);k=case.get('parents',3)
    probes=source_dates(case);graph=topology(case)
    source=[(8.*i,i) for i in range(128)]+[(s,128+i) for i,s in enumerate(probes)]
    parents=[source]+[[] for _ in range(w-1)];cells=[];layers=[]
    try:
        for n,row in enumerate(graph,1):
            new=[];layercells=[]
            for j,indices in enumerate(row):
                gains=[(.3 if case.get('gain_policy')=='added' else .6/(k-1))]*k;gains[k//2]=1.2
                pars=[[4,sim.LM0,sim.LS0,sim.LE0,sim.M0] for _ in range(k)]
                initial={'z':list(map(math.log,gains)),'q':sim.R,'b':.08}
                trains=[];kicks={}
                for p,parent in enumerate(indices):
                    train=[]
                    for t,label in parents[parent]:
                        perturb=case.get('noise_phase','probes')=='all' or t>=4096
                        sigma=case.get('sigma_amplitude',0.) if perturb else 0.
                        amplitude=math.exp(sigma*rng.gauss(0,1)-sigma*sigma/2) if sigma else 1.
                        jitter=case.get('jitter',0.) if perturb else 0.
                        # Signed edge-delay variation; positive nominal delay preserves causality.
                        delay=case.get('delay',0.)
                        if jitter:
                            delay+=rng.uniform(-math.sqrt(3)*jitter,math.sqrt(3)*jitter)
                        if delay < -1e-14:raise ArithmeticError('negative edge delay')
                        arrival=t+max(0.,delay)
                        decay=sim.A;width=1.
                        if n==1 and label is not None and label>=128:
                            factor=case.get('shape_factor',1.)
                            if case.get('shape_mode')=='alternating':factor=1.+(factor-1.)*(1 if label%2 else -1)
                            decay=sim.A*factor;width=case.get('pulse_width',1.)
                            # Match integral charge of the canonical pulse: 1-exp(-ln4)=.75.
                            amplitude*=.75/(-math.expm1(-decay*width))
                        train.append((arrival,label,amplitude,decay,width))
                        sigmaq=case.get('sigma_q',0.) if perturb else 0.
                        if sigmaq:kicks[p,label]=rng.uniform(-math.sqrt(3)*sigmaq*.9,math.sqrt(3)*sigmaq*.9)
                    train.sort();trains.append(train)
                events,info=sim.cell(trains,pars,initial,kicks)
                new.append(events)
                c={'layer':n,'lane':j,'training_count':sum(t<4096 for t,l in events),
                   'events':[(t,l) for t,l in events if t>=4096],
                   'before':info['after_training'],'after':info['after_probes'],
                   'probe_gain_moves':info['probe_gain_moves'],
                   'closest_event_gap':info['closest_event_gap']}
                if case.get('save_training'):c['training_events']=[(t,l) for t,l in events if t<4096]
                cells.append(c);layercells.append(c)
            parents=new
            layers.append({'layer':n,'training_events':sum(c['training_count'] for c in layercells),'probe_events':sum(len(c['events']) for c in layercells)})
        result={'status':'OK_POINT_NOT_CERTIFIED','case':case,'source_probes':probes,'graph':graph,'cells':cells,'layers':layers,'seconds':time.monotonic()-start}
    except Exception as e:
        result={'status':'UNSUPPORTED_OR_ERROR','case':case,'error':str(e),'traceback':traceback.format_exc(),'layer':n,'lane':j,'seconds':time.monotonic()-start}
    path.write_text(json.dumps(result,separators=(',',':')))
    return {'name':name,'status':result['status'],'seconds':round(result['seconds'],2),'error':result.get('error')}

def cases(suite):
    allcases=[]
    def add(name,**kw):allcases.append({'name':name,**kw})
    add('baseline',save_training=True)
    add('baseline_delay',delay=.1)
    if suite in ('all','noise'):
        for seed in range(12):
            for amp in [.001,.003,.01,.03,.05,.1,.2]:
                add(f'amp_{amp}_{seed}',sigma_amplitude=amp,seed=seed)
            for jitter in [.001,.003,.01,.03,.05]:
                add(f'jitter_{jitter}_{seed}',jitter=jitter,delay=.1,seed=seed)
            for sigmaq in [.001,.01,.03]:
                add(f'q_{sigmaq}_{seed}',sigma_q=sigmaq,seed=seed)
            for amp,jitter in [(.01,.003),(.03,.01),(.1,.03)]:
                add(f'joint_{amp}_{seed}',sigma_amplitude=amp,jitter=jitter,delay=.1,seed=seed)
        for seed in range(6):
            for amp in [.01,.03,.1]:add(f'allnoise_{amp}_{seed}',sigma_amplitude=amp,jitter=amp*.3,delay=.1,noise_phase='all',seed=seed)
    if suite in ('all','topology'):
        configs=[('ring24',{'width':24}),('ring48',{'width':48}),('parents5',{'parents':5}),('parents7',{'parents':7}),('parents5_added',{'parents':5,'gain_policy':'added'}),('parents7_added',{'parents':7,'gain_policy':'added'})]
        for seed in range(6):configs.append((f'random3_{seed}',{'topology':'random','topology_seed':seed+200}))
        for seed in range(6):configs.append((f'random5_{seed}',{'topology':'random','parents':5,'topology_seed':seed+200}))
        for name,config in configs:
            add(name,**config)
            for seed in range(3):add(name+f'_noisy_{seed}',**config,sigma_amplitude=.03,seed=seed)
    if suite in ('all','inputs'):
        for gap in [16,12,8,7,6,5,4,3,2,1.5]:
            add(f'gap_{gap}',gap=gap)
            for seed in range(3):add(f'gap_{gap}_noisy_{seed}',gap=gap,sigma_amplitude=.03,seed=seed)
        for factor in [.9,.95,1.05,1.1]:
            for mode in ['fixed','alternating']:add(f'shape_{mode}_{factor}',shape_factor=factor,shape_mode=mode)
        for width in [.9,1.1]:add(f'width_{width}',pulse_width=width)
    if suite in ('all','depth'):
        add('depth130',depth=130)
        add('depth130_delay',depth=130,delay=.1)
        for seed in range(4):
            for amp in [.01,.03,.1]:add(f'depth130_amp_{amp}_{seed}',depth=130,sigma_amplitude=amp,seed=seed)
            add(f'depth130_joint_{seed}',depth=130,sigma_amplitude=.03,jitter=.01,delay=.1,seed=seed)
    return allcases

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--suite',default='all');ap.add_argument('--workers',type=int,default=8);args=ap.parse_args()
    OUT.mkdir(exist_ok=True)
    cs=cases(args.suite);(ROOT/'cases.json').write_text(json.dumps(cs,indent=2))
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i,r in enumerate(ex.map(run,cs),1):print(json.dumps({'done':i,'total':len(cs),**r}),flush=True)
