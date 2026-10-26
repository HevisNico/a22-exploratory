"""Operational timing errors from paired physical outputs; no mixed-run labels."""
import bisect
import math

def match_times(reference, observed, tolerance=2.0):
    """Ordered maximum-cardinality matching, then minimum total |time shift|.

    Return index pairs. Separated reference windows have a linear fast path.
    Overlapping windows use dynamic programming. Ties prefer a current match.
    """
    a=list(reference); b=list(observed)
    if tolerance<0 or any(not math.isfinite(t) for t in a+b):
        raise ValueError('Invalid event times/tolerance')
    if a!=sorted(a) or b!=sorted(b):
        raise ValueError('Events must be ordered')
    if all(y-x>2*tolerance for x,y in zip(a,a[1:])):
        pairs=[]
        for i,t in enumerate(a):
            lo=bisect.bisect_left(b,t-tolerance); hi=bisect.bisect_right(b,t+tolerance)
            if hi>lo:
                j=min(range(lo,hi),key=lambda j:(abs(b[j]-t),j));pairs.append((i,j))
        return pairs
    n,m=len(a),len(b)
    table=[[(0,0.) for _ in range(m+1)] for _ in range(n+1)]
    move=[[0]*(m+1) for _ in range(n+1)]
    for i in range(1,n+1):
        for j in range(1,m+1):
            options=[(table[i-1][j],1),(table[i][j-1],2)]
            delta=abs(a[i-1]-b[j-1])
            if delta<=tolerance:
                k,c=table[i-1][j-1];options.append(((k+1,c-delta),3))
            table[i][j],move[i][j]=max(options,key=lambda x:(x[0],x[1]))
    pairs=[];i=n;j=m
    while i and j:
        step=move[i][j]
        if step==3:pairs.append((i-1,j-1));i-=1;j-=1
        elif step==1:i-=1
        else:j-=1
    return pairs[::-1]

def paired_score(clean, mixed, alone, tolerance=2.):
    """Clean-missing identities remain failures even if noise fills a time slot.

    Retention is an observable receiver criterion, not proof of event ancestry.
    An event shifted beyond the tolerance counts as one removal and one addition.
    """
    if any(len(d['output_events'])!=12 for d in (clean,mixed,alone)):
        raise ValueError('Expected 12 output lanes')
    covered=retained=added=removed=clean_extra=0;shifts=[];word=True
    for ref,test in zip(clean['output_events'],mixed['output_events']):
        a=[e[0] for e in ref];b=[e[0] for e in test]
        pairs=match_times(a,b,tolerance);added+=len(b)-len(pairs);removed+=len(a)-len(pairs)
        shifts.extend(b[j]-a[i] for i,j in pairs)
        # Only unambiguous, unique source identities in the clean run are anchors.
        appearances={i:[] for i in range(128)}
        for k,e in enumerate(ref):
            for i in e[2]:
                if 0<=i<128:appearances[i].append(k)
        valid=sorted(v[0] for i,v in appearances.items() if len(v)==1 and ref[v[0]][2]==[i])
        identities=[ref[k][2][0] for k in valid]
        if identities!=sorted(identities):valid=[]  # a reordered clean lane is not a valid receiver reference
        anchors=[a[k] for k in valid];matches=match_times(anchors,b,tolerance)
        covered+=len(valid);retained+=len(matches);clean_extra+=len(a)-len(valid)
        word &= len(valid)==128 and len(matches)==128 and len(b)==128
    return dict(clean_coverage=covered/1536,retained_recall=retained/1536,
                added_events=added,removed_events=removed,clean_extra_events=clean_extra,
                net_event_change=sum(map(len,mixed['output_events']))-sum(map(len,clean['output_events'])),
                noise_only_events=sum(map(len,alone['output_events'])),full_word=bool(word),
                max_abs_matched_shift=max(map(abs,shifts),default=0.),
                mean_abs_matched_shift=sum(map(abs,shifts))/len(shifts) if shifts else None,
                mixed_work=mixed['energy']['work_total'],clean_work=clean['energy']['work_total'],
                alone_work=alone['energy']['work_total'])

def audit_physics(d,frozen=True):
    e=d['energy'];w=e['work_components'];fail=[]
    tests=[('work_sum',sum(w.values())-e['work_total'],e['work_total']),
           ('fast_drain',w['main_fast']-.75*e['fires'],e['fires']),
           ('pump',0. if e.get('reserve_mode')=='positive_bound_work_exact' else e['pump_supplied']-e['work_total']-(e['sum_terminal_E']-100*e['cells']),e['work_total'])]
    for key,mass in [('aux_mark',.2),('aux_silent',.7),('aux_error',.075)]:
        tests.append((key,w[key]-mass*e['input_pulses'],e['input_pulses']))
    for key,err,scale in tests:
        if not math.isfinite(err) or abs(err)>1e-6+1e-8*max(1,scale):fail.append(key)
    if not e['continuous_E_lower_bound']>0:fail.append('reserve_bound')
    if frozen and (w['gain_learning']!=0 or w['b_learning']!=0):fail.append('plasticity_not_frozen')
    for lane in d['output_events']:
        times=[e[0] for e in lane]
        if any(not math.isfinite(t) for t in times) or times!=sorted(times):fail.append('output_times')
    if d.get('injection_timing',{}).get('violations',0):fail.append('probe_not_interstitial')
    if fail:raise ValueError(fail)
