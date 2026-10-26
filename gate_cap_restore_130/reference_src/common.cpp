// Full-network orchestration for the numeric point simulator. Not a certificate.
#include "point_cell.cpp"
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <map>
#include <string>
#include <iostream>
#include <sstream>
using Train=std::vector<Output>;
using Row=std::array<Train,12>;
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
static double uniform(uint64_t x){return ((mix(x)>>11)+.5)*0x1.0p-53;}
static std::pair<double,double> noise(int seed,int layer,int lane,int port,int stage,long long label,int occurrence){
    uint64_t key=mix(seed+137);key=mix(key^uint64_t(layer));key=mix(key^uint64_t(lane));key=mix(key^uint64_t(port));key=mix(key^uint64_t(stage));key=mix(key^uint64_t(label));key=mix(key^uint64_t(occurrence));
    return {std::sqrt(-2*std::log(uniform(key)))*std::cos(6.2831853071795864769*uniform(key^0x1af7)),std::sqrt(3.)*(2*uniform(key^0xa53d)-1)};
}
extern "C" void noise_pair(int seed,int layer,int lane,int port,int stage,long long label,int occurrence,double* out){auto x=noise(seed,layer,lane,port,stage,label,occurrence);out[0]=x.first;out[1]=x.second;}
std::vector<Pulse> incoming(const Row& row,int seed,int layer,int lane,int stage,double sigma,double jitter){
    std::vector<Pulse> in;
    for(int p=0;p<3;p++){
        auto& train=row[(lane+p+11)%12];std::map<long long,int> counts;int ordinal=0;
        for(auto x:train){int occurrence=counts[x.label]++;auto z=noise(seed,layer,lane,p,stage,x.label<0?-1-ordinal:x.label,occurrence);++ordinal;
            in.push_back({x.time+.1+jitter*z.second,x.label,std::exp(sigma*z.first-sigma*sigma/2),p});
        }
    }
    return in;
}
struct Metrics{int found=0,expected=0,complete=0,events=0,ambiguous=0,duplicates=0,outside=0,order=0,pairs=0;double sumsq=0,maxerr=0;};
Metrics metric(const Row& row,const std::vector<double>& dates,int start,bool filter=false){
    Metrics m;m.expected=12*dates.size();int end=start+dates.size();
    for(auto& train:row){std::map<long long,std::vector<double>> by;int count=0;long long last=-1;bool ordered=true;
        for(auto x:train){if(filter&&((x.label>=0&&x.label<start)||(x.label<0&&x.time<dates.front())))continue;
            count++;m.events++;if(x.label<0)m.ambiguous++;else{by[x.label].push_back(x.time);if(x.label<last){m.order++;ordered=false;}last=x.label;if(x.label<start||x.label>=end)m.outside++;}}
        bool complete=count==int(dates.size())&&ordered;
        for(int k=start;k<end;k++){int n=by[k].size();if(n==1)m.found++;else complete=false;if(n>1)m.duplicates+=n-1;}
        m.complete+=complete;
        for(int i=0;i+1<int(dates.size());i++)if(by[start+i].size()==1&&by[start+i+1].size()==1){double gap=dates[i+1]-dates[i];double err=(by[start+i+1][0]-by[start+i][0]-gap)/gap;m.pairs++;m.sumsq+=err*err;m.maxerr=std::max(m.maxerr,std::abs(err));}
    }return m;
}
void json_metric(std::ostream& o,const Metrics& m){o<<"{\"found\":"<<m.found<<",\"expected\":"<<m.expected<<",\"recall\":"<<double(m.found)/m.expected<<",\"complete_lanes\":"<<m.complete<<",\"full_network_word\":"<<(m.complete==12?"true":"false")<<",\"events\":"<<m.events<<",\"ambiguous\":"<<m.ambiguous<<",\"duplicates\":"<<m.duplicates<<",\"outside_labels\":"<<m.outside<<",\"order_violations\":"<<m.order<<",\"interval_pairs\":"<<m.pairs<<",\"relative_rms\":";if(m.pairs)o<<std::sqrt(m.sumsq/m.pairs);else o<<"null";o<<",\"max_relative_error\":"<<m.maxerr<<"}";}
void json_state(std::ostream& o,const State& s){o<<"{\"z\":["<<s.z[0]<<","<<s.z[1]<<","<<s.z[2]<<"],\"b\":"<<s.b<<",\"q\":"<<s.q<<",\"time\":"<<s.time<<",\"phase\":"<<s.phase<<"}";}
Train cell_run(const std::vector<Pulse>& in,const State& initial,bool frozen,bool ungated,long long tail,State& terminal,double* diag){
    std::vector<Output> out(2*in.size()+16);State before;long long moves;char err[512];
    int n=point_cell(in.data(),in.size(),&initial,frozen,ungated,0.,out.data(),out.size(),&terminal,&before,&moves,diag,tail,err,512);
    if(n<0)throw std::runtime_error(err);out.resize(n);return out;
}
