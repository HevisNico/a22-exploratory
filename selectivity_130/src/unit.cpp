#define main experiment_entry
#include "experiment.cpp"
#undef main
#include <cassert>
int main(){
 Row r;Lineage mixed=singleton(0);mixed[2]|=singleton(128)[2];
 r[0]={{0,3000000,singleton(0)},{1,4000000,singleton(128)},{2,-1,mixed}};
 auto s=score(r,1,1);assert(s.false_reached==1&&s.false_lane_hits==1&&s.true_found==0&&s.mixed_events==1&&s.pure_false_events==1);
 Row clean;for(auto& lane:clean)lane.push_back({0,3000000,singleton(0)});s=score(clean,1,0);assert(s.true_found==12&&s.complete_lanes==12&&s.false_reached==0);
 for(double gain:{.9960350768196247,2.,4.})for(double amp:{.4,.5,1.}){
  State st={{std::log(gain),std::log(gain),std::log(gain)},1.1,.1,0,0};State end;double diag[8];std::vector<Pulse> in={{.1,4000000,amp,0,singleton(128)}};
  auto out=cell_run(in,st,true,false,0,end,diag);double h=A/(A-K)*(std::exp(-K)-std::exp(-A));bool fires=.1+gain*amp*h>=1.;assert(out.size()==size_t(fires));if(fires)assert(out[0].lineage==singleton(128));
 }
 State st={{std::log(1.2),std::log(1.2),std::log(1.2)},1.1,.1,0,0};State end;double diag[8];std::vector<Pulse> in={{.1,3000000,1.,0,singleton(0)},{.1,4000000,1.,1,singleton(128)}};
 auto out=cell_run(in,st,true,false,0,end,diag);assert(out.size()==1&&out[0].label==-1&&out[0].lineage==mixed);
 std::cout<<"PASS: analytic single-pulse thresholds, lineage unions, contamination scoring and pure truth recovery\n";
}
