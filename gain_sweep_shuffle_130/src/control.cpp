#include "common.cpp"
#include <cstring>
int main(int argc,char** argv){try{
 if(argc!=8)throw std::runtime_error("checkpoint seed level bmode gain output count");
 std::string checkpoint=argv[1],bmode=argv[4];int seed=std::stoi(argv[2]),level=std::stoi(argv[3]),count=std::stoi(argv[7]);double gain=std::stod(argv[5]);bool loaded=checkpoint!="-",frozen=bmode!="adaptive";FREEZE_GAINS=true;
 std::array<State,1560> states;
 if(loaded){std::ifstream f(checkpoint);for(auto& st:states){for(auto& z:st.z)if(!(f>>z))throw std::runtime_error("truncated gains");if(!(f>>st.b>>st.q>>st.time>>st.phase)||st.phase!=0)throw std::runtime_error("invalid checkpoint");}}
 else for(auto& st:states)st={{std::log(gain),std::log(gain),std::log(gain)},bmode=="fixed_high"?1.1:.08,.1,0.,0};
 double sigma=level<0?0:.05*(level+1),jitter=level<0?0:.015*(level+1);Row row;std::vector<double> dates={0};double gaps[]={1,1.1,1.05,1.2,1,1.15};for(int i=1;i<count;i++)dates.push_back(dates.back()+20*gaps[(i-1)%6]);for(int i=0;i<count;i++)row[0].push_back({dates[i],2000000+i});
 std::ostringstream o;o<<std::setprecision(17)<<"{\"seed\":"<<seed<<",\"level\":"<<level<<",\"bmode\":\""<<bmode<<"\",\"uniform_gain\":"<<gain<<",\"count\":"<<count<<",\"layers\":[";
 double max_gain_change=0,max_b_change=0,bsum=0;int violated=0;
 for(int layer=1;layer<=130;layer++){
  Row next;
  for(int lane=0;lane<12;lane++){
   State init=states[(layer-1)*12+lane],terminal;
   if(loaded)init.q=R+(init.q-R)*std::exp(-K*3080.);
   double diag[8]={};next[lane]=cell_run(incoming(row,seed,layer,lane,7001,sigma,jitter),init,frozen,false,2000000,terminal,diag);
   for(int p=0;p<3;p++){max_gain_change=std::max(max_gain_change,std::abs(terminal.z[p]-init.z[p]));if(terminal.z[p]!=init.z[p])violated++;}
   max_b_change=std::max(max_b_change,std::abs(terminal.b-init.b));bsum+=terminal.b;
   if(terminal.phase!=0)throw std::runtime_error("terminal phase not READY");
  }
  if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"metric\":";json_metric(o,metric(next,dates,2000000));o<<"}";row=std::move(next);
 }
 if(violated)throw std::runtime_error("gain freeze violated");if(frozen&&max_b_change!=0)throw std::runtime_error("b freeze violated");
 o<<"],\"max_log_gain_change\":"<<max_gain_change<<",\"max_b_change\":"<<max_b_change<<",\"final_mean_b\":"<<bsum/1560<<",\"output_events\":[";
 for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";for(int i=0;i<int(row[lane].size());i++){if(i)o<<",";o<<"["<<row[lane][i].time<<","<<row[lane][i].label<<"]";}o<<"]";}o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";
 std::string path=argv[6],tmp=path+".tmp",data=o.str();std::ofstream f(tmp,std::ios::binary);f<<data;f.close();if(!f)throw std::runtime_error("write failure");if(std::rename(tmp.c_str(),path.c_str()))throw std::runtime_error("rename failed");
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
