"""Reviewable ablations of the supplied point simulator; no certified engine."""
from pathlib import Path
import difflib
P=Path(__file__).parent
s=(P/'reference_kernel.py').read_text()
s=s.replace('def cell(trains,params,initial,charge_kicks=None):','def cell(trains,params,initial,charge_kicks=None,rule="normal",freeze_at=float("inf")):\n    assert rule in ("normal","none","ungated","gain_frozen")')
start=s.index('def root(');end=s.index('\ndef cell(',start)
s=s[:start]+'''from scipy.optimize import brentq
def root(f,hi):
    flo=f(0.);fhi=f(hi)
    if flo>1e-10 or fhi < -1e-10:raise ArithmeticError(('root',flo,fhi,hi))
    if flo>=0:return 0.
    if fhi<=0:return hi
    return brentq(f,0.,hi,xtol=5e-14,rtol=1e-14)
''' + s[end:]
# Exact same closed-form recovery integral; skip zero coefficients.
s=s.replace('        if b>=1.1:Bs=[0.]*N','        if b>=1.1 or rule=="none" or t>=freeze_at:Bs=[0.]*N\n        activeB=[(B,LM[p]) for p,B in enumerate(Bs) if B]')
s=s.replace('sum(Bs[p]*(-math.expm1(-LM[p]*u)) for p in range(N))','sum(B*(-math.expm1(-rate*u)) for B,rate in activeB)')
s=s.replace('sum(Bs[p]*(v+math.expm1(-LM[p]*v)/LM[p]) for p in range(N))','sum(B*(v+math.expm1(-rate*v)/rate) for B,rate in activeB)')
s=s.replace('                upto=min(dt,max(0.,peak))','                upto=min(dt,max(0.,peak))\n                def charge(u):return R+C*math.exp(-K*u)-D*math.exp(-A*u)')
# Move the z-actuation block outside the READY-only branch; choose its gate.
start=s.index('            for p,s in enumerate(errors):')
end=s.index('        elif phase==1:q*=',start)
block=s[start:end]
s=s[:start]+s[end:]
pos=s.index('        if oldphase!=0:')
new='        if rule not in ("none","gain_frozen") and t<freeze_at and (oldphase==0 or rule=="ungated"):\n'+block
s=s[:pos]+new+s[pos:]
s=s.replace('            b=min(1.1,b+db(dt))','            b=min(1.1,b+db(dt))')
(P/'kernel.py').write_text(s)
(P/'kernel.diff').write_text(''.join(difflib.unified_diff((P/'reference_kernel.py').read_text().splitlines(True),s.splitlines(True),fromfile='reference_kernel.py',tofile='kernel.py')))
print('built kernel.py')
