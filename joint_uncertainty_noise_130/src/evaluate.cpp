#include "field.hpp"
using States=std::array<State,1560>;
struct Probe {int id,layer,lane,port;double time,amplitude;};
Lineage singleton(int i){Lineage x{};x[i/64]=uint64_t(1)<<(i%64);return x;}
States load(const std::string& path){States s;std::ifstream f(path);for(auto& x:s){for(auto& z:x.z)if(!(f>>z))throw std::runtime_error("checkpoint gain");if(!(f>>x.b>>x.q>>x.time>>x.phase)||x.phase!=0)throw std::runtime_error("checkpoint state");x.q=R;x.time=0;x.phase=0;}return s;}
int main(int argc,char** argv){try{
 if(argc!=9)throw std::runtime_error("seed level checkpoint scenario mode omitted_probe output");
 int seed=std::stoi(argv[1]),level=std::stoi(argv[2]),omit=std::stoi(argv[6]);
 std::string scenario=argv[4],mode=argv[5],dest=argv[7];
 if(level<-1||level>2||omit < -1||omit>=24)throw std::runtime_error("invalid argument");
 if(mode!="clean"&&mode!="mixed"&&mode!="alone")throw std::runtime_error("invalid mode");
 if(scenario!="lateral_050"&&scenario!="lateral_100"&&scenario!="central_050"&&scenario!="noise"&&scenario!="wrong_lane")throw std::runtime_error("invalid scenario");

 auto field=load_field(argv[8]); auto states=load(argv[3]);FREEZE_GAINS=true;ENERGY_ENABLED=true;GAIN_CAP=4.;
 double sigma=.05*(level+1),jitter=.015*(level+1);double gaps[]={20,22,21,24,20,23};
 std::vector<double> dates{0};for(int i=1;i<128;i++)dates.push_back(dates.back()+gaps[(i-1)%6]);
 Row row;if(mode!="alone")for(int i=0;i<128;i++)row[0].push_back({dates[i],3000000+i,singleton(i)});
 std::vector<Probe> probes;
 if(mode!="clean")for(int j=0;j<24;j++){
  if(j==omit)continue;
  int gap=3+5*j,lane=j%12,port=j<12?0:2,layer=7;double amp=scenario=="lateral_100"?1.:.5;
  double t=.5*(dates[gap]+dates[gap+1])+3.;uint64_t key=mix(uint64_t(seed+137)^mix(uint64_t(level+2))^mix(uint64_t(j+7141)));
  if(scenario=="central_050")port=1;
  if(scenario=="noise"){lane=std::min(11,int(12*uniform(key)));port=std::min(2,int(3*uniform(key^0x143)));amp=.3+.7*uniform(key^0x287);t+=2*uniform(key^0x391)-1.;}
  if(scenario=="wrong_lane"){layer=0;lane=6;port=-1;amp=1.;t-=3.;row[6].push_back({t,4000000+j,singleton(128+j)});}
  else{auto z=noise(seed,layer,lane,port,9101,4000000+j,0);t+=jitter*z.second;amp*=std::exp(sigma*z.first-.5*sigma*sigma);}
  probes.push_back({j,layer,lane,port,t,amp});
 }
 std::array<double,9> work{};double lower=100,minE=100,pump=0,terminalE=0;long long inputs=0,fires=0;int brackets=0,violations=0;
 std::ostringstream o;o<<std::setprecision(17)<<"{\"seed\":"<<seed<<",\"level\":"<<level<<",\"scenario\":\""<<scenario<<"\",\"mode\":\""<<mode<<"\",\"omitted_probe\":"<<omit<<",\"probes\":[";
 for(size_t j=0;j<probes.size();j++){auto p=probes[j];if(j)o<<",";o<<"["<<p.id<<","<<p.layer<<","<<p.lane<<","<<p.port<<","<<p.time<<","<<p.amplitude<<"]";}
 o<<"],\"layer_event_counts\":[";
 for(int layer=1;layer<=130;layer++){
  Row next;long long events=0;
  for(int lane=0;lane<12;lane++){
   auto in=incoming(row,seed,layer,lane,8001,sigma,jitter);
   for(auto p:probes)if(p.layer==layer&&p.lane==lane){
    int gap=3+5*p.id;double prev=-1e300,after=1e300;bool a=false,b=false;
    for(auto x:in){if(x.label==3000000+gap){prev=std::max(prev,x.time+1.);a=true;}if(x.label==3000000+gap+1){after=std::min(after,x.time);b=true;}}
    if(a&&b){brackets++;if(std::min(p.time-prev,after-p.time-1.)<=0)violations++;}
    in.push_back({p.time,4000000+p.id,p.amplitude,p.port,singleton(128+p.id)});
   }
   std::sort(in.begin(),in.end(),[](auto a,auto b){if(a.port!=b.port)return a.port<b.port;if(a.time!=b.time)return a.time<b.time;return a.label<b.label;});
   PHYS=field[(layer-1)*12+lane]; auto initial=states[(layer-1)*12+lane];State terminal;double diag[8];next[lane]=cell_run(in,initial,true,false,3000000,terminal,diag);
   for(int p=0;p<3;p++)if(initial.z[p]!=terminal.z[p])throw std::runtime_error("gain moved");if(initial.b!=terminal.b)throw std::runtime_error("b moved");
   auto e=LAST_ENERGY;for(int p=0;p<9;p++)work[p]+=e.work[p];lower=std::min(lower,e.lower_bound);minE=std::min(minE,e.min_event);pump+=e.pump;terminalE+=e.E;inputs+=in.size();fires+=next[lane].size();events+=next[lane].size();
  }
  if(layer>1)o<<",";o<<events;row=std::move(next);
 }
 static const char* names[]={"main_admission","main_fast","main_slow","aux_admission","aux_mark","aux_silent","aux_error","gain_learning","b_learning"};double total=0;for(auto w:work)total+=w;
 o<<"],\"energy\":{\"work_total\":"<<total<<",\"work_components\":{";for(int i=0;i<9;i++){if(i)o<<",";o<<"\""<<names[i]<<"\":"<<work[i];}
 o<<"},\"continuous_E_lower_bound\":"<<lower<<",\"min_E_at_events\":"<<minE<<",\"pump_supplied\":"<<pump<<",\"sum_terminal_E\":"<<terminalE<<",\"cells\":1560,\"input_pulses\":"<<inputs<<",\"fires\":"<<fires<<"},\"injection_timing\":{\"brackets_checked\":"<<brackets<<",\"violations\":"<<violations<<"},\"output_events\":[";
 for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";for(size_t j=0;j<row[lane].size();j++){if(j)o<<",";auto e=row[lane][j];o<<"["<<e.time<<","<<e.label<<",[";bool first=true;for(int word=0;word<4;word++){uint64_t bits=e.lineage[word];while(bits){int bit=__builtin_ctzll(bits);if(!first)o<<",";first=false;o<<64*word+bit;bits&=bits-1;}}o<<"]]";}o<<"]";}
 o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";std::string tmp=dest+".tmp";std::ofstream f(tmp);f<<o.str();f.close();if(!f||std::rename(tmp.c_str(),dest.c_str()))throw std::runtime_error("output write failed");
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
