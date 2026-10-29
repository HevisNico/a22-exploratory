// Numeric point implementation of the supplied simulator, NOT a certified engine.
// Three nominal ports, canonical exponential pulses with per-pulse amplitudes.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <limits>
#include <stdexcept>
#include <vector>
#include <array>
#include <cstdint>
using Lineage=std::array<uint64_t,4>;
extern "C" {
struct Pulse { double time; long long label; double amp; int port; Lineage lineage{}; };
struct Output { double time; long long label; Lineage lineage{}; };
struct State { double z[3],b,q,time; int phase; };
}
struct Event {double t;int kind,p;double origin,d;long long label;double amp;Lineage lineage{};};
static const double A=std::log(4.),K=.5,R=.1,RM=.025,LM=std::log(1.25)/.02,LE=A/.15;
static const double M=.975/(A/(A-K)*(std::exp(-K*.02)-std::exp(-A*.02)));
template<class F> double root(F f,double hi) {
    double lo=0.,fl=f(lo),fh=f(hi);
    if(fl>1e-10 || fh< -1e-10)throw std::runtime_error("root bracket");
    if(fl>=0)return 0.;if(fh<=0)return hi;
    int side=0;
    for(int i=0;i<100;i++){
        double x=(lo*fh-hi*fl)/(fh-fl);
        if(!(x>lo&&x<hi))x=(lo+hi)*.5;
        double fx=f(x);if(fx==0.)return x;
        if(fx>0){hi=x;fh=fx;if(side==1)fl*=.5;side=1;}
        else{lo=x;fl=fx;if(side==-1)fh*=.5;side=-1;}
        if(hi-lo<2e-14+2e-15*std::abs(x))return (lo+hi)*.5;
    }
    return (lo+hi)*.5;
}
static double GAIN_CAP=4.;
static bool FREEZE_GAINS=false;
static std::array<double,3> ACTUATION={1.,1.,1.};
struct PhysicalPort { double cap,lm,ls,le,m; };
static std::array<PhysicalPort,3> PHYS;

#include "work_budget.hpp"
extern "C" int point_cell(const Pulse* input,int size,const State* initial,int frozen,int ungated,
 double probe_start,Output* output,int capacity,State* terminal,State* before,
 long long* gain_moves,double* diagnostic,long long tail_label,char* error,int error_capacity){
 try {
    const double INF=std::numeric_limits<double>::infinity();
    double cap[3],mp[3],lm[3],lp[3],le[3],dm[3],ds[3],de[3];
    double maxc=0,maxm=0,maxlm=0,maxls=0,maxle=0;
    for(int p=0;p<3;p++){
      auto h=PHYS[p];cap[p]=std::log(h.cap);mp[p]=h.m;lm[p]=h.lm;lp[p]=h.ls;le[p]=h.le;
      dm[p]=h.lm==LM?.02:std::log(1.25)/h.lm;
      ds[p]=h.ls==std::log(8.)/1.06?1.06:std::log(8.)/h.ls;
      de[p]=h.le==LE?.15:A/h.le;
      maxc=std::max(maxc,h.cap*ACTUATION[p]);maxm=std::max(maxm,h.m);maxlm=std::max(maxlm,h.lm);maxls=std::max(maxls,h.ls);maxle=std::max(maxle,h.le);
      if(!(h.cap>1.2&&h.lm>0&&h.ls>0&&h.le>0&&h.m>0))throw std::runtime_error("invalid physical parameter");
    }
    LAST_ENERGY=EnergyBudget();
    double max_amp=1.;for(int i=0;i<size;i++)max_amp=std::max(max_amp,input[i].amp);
    double ls=std::log(8.)/1.06;
    double work_bound=std::max({3*maxc*A*max_amp,A,1.1})+3*std::max({maxm*A*max_amp,maxlm,.8*maxls,.1*maxle})+2.4*maxle+1.5*maxlm;
    LAST_ENERGY.lower_bound=std::min(100.,100.-work_bound/10.);
    if(ENERGY_ENABLED&&LAST_ENERGY.lower_bound<=0)throw std::runtime_error("finite-path resource bound not positive");
    std::vector<Event> events;events.reserve(size*6);
    double previous_end[3]={-INF,-INF,-INF};
    for(int i=0;i<size;i++){
        auto x=input[i];int p=x.port;
        if(p<0||p>=3||x.amp<=0)throw std::runtime_error("invalid input");
        double d=root([&](double u){return RM+mp[p]*x.amp*A/(A-K)*(std::exp(-K*u)-std::exp(-A*u))-1.;},1.);
        double cycle=d+dm[p]+ds[p]+de[p];
        if(x.time<=previous_end[p])throw std::runtime_error("auxiliary not regenerated");
        if(d+dm[p]+ds[p]<=1.)throw std::runtime_error("raw/error overlap");
        previous_end[p]=x.time+std::max(1.,cycle);
        double ages[6]={0.,d,d+dm[p],1.,d+dm[p]+ds[p],cycle};
        for(int k=0;k<6;k++)events.push_back({x.time+ages[k],k,p,x.time,d,x.label,x.amp,x.lineage});
    }
    std::sort(events.begin(),events.end(),[](const Event& a,const Event& b){
        if(a.t!=b.t)return a.t<b.t;if(a.kind!=b.kind)return a.kind<b.kind;
        if(a.p!=b.p)return a.p<b.p;if(a.origin!=b.origin)return a.origin<b.origin;return a.label<b.label;
    });
    double z[3];std::copy(initial->z,initial->z+3,z);double q=initial->q,b=initial->b,t=initial->time,fast_end=INF;
    int phase=0,nout=0;size_t idx=0;bool snap=false;long long moves=0;
    double raw[3]={-INF,-INF,-INF},amplitude[3]={0,0,0},mark[3]={-INF,-INF,-INF},err[3]={-INF,-INF,-INF};
    long long labels[3]={-1,-1,-1},error_labels[3]={-1,-1,-1};
    Lineage raw_lineage[3]{};
    double requested_ready=0.,requested_protected=0.;
    int aux_phase[3]={0,0,0};double aux_start[3]={0,0,0};
    double last_gain=-1.,last_b=-1.,tail_dz=0.,tail_db=0.; long long total_moves=0,tail_moves=0;
    auto state=[&](){State st;std::copy(z,z+3,st.z);st.b=b;st.q=q;st.time=t;st.phase=phase;return st;};
    auto emit=[&](){
        long long label=-2;for(int p=0;p<3;p++)if(raw[p]!=-INF){if(label==-2)label=labels[p];else if(label!=labels[p])label=-1;}
        if(label<0)label=-1;
        Lineage lineage{};for(int p=0;p<3;p++)if(raw[p]!=-INF)for(int j=0;j<4;j++)lineage[j]|=raw_lineage[p][j];
        if(nout>=capacity)throw std::runtime_error("output capacity");output[nout++]={t,label,lineage};
    };
    long long steps=0;
    while(idx<events.size()||phase!=0){
        if(++steps>10000000)throw std::runtime_error("step budget");
        double ext=idx<events.size()?events[idx].t:INF;
        if(!snap&&ext>=probe_start&&phase==0){
            for(int p=0;p<3;p++)if(raw[p]!=-INF||mark[p]!=-INF||err[p]!=-INF)throw std::runtime_error("uncleared training state");
            *before=state();snap=true;
        }
        double target=phase==1?std::min(ext,fast_end):ext;
        if(!std::isfinite(target)){if(phase!=2)throw std::runtime_error("infinite target");target=t+20.;}
        double dt=std::max(0.,target-t),Bs[3]={0,0,0};
        if(b<1.1&&!frozen)for(int p=0;p<3;p++)if(mark[p]!=-INF)Bs[p]=.5*std::exp(-lm[p]*(t-mark[p]));
        auto db=[&](double u){double value=0.;for(int p=0;p<3;p++)value+=Bs[p]*(-std::expm1(-lm[p]*u));return value;};
        double captime=(b<1.1&&b+db(dt)>1.1)?root([&](double u){return db(u)-(1.1-b);},dt):INF;
        auto intb=[&](double u){double v=std::min(u,captime),value=b*v;for(int p=0;p<3;p++)value+=Bs[p]*(v+std::expm1(-lm[p]*v)/lm[p]);return value+1.1*std::max(0.,u-v);};
        double J=0.;for(int p=0;p<3;p++)if(raw[p]!=-INF)J+=ACTUATION[p]*std::exp(z[p])*amplitude[p]*A*std::exp(-A*(t-raw[p]));
        double C=q-R+J/(A-K),D=J/(A-K);
        auto charge=[&](double u){return R+C*std::exp(-K*u)-D*std::exp(-A*u);};
        int internal=0;
        if(phase==0&&dt>0){
            double peak=(C>0&&D>0)?std::log(A*D/(K*C))/(A-K):0.;double upto=std::min(dt,std::max(0.,peak));
            if(upto>0&&charge(upto)>=1.){dt=root([&](double u){return charge(u)-1.;},upto);internal=1;}
        }else if(phase==2&&intb(dt)>=std::log(q/R)){
            double needed=std::log(q/R);dt=root([&](double u){return intb(u)-needed;},dt);internal=2;
        }
        int old=phase;
        if(ENERGY_ENABLED){
            LAST_ENERGY.begin(dt);
            if(old==0)LAST_ENERGY.add(0,J,A,dt);
            else if(old==1)LAST_ENERGY.add(1,A*q,A,dt);
            else LAST_ENERGY.add(2,1.1,0.,dt);
            for(int p=0;p<3;p++){
                int h=aux_phase[p];
                if(h==0){if(raw[p]!=-INF)LAST_ENERGY.add(3,mp[p]*amplitude[p]*A*std::exp(-A*(t-raw[p])),A,dt);}
                else{double rate=h==1?lm[p]:(h==2?lp[p]:le[p]);double section=h==1?1.:(h==2?.8:.1);LAST_ENERGY.add(3+h,rate*section*std::exp(-rate*(t-aux_start[p])),rate,dt);}
                if(!frozen&&!FREEZE_GAINS&&(old==0||ungated)&&err[p]!=-INF&&z[p]<cap[p]){
                    double mass=.8*std::exp(-le[p]*(t-err[p]));
                    double length=mass>cap[p]-z[p]?-std::log1p(-(cap[p]-z[p])/mass)/le[p]:dt;
                    LAST_ENERGY.add(7,le[p]*mass,le[p],std::min(dt,length));
                }
            }
            if(old!=0&&!frozen){for(int p=0;p<3;p++)LAST_ENERGY.add(8,lm[p]*Bs[p],lm[p],std::min(dt,captime));}
            LAST_ENERGY.finish();
        }
        if(phase==0)q=charge(dt);else if(phase==1)q*=std::exp(-A*dt);else q*=std::exp(-intb(dt));
        if(!frozen)for(int p=0;p<3;p++)if(err[p]!=-INF){
            double demand=.8*std::exp(-le[p]*(t-err[p]))*(-std::expm1(-le[p]*dt));
            if(old==0)requested_ready+=demand;else requested_protected+=demand;
        }
        if(!frozen&&!FREEZE_GAINS&&(old==0||ungated))for(int p=0;p<3;p++)if(err[p]!=-INF){
            if(raw[p]!=-INF)throw std::runtime_error("own raw/error overlap");
            double inc=.8*std::exp(-le[p]*(t-err[p]))*(-std::expm1(-le[p]*dt));
            if(inc>0&&z[p]<cap[p]&&t>=probe_start)moves++;
            double added=std::min(cap[p],z[p]+inc)-z[p];
            if(added>0){total_moves++;last_gain=t+dt;if(error_labels[p]>=tail_label){tail_moves++;tail_dz+=added;}}
            z[p]=std::min(cap[p],z[p]+inc);
        }
        if(old!=0){double added=std::min(1.1,b+db(dt))-b;if(added>0){last_b=t+dt;bool tail=false;for(int p=0;p<3;p++)if(mark[p]!=-INF&&labels[p]>=tail_label)tail=true;if(tail)tail_db+=added;}b=std::min(1.1,b+db(dt));}
        t+=dt;
        if(internal){if(internal==1){q=1.;phase=1;fast_end=t+1.;emit();}else{q=R;phase=0;}continue;}
        if(old==1&&std::abs(t-fast_end)<1e-9){q=.25;phase=2;fast_end=INF;}
        while(idx<events.size()&&std::abs(events[idx].t-t)<1e-9){
            auto e=events[idx];int p=e.p;
            if(e.kind==0){if(raw[p]!=-INF)throw std::runtime_error("raw overlap");raw[p]=e.origin;amplitude[p]=e.amp;labels[p]=e.label;raw_lineage[p]=e.lineage;}
            else if(e.kind==1){mark[p]=e.origin+e.d;aux_phase[p]=1;aux_start[p]=t;}
            else if(e.kind==2){mark[p]=-INF;aux_phase[p]=2;aux_start[p]=t;}
            else if(e.kind==3){raw[p]=-INF;labels[p]=-1;}
            else if(e.kind==4){aux_phase[p]=3;aux_start[p]=t;err[p]=e.origin+e.d+dm[p]+ds[p];error_labels[p]=e.label;}
            else{err[p]=-INF;aux_phase[p]=0;aux_start[p]=t;}
            idx++;
        }
    }
    *terminal=state();if(!snap)*before=*terminal;*gain_moves=moves;diagnostic[0]=total_moves;diagnostic[1]=tail_moves;diagnostic[2]=tail_dz;diagnostic[3]=tail_db;diagnostic[4]=last_gain;diagnostic[5]=last_b;diagnostic[6]=requested_ready;diagnostic[7]=requested_protected;return nout;
 }catch(const std::exception& e){std::snprintf(error,error_capacity,"%s",e.what());return -1;}
}
