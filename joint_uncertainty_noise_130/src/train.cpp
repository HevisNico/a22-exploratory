#include "field.hpp"
int main(int argc,char** argv){try{
 if(argc!=5)throw std::runtime_error("seed level field output");
 int seed=std::stoi(argv[1]),level=std::stoi(argv[2]);auto field=load_field(argv[3]);std::string dest=argv[4];
 bool frozen=false;FREEZE_GAINS=false;ENERGY_ENABLED=true;
 double sigma=.05*(level+1),jitter=.015*(level+1);
 Row row;for(int i=0;i<2048;i++)row[0].push_back({8.*i,i});
 std::array<State,1560> states;for(auto& s:states)s={{std::log(.3),std::log(1.2),std::log(.3)},.08,.1,0,0};
 std::array<double,9> work{};double lower=100;long long inputs=0,fires=0;
 std::ostringstream o;o<<std::setprecision(17)<<"{\"layer_event_counts\":[";
 Metrics tail;
 for(int layer=1;layer<=130;layer++){
  Row next;long long events=0;
  for(int lane=0;lane<12;lane++){
   auto idx=(layer-1)*12+lane;PHYS=field[idx];auto in=incoming(row,seed,layer,lane,0,sigma,jitter);
   State terminal;double diag[8];next[lane]=cell_run(in,states[idx],false,false,1920,terminal,diag);
   if(terminal.phase!=0)throw std::runtime_error("training terminal not ready");states[idx]=terminal;
   for(int p=0;p<9;p++)work[p]+=LAST_ENERGY.work[p];lower=std::min(lower,LAST_ENERGY.lower_bound);inputs+=in.size();fires+=next[lane].size();events+=next[lane].size();
  }
  if(layer>1)o<<",";o<<events;row=std::move(next);
 }
 std::vector<double> dates;for(int i=1920;i<2048;i++)dates.push_back(8.*i);
 o<<"],\"final_training_metric\":";json_metric(o,metric(row,dates,1920,true));
 static const char* names[]={"main_admission","main_fast","main_slow","aux_admission","aux_mark","aux_silent","aux_error","gain_learning","b_learning"};
 double total=0;for(double w:work)total+=w;
 o<<",\"energy\":{\"work_total\":"<<total<<",\"continuous_E_lower_bound\":"<<lower<<",\"input_pulses\":"<<inputs<<",\"fires\":"<<fires<<",\"cells\":1560,\"work_components\":{";
 for(int i=0;i<9;i++){if(i)o<<",";o<<"\""<<names[i]<<"\":"<<work[i];}o<<"}}}";
 std::ofstream out(dest);out<<o.str();out.close();if(!out)throw std::runtime_error("training output");
 std::ofstream st(dest+".states");st<<std::setprecision(17);for(auto& s:states){for(double z:s.z)st<<z<<" ";st<<s.b<<" "<<s.q<<" "<<s.time<<" "<<s.phase<<"\n";}
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
