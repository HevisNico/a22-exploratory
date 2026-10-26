"""Fresh matched-intervention campaign. All scientific settings are in PROTOCOL.json."""
import concurrent.futures,hashlib,json,pathlib,subprocess,time
P=pathlib.Path(__file__).resolve().parent
TESTS=['gate_on','gate_off','trained_off','normal_frozen','uniform4_frozen']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def job(mode,level,seed,condition):
    root=P/('training' if mode=='train' else 'results');name=f'L{level}_s{seed}_{condition}';dest=root/(name+'.json')
    fingerprint=digest(P/'experiment')+digest(P/'PROTOCOL.json')
    checkpoint='-'
    if mode=='test':checkpoint=str(P/'training'/f"L{level}_s{seed}_{'gate_off' if condition=='trained_off' else 'gate_on'}.json.states")
    initial_hash=digest(pathlib.Path(checkpoint)) if checkpoint!='-' else 'nominal_g_0.3_1.2_0.3_b_0.08_q_0.1_E_100'
    if dest.exists():
        try:
            d=json.loads(dest.read_text())
            if d.get('run_fingerprint')==fingerprint and d.get('initial_checkpoint_sha256')==initial_hash and pathlib.Path(str(dest)+'.states').exists():return dict(name=name,cached=True)
        except (ValueError,OSError):pass
    started=time.monotonic()
    subprocess.run([str(P/'experiment'),mode,str(seed),str(level),condition,checkpoint,str(dest),'1'],check=True,capture_output=True,text=True)
    d=json.loads(dest.read_text());d.update(run_fingerprint=fingerprint,initial_checkpoint_sha256=initial_hash,source_checkpoint=pathlib.Path(checkpoint).name)
    dest.write_text(json.dumps(d,separators=(',',':')))
    return dict(name=name,seconds=round(time.monotonic()-started,3))
def batch(jobs):
    errors=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
        fs={pool.submit(job,*j):j for j in jobs}
        for i,f in enumerate(concurrent.futures.as_completed(fs),1):
            try:r=f.result()
            except Exception as e:r={'error':str(e),'job':fs[f]};errors.append(r)
            print(json.dumps(dict(done=i,total=len(jobs),**r)),flush=True)
    return errors
if __name__=='__main__':
    validation=json.loads((P/'VALIDATION.json').read_text())
    assert validation['status']=='PASS'
    assert validation['production_binary_sha256']==digest(P/'experiment'),'Revalidate the rebuilt production binary.'
    assert all(digest(P/k)==v for k,v in validation['tested_cpp_sources_sha256'].items()),'Revalidate modified C++ sources.'
    fields=[(-1,0)]+[(level,seed) for level in range(3) for seed in range(20)]
    errors=batch([('train',level,seed,c) for level,seed in fields for c in ['gate_on','gate_off']])
    if not errors:errors+=batch([('test',level,seed,c) for level,seed in fields for c in TESTS])
    (P/'RUN_ERRORS.json').write_text(json.dumps(errors,indent=2))
    if errors:raise SystemExit(1)
