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
int main(int argc,char** argv){try{
    if(argc!=9)throw std::runtime_error("seed rule sigma jitter N prefix checkpoint testlevel");
    int seed=std::stoi(argv[1]),N=std::stoi(argv[5]);bool ungated=std::string(argv[2])=="ungated";double sigma=std::stod(argv[3]),jitter=std::stod(argv[4]);std::string prefix=argv[6],checkpoint=argv[7];int target=std::stoi(argv[8]);
    std::ostringstream o;o<<std::setprecision(17);o<<"{\"seed\":"<<seed<<",\"rule\":\""<<argv[2]<<"\",\"sigma\":"<<sigma<<",\"jitter\":"<<jitter<<",\"training_N\":"<<N<<",\"training\":[";
    std::array<State,1560> states;
    if(checkpoint=="-"){
        Row row;for(int i=0;i<N;i++)row[0].push_back({8.*i,i});
        std::ofstream statefile(prefix+".states");statefile<<std::setprecision(17);
        std::vector<double> taildates;for(int i=N-128;i<N;i++)taildates.push_back(8.*i);
        for(int layer=1;layer<=130;layer++){
            Row next;std::vector<std::array<double,6>> diagnostics(12);
            for(int lane=0;lane<12;lane++){
                State init={{std::log(.3),std::log(1.2),std::log(.3)},.08,.1,0.,0};auto& state=states[(layer-1)*12+lane];
                next[lane]=cell_run(incoming(row,seed,layer,lane,0,sigma,jitter),init,false,ungated,N-128,state,diagnostics[lane].data());
                for(double z:state.z)statefile<<z<<' ';statefile<<state.b<<' '<<state.q<<' '<<state.time<<' '<<state.phase<<'\n';
            }
            if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"tail128\":";json_metric(o,metric(next,taildates,N-128,true));o<<",\"cells\":[";
            for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"{\"state\":";json_state(o,states[(layer-1)*12+lane]);o<<",\"diagnostic\":[";for(int k=0;k<6;k++){if(k)o<<",";o<<diagnostics[lane][k];}o<<"]}";}o<<"]}";row=std::move(next);
        }
    }else{
        std::ifstream f(checkpoint);for(auto& s:states){for(double& z:s.z)f>>z;f>>s.b>>s.q>>s.time>>s.phase;}if(!f)throw std::runtime_error("invalid checkpoint");
    }
    o<<"],\"tests\":[";bool first=true;
    // Matched 24/128 active and frozen; cross-level 128 frozen for normal only.
    for(int level=0;level<3;level++)for(int count:{24,128})for(bool frozen:{false,true}){
        if(level!=target&&(ungated||checkpoint!="-"||count!=128||!frozen))continue;
        double tsigma=.05*(level+1),tjitter=.015*(level+1);Row row;std::vector<double> dates={0.};
        double gaps[6]={1,1.1,1.05,1.2,1,1.15};for(int i=0;i<count-1;i++)dates.push_back(dates.back()+20*gaps[i%6]);
        for(int i=0;i<count;i++)row[0].push_back({dates[i],1000000+i});
        if(!first)o<<",";first=false;o<<"{\"level\":"<<level<<",\"pulses\":"<<count<<",\"frozen\":"<<(frozen?"true":"false")<<",\"layers\":[";
        for(int layer=1;layer<=130;layer++){
            Row next;double delta_z=0,delta_b=0;long long updates=0;double minquiet=1e99;
            for(int lane=0;lane<12;lane++){
                State init=states[(layer-1)*12+lane],terminal;double quiet=4096.+8*(N-128)-init.time;if(quiet<=0)throw std::runtime_error("no quiet interval");minquiet=std::min(minquiet,quiet);init.q=R+(init.q-R)*std::exp(-K*quiet);double diag[6];
                next[lane]=cell_run(incoming(row,seed,layer,lane,count,tsigma,tjitter),init,frozen,ungated,1000000,terminal,diag);
                for(int p=0;p<3;p++)delta_z+=terminal.z[p]-init.z[p];delta_b+=terminal.b-init.b;updates+=diag[0];
            }
            if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"metric\":";json_metric(o,metric(next,dates,1000000));o<<",\"gain_updates\":"<<updates<<",\"delta_z\":"<<delta_z<<",\"delta_b\":"<<delta_b<<",\"minimum_quiet\":"<<minquiet<<"}";row=std::move(next);
        }
        o<<"],\"output_events\":[";for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";bool f=true;for(auto x:row[lane]){if(!f)o<<",";f=false;o<<"["<<x.time<<","<<x.label<<"]";}o<<"]";}o<<"]}";
    }
    o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";std::string data=o.str();std::ofstream final(prefix+".json.tmp",std::ios::binary);final.write(data.data(),data.size());final.close();if(!final)throw std::runtime_error("output write failed");if(std::rename((prefix+".json.tmp").c_str(),(prefix+".json").c_str()))throw std::runtime_error("output rename failed");std::cout<<prefix<<" OK\n";
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
