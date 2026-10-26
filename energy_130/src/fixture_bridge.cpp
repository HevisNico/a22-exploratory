#include "common.cpp"
int main(){try{
 State init;int frozen,ungated,n;std::cin>>init.z[0]>>init.z[1]>>init.z[2]>>init.b>>init.q>>frozen>>ungated>>n;
 init.time=0.;init.phase=0;std::vector<Pulse> in(n);for(auto& p:in)std::cin>>p.time>>p.label>>p.amp>>p.port;
 if(!std::cin)throw std::runtime_error("invalid fixture");FREEZE_GAINS=frozen;
 State terminal;double diag[8];auto out=cell_run(in,init,frozen,ungated,0,terminal,diag);auto e=LAST_ENERGY;
 std::cout<<std::setprecision(17)<<"{\"state\":";json_state(std::cout,terminal);
 std::cout<<",\"E\":"<<e.E<<",\"pump\":"<<e.pump<<",\"work\":[";
 for(int i=0;i<9;i++){if(i)std::cout<<",";std::cout<<e.work[i];}
 std::cout<<"],\"events\":[";for(size_t i=0;i<out.size();i++){if(i)std::cout<<",";std::cout<<out[i].time;}std::cout<<"]}";
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
