import concurrent.futures,hashlib,json,pathlib,subprocess,time
P=pathlib.Path(__file__).resolve().parent
CONDITIONS=['learned','ungated','uniform4','uniform2','directional','directional_tail']
SCENARIOS=['clean','lateral_050','lateral_100','central_050','noise_only','noise_mixed','wrong_lane']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def job(level,seed,condition,scenario):
    name=f'L{level}_s{seed}_{condition}_{scenario}';dest=P/'results'/f'{name}.json'
    fp=sha(P/'experiment')+sha(P/'PROTOCOL.json')+sha(P/'CALIBRATION.json')
    inputfile=P/'inputs'/f"L{level}_s{seed}_{'gate_off' if condition=='ungated' else 'gate_on'}.states";source_hash=sha(inputfile)
    if dest.exists():
        try:
            d=json.loads(dest.read_text())
            if d.get('fingerprint')==fp and d.get('checkpoint_sha256')==source_hash:return dict(name=name,cached=True)
        except (ValueError,OSError):pass
    start=time.monotonic();r=subprocess.run([str(P/'experiment'),str(seed),str(level),condition,scenario,str(P/'inputs'),str(dest)],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(f'{name}: {r.stderr}')
    d=json.loads(dest.read_text());d.update(fingerprint=fp,checkpoint_sha256=source_hash)
    tmp=dest.with_suffix('.finalizing');tmp.write_text(json.dumps(d,separators=(',',':')));tmp.replace(dest)
    return dict(name=name,seconds=round(time.monotonic()-start,3))
if __name__=='__main__':
    validation=json.loads((P/'VALIDATION.json').read_text());assert validation['status']=='PASS' and validation['binary_sha256']==sha(P/'experiment')
    jobs=[(l,s,c,t) for l,s in [(-1,0)]+[(l,s) for l in range(3) for s in range(20)] for c in CONDITIONS for t in SCENARIOS];errors=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
        fs={pool.submit(job,*j):j for j in jobs}
        for i,f in enumerate(concurrent.futures.as_completed(fs),1):
            try:r=f.result()
            except Exception as e:r=dict(error=str(e),job=fs[f]);errors.append(r)
            print(json.dumps(dict(done=i,total=len(jobs),**r)),flush=True)
    (P/'RUN_ERRORS.json').write_text(json.dumps(errors,indent=2))
    if errors:raise SystemExit(1)
