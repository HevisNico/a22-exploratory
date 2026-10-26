#include "common.cpp"
#include "calibration.hpp"
using States=std::array<State,1560>;
static const char* COMPONENTS[]={"main_admission","main_fast","main_slow","aux_admission","aux_mark","aux_silent","aux_error","gain_learning","b_learning"};
Lineage singleton(int index){Lineage b{};b[index/64]=uint64_t(1)<<(index%64);return b;}
int bitcount(const Lineage& b){int n=0;for(auto x:b)n+=__builtin_popcountll(x);return n;}
std::vector<int> indices(const Lineage& b){std::vector<int> out;for(int word=0;word<4;word++){uint64_t bits=b[word];while(bits){int bit=__builtin_ctzll(bits);out.push_back(64*word+bit);bits&=bits-1;}}return out;}
struct Probe {int id,layer,lane,port;double time,amplitude;};
States load(const std::string& path){States out;std::ifstream f(path);for(auto& s:out){for(auto& z:s.z)if(!(f>>z))throw std::runtime_error("truncated checkpoint");if(!(f>>s.b>>s.q>>s.time>>s.phase)||s.phase!=0)throw std::runtime_error("invalid checkpoint");}return out;}
struct Score {int true_found=0,true_expected=0,complete_lanes=0,false_reached=0,false_lane_hits=0,probe_count=0,events=0,pure_false_events=0,mixed_events=0,unattributed=0,order_errors=0;};
Score score(const Row& row,int true_count,int probe_count){
 Score out;out.true_expected=12*true_count;out.probe_count=probe_count;std::array<bool,24> reached{};
 for(auto& train:row){std::array<int,128> pure{},all{};std::array<bool,24> lane_reached{};int last=-1;bool ordered=true;
  for(auto e:train){out.events++;auto ids=indices(e.lineage);if(ids.empty()){out.unattributed++;continue;}bool has_true=false,has_false=false;
   for(int id:ids){if(id<128){all[id]++;has_true=true;}else if(id<128+probe_count){lane_reached[id-128]=true;reached[id-128]=true;has_false=true;}else throw std::runtime_error("invalid provenance id");}
   if(ids.size()==1&&ids[0]<128){pure[ids[0]]++;if(ids[0]<last){ordered=false;out.order_errors++;}last=ids[0];}
   if(has_false&&!has_true)out.pure_false_events++;
   if(ids.size()>1)out.mixed_events++;
  }
  bool complete=true_count>0&&ordered;for(int k=0;k<true_count;k++){bool ok=pure[k]==1&&all[k]==1;out.true_found+=ok;complete&=ok;}
  out.complete_lanes+=complete;for(bool r:lane_reached)out.false_lane_hits+=r;
 }
 for(bool r:reached)out.false_reached+=r;return out;
}
void json_score(std::ostream& o,const Score& s){o<<"{\"true_found\":"<<s.true_found<<",\"true_expected\":"<<s.true_expected<<",\"complete_lanes\":"<<s.complete_lanes<<",\"full_true_word\":"<<(s.complete_lanes==12?"true":"false")<<",\"false_reached\":"<<s.false_reached<<",\"probe_count\":"<<s.probe_count<<",\"false_lane_hits\":"<<s.false_lane_hits<<",\"events\":"<<s.events<<",\"pure_false_events\":"<<s.pure_false_events<<",\"mixed_events\":"<<s.mixed_events<<",\"unattributed_events\":"<<s.unattributed<<",\"order_errors\":"<<s.order_errors<<"}";}
int main(int argc,char** argv){try{
 if(argc!=7)throw std::runtime_error("seed level condition scenario input_directory output_json");
 int seed=std::stoi(argv[1]),level=std::stoi(argv[2]);std::string condition=argv[3],scenario=argv[4],inputdir=argv[5],dest=argv[6];
 std::vector<std::string> conditions={"learned","ungated","uniform4","uniform2","directional","directional_tail"};
 std::vector<std::string> scenarios={"clean","lateral_050","lateral_100","central_050","noise_only","noise_mixed","wrong_lane"};
 if(std::find(conditions.begin(),conditions.end(),condition)==conditions.end()||std::find(scenarios.begin(),scenarios.end(),scenario)==scenarios.end())throw std::runtime_error("unknown condition/scenario");
 auto normal=load(inputdir+"/L"+std::to_string(level)+"_s"+std::to_string(seed)+"_gate_on.states");
 auto states=condition=="ungated"?load(inputdir+"/L"+std::to_string(level)+"_s"+std::to_string(seed)+"_gate_off.states"):normal;
 for(int layer=1;layer<=130;layer++)for(int lane=0;lane<12;lane++){
  auto& s=states[(layer-1)*12+lane];s.q=R;s.time=0;s.phase=0;
  for(int p=0;p<3;p++){
   if(condition=="uniform4"||condition=="uniform2")s.z[p]=std::log(condition=="uniform4"?4.:2.);
   if(condition=="directional"||(condition=="directional_tail"&&layer>=7))s.z[p]=std::log(p==1?STATIC_CENTRAL:STATIC_LATERAL);
  }
 }
 const double sigma=level<0?0:.05*(level+1),jitter=level<0?0:.015*(level+1);FREEZE_GAINS=true;ENERGY_ENABLED=true;
 std::vector<double> dates={0};double gaps[]={20,22,21,24,20,23};for(int i=1;i<128;i++)dates.push_back(dates.back()+gaps[(i-1)%6]);
 bool only_noise=scenario=="noise_only";int true_count=only_noise?0:128,probe_count=scenario=="clean"?0:24;
 Row row;if(!only_noise)for(int i=0;i<128;i++)row[0].push_back({dates[i],3000000+i,singleton(i)});
 std::vector<Probe> probes;
 for(int j=0;j<probe_count;j++){
  int gap=3+5*j,lane=j%12,port=(j/12)%2==0?0:2,layer=7;double amp=scenario=="lateral_100"?1.:.5;
  double t=.5*(dates[gap]+dates[gap+1])+3.;
  uint64_t key=mix(uint64_t(seed+137)^mix(uint64_t(level+2))^mix(uint64_t(j+7141)));
  if(scenario=="central_050")port=1;
  if(scenario=="noise_only"||scenario=="noise_mixed"){lane=std::min(11,int(12*uniform(key)));port=std::min(2,int(3*uniform(key^0x143)));amp=.3+.7*uniform(key^0x287);t+=2*uniform(key^0x391)-1.;}
  if(scenario=="wrong_lane"){layer=0;lane=6;port=-1;amp=1.;t-=3.;row[6].push_back({t,4000000+j,singleton(128+j)});}
  else{auto z=noise(seed,layer,lane,port,9101,4000000+j,0);t+=jitter*z.second;amp*=std::exp(sigma*z.first-.5*sigma*sigma);}
  probes.push_back({j,layer,lane,port,t,amp});
 }
 std::array<double,9> work{};double lower_bound=100,min_E=100,pump=0,terminal_E=0;long long input_count=0,fire_count=0;int bracket_checked=0,bracket_violations=0;double min_clearance=1e300;
 std::ostringstream o;o<<std::setprecision(17)<<"{\"seed\":"<<seed<<",\"level\":"<<level<<",\"condition\":\""<<condition<<"\",\"scenario\":\""<<scenario<<"\",\"static_central\":"<<STATIC_CENTRAL<<",\"static_lateral\":"<<STATIC_LATERAL<<",\"probes\":[";
 for(size_t j=0;j<probes.size();j++){auto p=probes[j];if(j)o<<",";o<<"["<<p.id<<","<<p.layer<<","<<p.lane<<","<<p.port<<","<<p.time<<","<<p.amplitude<<"]";}o<<"],\"layers\":[";
 for(int layer=1;layer<=130;layer++){
  Row next;
  for(int lane=0;lane<12;lane++){
   auto in=incoming(row,seed,layer,lane,8001,sigma,jitter);
   for(auto p:probes)if(p.layer==layer&&p.lane==lane){
    int gap=3+5*p.id;double prev=-1e300,following=1e300;bool before=false,after=false;
    for(auto x:in){if(x.label==3000000+gap){prev=std::max(prev,x.time+1.);before=true;}if(x.label==3000000+gap+1){following=std::min(following,x.time);after=true;}}
    if(before&&after){bracket_checked++;double clearance=std::min(p.time-prev,following-p.time-1.);min_clearance=std::min(min_clearance,clearance);if(clearance<=0)bracket_violations++;}
    in.push_back({p.time,4000000+p.id,p.amplitude,p.port,singleton(128+p.id)});
   }
   std::sort(in.begin(),in.end(),[](auto a,auto b){if(a.port!=b.port)return a.port<b.port;if(a.time!=b.time)return a.time<b.time;return a.label<b.label;});
   auto initial=states[(layer-1)*12+lane];State terminal;double diag[8];next[lane]=cell_run(in,initial,true,false,3000000,terminal,diag);
   for(int p=0;p<3;p++)if(terminal.z[p]!=initial.z[p])throw std::runtime_error("frozen gain moved");if(terminal.b!=initial.b)throw std::runtime_error("frozen b moved");
   auto e=LAST_ENERGY;for(int p=0;p<9;p++)work[p]+=e.work[p];lower_bound=std::min(lower_bound,e.lower_bound);min_E=std::min(min_E,e.min_event);pump+=e.pump;terminal_E+=e.E;input_count+=in.size();fire_count+=next[lane].size();
  }
  if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"score\":";json_score(o,score(next,true_count,probe_count));o<<"}";row=std::move(next);
 }
 double total=0;for(double v:work)total+=v;
 o<<"],\"score\":";json_score(o,score(row,true_count,probe_count));o<<",\"energy\":{\"work_total\":"<<total<<",\"work_components\":{";
 for(int i=0;i<9;i++){if(i)o<<",";o<<"\""<<COMPONENTS[i]<<"\":"<<work[i];}
 o<<"},\"continuous_E_lower_bound\":"<<lower_bound<<",\"min_E_at_events\":"<<min_E<<",\"pump_supplied\":"<<pump<<",\"sum_terminal_E\":"<<terminal_E<<",\"cells\":1560,\"input_pulses\":"<<input_count<<",\"fires\":"<<fire_count<<"},\"injection_timing\":{\"brackets_checked\":"<<bracket_checked<<",\"violations\":"<<bracket_violations<<",\"minimum_clearance\":";if(bracket_checked)o<<min_clearance;else o<<"null";
 o<<"},\"output_events\":[";for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";for(size_t j=0;j<row[lane].size();j++){if(j)o<<",";auto e=row[lane][j];o<<"["<<e.time<<","<<e.label<<",[";auto ids=indices(e.lineage);for(size_t k=0;k<ids.size();k++){if(k)o<<",";o<<ids[k];}o<<"]]";}o<<"]";}o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";
 std::string temp=dest+".tmp";std::ofstream f(temp);f<<o.str();f.close();if(!f||std::rename(temp.c_str(),dest.c_str()))throw std::runtime_error("write failed");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
