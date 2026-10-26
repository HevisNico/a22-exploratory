"""Build a reviewable extension of the supplied event-driven point simulator.
Never imports the certified engine. Keep original_simulate.py byte-identical.
"""
from pathlib import Path
import difflib

root=Path(__file__).parent
s=(root/'original_simulate.py').read_text()
s=s[:s.index('\ndef parameters(')]
s=s.replace('def cell(trains,params,initial):','def cell(trains,params,initial,charge_kicks=None):\n    N=len(trains)\n    charge_kicks=charge_kicks or {}')
s=s.replace('range(3)','range(N)').replace('[None]*3','[None]*N').replace('[0.]*3','[0.]*N')
start=s.index('    d=[root(')
end=s.index('    external.sort()',start)
s=s[:start]+'''    dm=[math.log(1.25)/x for x in LM];ds=[math.log(8)/x for x in LS];de=[A/x for x in LE]
    external=[];pulses={};delays={};delay_cache={}
    for p,train in enumerate(trains):
        previous_end=-math.inf
        for s,label,amplitude,decay,width in train:
            assert amplitude>0 and decay>K and width>0
            def response(u):
                return amplitude*decay/(decay-K)*(math.exp(-K*u)-math.exp(-decay*u))
            peak=min(width,math.log(decay/K)/(decay-K))
            if RM+M[p]*response(peak)<1:
                raise ArithmeticError('auxiliary subthreshold: residual memory needs full auxiliary solver')
            cache_key=(p,amplitude,decay,width)
            if cache_key not in delay_cache:delay_cache[cache_key]=root(lambda u:RM+M[p]*response(u)-1,peak)
            d=delay_cache[cache_key]
            cycle=d+dm[p]+ds[p]+de[p]
            if s<=previous_end:raise ArithmeticError('auxiliary not regenerated')
            if d+dm[p]+ds[p]<=width:raise ArithmeticError('ERROR overlaps own raw pulse')
            previous_end=s+max(cycle,width)
            pulses[p,s]=(amplitude,decay,width);delays[p,s]=d
            for age,kind in [(0.,0),(d,1),(d+dm[p],2),(width,3),(d+dm[p]+ds[p],4),(cycle,5)]:
                external.append((s+age,kind,p,s,label))
''' +s[end:]
start=s.index('        internal=None')
end=s.index('        elif phase==2',start)
s=s[:start]+'''        internal=None
        terms=[(math.exp(z[p])*pulses[p,s][0]*pulses[p,s][1]*math.exp(-pulses[p,s][1]*(t-s)),pulses[p,s][1]) for p,s in enumerate(raw) if s is not None]
        def charge(u):
            ek=math.exp(-K*u)
            return R+(q-R)*ek+sum(J*(ek-math.exp(-decay*u))/(decay-K) for J,decay in terms)
        if phase==0 and dt>0:
            if all(decay==A for J,decay in terms):
                J=sum(J for J,decay in terms)
                C=q-R+J/(A-K);D=J/(A-K)
                peak=math.log(A*D/(K*C))/(A-K) if C>0 and D>0 else 0.
                upto=min(dt,max(0.,peak))
            else:
                # derivative times exp(K*u) is strictly decreasing for positive inputs.
                def derivative_scaled(u):
                    return -K*(q-R)+sum(J*(-K+decay*math.exp(-(decay-K)*u))/(decay-K) for J,decay in terms)
                if derivative_scaled(0)<=0:upto=0.
                elif derivative_scaled(dt)>=0:upto=dt
                else:upto=root(lambda u:-derivative_scaled(u),dt)
            if upto>0 and charge(upto)>=1:dt=root(lambda u:charge(u)-1,upto);internal='fire'
''' +s[end:]
start=s.index('            J=sum(',s.index('        oldphase=phase'))
end=s.index('            for p,s in enumerate(errors):',start)
s=s[:start]+'            q=charge(dt)\n'+s[end:]
s=s.replace('marks[p]=s+d[p]','marks[p]=s+delays[p,s]').replace('errors[p]=s+d[p]+dm[p]+ds[p]','errors[p]=s+delays[p,s]+dm[p]+ds[p]')
s=s.replace('raw[p]=s;labels[p]=label','raw[p]=s;labels[p]=label\n                if phase==0:q=max(0.,q+charge_kicks.get((p,label),0.))')
s=s.replace('            idx+=1\n','''            idx+=1
        if phase==0 and q>=1:
            live=[labels[p] for p in range(N) if raw[p] is not None]
            unique=set(live)
            label=next(iter(unique)) if len(unique)==1 and None not in unique else None
            if label is None:mix.append({'time':t,'parent_labels':live})
            q=1.;phase=1;fast_end=t+1.;out.append((t,label))
''')
(root/'extended_simulate.py').write_text(s)
(root/'extension.diff').write_text(''.join(difflib.unified_diff((root/'original_simulate.py').read_text().splitlines(True),s.splitlines(True),fromfile='original_simulate.py',tofile='extended_simulate.py')))
print('Built extended_simulate.py')
