from pathlib import Path
import shutil,json,hashlib
P=Path(__file__).resolve().parent
old=P.parent/'restored/A22_targeted_noise_selectivity_diagnostic_EN'
for f in ['work_budget.hpp','work_common.cpp']:
 shutil.copy2(old/'src'/f,P/'src'/f)
s=(old/'src/work_cell.cpp').read_text()
s=s.replace('static bool FREEZE_GAINS=false;', '''static bool FREEZE_GAINS=false;
struct PhysicalPort { double cap,lm,ls,le,m; };
static std::array<PhysicalPort,3> PHYS;
''')
s=s.replace('const double INF=std::numeric_limits<double>::infinity(),cap=std::log(GAIN_CAP);','''const double INF=std::numeric_limits<double>::infinity();
    double cap[3],mp[3],lm[3],lp[3],le[3],dm[3],ds[3],de[3];
    double maxc=0,maxm=0,maxlm=0,maxls=0,maxle=0;
    for(int p=0;p<3;p++){
      auto h=PHYS[p];cap[p]=std::log(h.cap);mp[p]=h.m;lm[p]=h.lm;lp[p]=h.ls;le[p]=h.le;
      dm[p]=h.lm==LM?.02:std::log(1.25)/h.lm;
      ds[p]=h.ls==std::log(8.)/1.06?1.06:std::log(8.)/h.ls;
      de[p]=h.le==LE?.15:A/h.le;
      maxc=std::max(maxc,h.cap);maxm=std::max(maxm,h.m);maxlm=std::max(maxlm,h.lm);maxls=std::max(maxls,h.ls);maxle=std::max(maxle,h.le);
      if(!(h.cap>1.2&&h.lm>0&&h.ls>0&&h.le>0&&h.m>0))throw std::runtime_error("invalid physical parameter");
    }''')
s=s.replace('3*GAIN_CAP*A*max_amp','3*maxc*A*max_amp').replace('3*std::max({M*A*max_amp,LM,.8*ls,.1*LE})+2.4*LE+1.5*LM','3*std::max({maxm*A*max_amp,maxlm,.8*maxls,.1*maxle})+2.4*maxle+1.5*maxlm')
s=s.replace('RM+M*x.amp','RM+mp[p]*x.amp')
s=s.replace('d+.02+1.06+.15','d+dm[p]+ds[p]+de[p]').replace('d+.02+1.06','d+dm[p]+ds[p]').replace('d+.02','d+dm[p]')
s=s.replace('std::exp(-LM*(t-mark[p]))','std::exp(-lm[p]*(t-mark[p]))').replace('std::expm1(-LM*u)','std::expm1(-lm[p]*u)').replace('std::expm1(-LM*v)/LM','std::expm1(-lm[p]*v)/lm[p]')
s=s.replace('3,M*amplitude[p]','3,mp[p]*amplitude[p]').replace('h==1?LM:(h==2?ls:LE)','h==1?lm[p]:(h==2?lp[p]:le[p])')
s=s.replace('z[p]<cap','z[p]<cap[p]').replace('cap-z[p]','cap[p]-z[p]').replace('std::min(cap,z[p]+inc)','std::min(cap[p],z[p]+inc)')
s=s.replace('std::exp(-LE*(t-err[p]))','std::exp(-le[p]*(t-err[p]))').replace('/LE:dt','/le[p]:dt').replace('7,LE*mass,LE,','7,le[p]*mass,le[p],').replace('std::expm1(-LE*dt)','std::expm1(-le[p]*dt)')
s=s.replace('double coeff=0.;for(double bpart:Bs)coeff+=LM*bpart;LAST_ENERGY.add(8,coeff,LM,std::min(dt,captime));','for(int p=0;p<3;p++)LAST_ENERGY.add(8,lm[p]*Bs[p],lm[p],std::min(dt,captime));')
s=s.replace('e.origin+e.d+.02+1.06','e.origin+e.d+dm[p]+ds[p]')
(P/'src/work_cell.cpp').write_text(s)
shutil.copy2(old/'scoring.py',P/'scoring.py')
protocol=dict(status='FROZEN_BEFORE_NEW_OUTCOMES',scope='Exploratory joint physical-parameter uncertainty and link-noise pilot, not certification.',seeds=list(range(3000,3006)),epsilon=1e-4,parameter_distribution='Independent uniform relative [-epsilon,+epsilon] per cell, per port and per parameter; fixed across acquisition and both evaluations.',parameters=['C','L_m','L_s','L_e','M'],not_perturbed=['a','kappa','r','r_m','actuation gains','b_max','pump','initial states'],noise=dict(sigma_log_amplitude=.05,jitter_sd=.015,mean_link_delay=.1),arms=['nominal_quiet','nominal_noisy','uncertain_quiet','uncertain_noisy'],training_pulses=2048,training_spacing=8,test_pulses=128,test_gaps=[20,22,21,24,20,23],test_modes=['baseline','lateral_100_mixed'],decoys=24,conditions='Gate-on model only. Same fixed physical field for a seed in its quiet and noisy uncertain arms. No claim about gate necessity or superiority to hybrid.',training_runs=24,evaluations=48,retention='Freeze learned gains and b at test. Reset q=.1. All failed acquisitions retained.',comparisons='Paired uncertainty effect at each noise regime, paired total noise effect at each uncertainty regime, interaction. Counts descriptive by independent network seed.',work='Nine model-work integrals, positive finite-path reserve bound. No detailed E trajectory.',stop='Fixed pilot only; stop on solver/audit failure. Never skip/replace seeds or automatically enlarge.',proof_limit='Six random physical draws are not coverage of the parameter box. Unbounded Gaussian amplitude noise admits no deterministic all-noise guarantee. No initial-state box uncertainty is claimed.',source_commit='22294781127aa47628bb8a3270d5c5a758c31729',source_archive_sha256=hashlib.sha256((P.parent/'upload/A22_targeted_noise_selectivity_diagnostic_EN(1).zip').read_bytes()).hexdigest())
(P/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
