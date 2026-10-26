#include "common.cpp"
using States=std::array<State,1560>;
static const char* COMPONENTS[]={"main_admission","main_fast","main_slow","aux_admission","aux_mark","aux_silent","aux_error","gain_learning","b_learning"};
struct NetworkEnergy{
 std::array<double,9> work{};double min_event=100,lower_bound=100,max_power=0,terminal_E=0,pump=0,dz=0,db=0;long long inputs=0,fires=0;int cells=0;
 void add(const EnergyBudget& x,const State& before,const State& after,int incoming,int outgoing){for(int i=0;i<9;i++)work[i]+=x.work[i];min_event=std::min(min_event,x.min_event);lower_bound=std::min(lower_bound,x.lower_bound);max_power=std::max(max_power,x.max_power);terminal_E+=x.E;pump+=x.pump;for(int i=0;i<3;i++)dz+=after.z[i]-before.z[i];db+=after.b-before.b;inputs+=incoming;fires+=outgoing;cells++;}
 double total()const{double v=0;for(auto x:work)v+=x;return v;}
};
void json_energy(std::ostream& o,const NetworkEnergy& e){o<<"{\"work_components\":{";for(int i=0;i<9;i++){if(i)o<<",";o<<"\""<<COMPONENTS[i]<<"\":"<<e.work[i];}o<<"},\"work_total\":"<<e.total()<<",\"min_E_at_events\":"<<e.min_event<<",\"continuous_E_lower_bound\":"<<e.lower_bound<<",\"max_observed_power\":"<<e.max_power<<",\"sum_terminal_E\":"<<e.terminal_E<<",\"pump_supplied\":"<<e.pump<<",\"delta_log_gains\":"<<e.dz<<",\"delta_b\":"<<e.db<<",\"input_pulses\":"<<e.inputs<<",\"fires\":"<<e.fires<<",\"cells\":"<<e.cells<<"}";}
States load(const std::string& path){States out;std::ifstream f(path);for(auto& s:out){for(auto& z:s.z)if(!(f>>z))throw std::runtime_error("truncated checkpoint");if(!(f>>s.b>>s.q>>s.time>>s.phase)||s.phase!=0)throw std::runtime_error("invalid checkpoint");}return out;}
void save(const std::string& path,const States& states){std::ofstream f(path);f<<std::setprecision(17);for(auto& s:states){for(double z:s.z)f<<z<<" ";f<<s.b<<" "<<s.q<<" "<<s.time<<" "<<s.phase<<"\n";}}
int main(int argc,char** argv){try{
 if(argc!=8)throw std::runtime_error("mode seed level condition checkpoint output enabled");
 std::string mode=argv[1],condition=argv[4],checkpoint=argv[5],destination=argv[6];int seed=std::stoi(argv[2]),level=std::stoi(argv[3]);ENERGY_ENABLED=std::stoi(argv[7]);double sigma=level<0?0:.05*(level+1),jitter=level<0?0:.015*(level+1);
 bool training=mode=="train",uniform=condition=="uniform4_frozen";
 bool ungated=condition=="gate_off"||condition=="trained_off";
 bool frozen=condition=="normal_frozen"||condition=="uniform4_frozen";FREEZE_GAINS=frozen;
 States states;if(!training&&checkpoint!="-")states=load(checkpoint);
 else for(auto& s:states)s={{std::log(uniform?4.:.3),std::log(uniform?4.:1.2),std::log(uniform?4.:.3)},.08,.1,0.,0};
 if(!training)for(auto& s:states){s.q=R+(s.q-R)*std::exp(-K*3080.);if(uniform)for(double& z:s.z)z=std::log(4.);}
 int count=training?2048:128,label0=training?0:3000000,stage=training?0:8001;Row row;std::vector<double> dates={0};double gaps[]={1,1.1,1.05,1.2,1,1.15};for(int i=1;i<count;i++)dates.push_back(training?8.*i:dates.back()+20*gaps[(i-1)%6]);for(int i=0;i<count;i++)row[0].push_back({dates[i],label0+i});
 std::ostringstream o;o<<std::setprecision(17)<<"{\"mode\":\""<<mode<<"\",\"seed\":"<<seed<<",\"level\":"<<level<<",\"condition\":\""<<condition<<"\",\"energy_enabled\":"<<(ENERGY_ENABLED?"true":"false")<<",\"layers\":[";NetworkEnergy total;
 for(int layer=1;layer<=130;layer++){
  Row next;NetworkEnergy le;
  for(int lane=0;lane<12;lane++){
   State initial=states[(layer-1)*12+lane],terminal;double diag[8];auto in=incoming(row,seed,layer,lane,stage,sigma,jitter);next[lane]=cell_run(in,initial,frozen,ungated,label0,terminal,diag);
   if(terminal.phase!=0)throw std::runtime_error("nonready terminal");
   auto e=LAST_ENERGY;
   le.add(e,initial,terminal,in.size(),next[lane].size());total.add(e,initial,terminal,in.size(),next[lane].size());states[(layer-1)*12+lane]=terminal;
  }
  if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"metric\":";if(training){std::vector<double> tail(dates.end()-128,dates.end());json_metric(o,metric(next,tail,count-128,true));}else json_metric(o,metric(next,dates,label0));o<<",\"energy\":";json_energy(o,le);o<<"}";row=std::move(next);
 }
 o<<"],\"energy\":";json_energy(o,total);o<<",\"output_events\":[";for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";for(int i=0;i<int(row[lane].size());i++){if(i)o<<",";o<<"["<<row[lane][i].time<<","<<row[lane][i].label<<"]";}o<<"]";}o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";
 std::string tmp=destination+".tmp";std::ofstream f(tmp);f<<o.str();f.close();if(!f)throw std::runtime_error("write failed");if(std::rename(tmp.c_str(),destination.c_str()))throw std::runtime_error("rename failed");
 save(destination+".states",states);
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
