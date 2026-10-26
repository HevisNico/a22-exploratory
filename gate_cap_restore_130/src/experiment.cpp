#include "common.cpp"
using States=std::array<State,1560>;
States load(const std::string& path){States s;std::ifstream f(path);for(auto& x:s){for(auto& z:x.z)f>>z;f>>x.b>>x.q>>x.time>>x.phase;if(x.phase!=0)throw std::runtime_error("not READY");}if(!f)throw std::runtime_error("bad checkpoint");return s;}
void stats(std::ostream& o,const States& s){double sum=0,zsum=0,b=0,mx=0;int caps=0;for(auto& x:s){b+=x.b;for(double z:x.z){double g=std::exp(z);sum+=g;zsum+=z;mx=std::max(mx,g);caps+=z>=std::log(GAIN_CAP)-1e-10;}}o<<"{\"mean_gain\":"<<sum/4680<<",\"max_gain\":"<<mx<<",\"zsum\":"<<zsum<<",\"cap_fraction\":"<<caps/4680.<<",\"mean_b\":"<<b/1560<<"}";}
int main(int argc,char** argv){try{
 if(argc!=9)throw std::runtime_error("checkpoint seed sigma jitter cap rule output validation");
 auto states=load(argv[1]);int seed=std::stoi(argv[2]);double sigma=std::stod(argv[3]),jitter=std::stod(argv[4]);GAIN_CAP=std::stod(argv[5]);std::string rule=argv[6];bool validation=std::stoi(argv[8]);
 std::ofstream o(argv[7]);o<<std::setprecision(17)<<"{\"seed\":"<<seed<<",\"sigma\":"<<sigma<<",\"jitter\":"<<jitter<<",\"cap\":"<<GAIN_CAP<<",\"rule\":\""<<rule<<"\",\"initial\":";stats(o,states);o<<",\"blocks\":[";
 int counts[]={1,127,128,256};int cumulative=0;
 for(int block=0;block<(validation?1:4);block++){
  int count=validation?128:counts[block];bool ungated=rule=="ungated"||(rule=="restore"&&block==0);Row row;std::vector<double> dates={0.};double gaps[]={1,1.1,1.05,1.2,1,1.15};for(int i=1;i<count;i++)dates.push_back(dates.back()+20*gaps[(i-1)%6]);for(int i=0;i<count;i++)row[0].push_back({dates[i],1000000+i});
  if(block)o<<",";o<<"{\"count\":"<<count<<",\"ungated\":"<<(ungated?"true":"false")<<",\"layers\":[";
  double dz=0,db=0,rr=0,rp=0;int changed=0;
  for(int layer=1;layer<=130;layer++){
   Row next;
   for(int lane=0;lane<12;lane++){
    auto& st=states[(layer-1)*12+lane];State initial=st,terminal;
    double quiet=validation?4096.+8*(2048-128)-initial.time:3080.;if(quiet<=0)throw std::runtime_error("invalid silence");initial.q=R+(initial.q-R)*std::exp(-K*quiet);double diag[8]={};
    next[lane]=cell_run(incoming(row,seed,layer,lane,validation?128:5000+block,sigma,jitter),initial,false,ungated,1000000,terminal,diag);
    if(terminal.phase!=0)throw std::runtime_error("nonready end");
    for(int p=0;p<3;p++){double d=terminal.z[p]-initial.z[p];if(d< -1e-10||terminal.z[p]>std::log(GAIN_CAP)+1e-10)throw std::runtime_error("gain invariant");dz+=d;changed+=d>1e-10;}db+=terminal.b-initial.b;rr+=diag[6];rp+=diag[7];st=terminal;
   }
   if(layer>1)o<<",";o<<"{\"layer\":"<<layer<<",\"metric\":";json_metric(o,metric(next,dates,1000000));o<<"}";row=std::move(next);
  }
  cumulative+=count;o<<"],\"cumulative_pulses\":"<<cumulative<<",\"delta_z\":"<<dz<<",\"delta_b\":"<<db<<",\"changed_gains\":"<<changed<<",\"requested_ready\":"<<rr<<",\"requested_protected\":"<<rp<<",\"terminal\":";stats(o,states);
  if(validation){o<<",\"events\":[";for(int j=0;j<12;j++){if(j)o<<",";o<<"[";for(int i=0;i<int(row[j].size());i++){if(i)o<<",";o<<"["<<row[j][i].time<<","<<row[j][i].label<<"]";}o<<"]";}o<<"]";}
  o<<"}";
 }
 o<<"],\"status\":\"OK_POINT_NOT_CERTIFIED\"}";if(!o)throw std::runtime_error("write failed");
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
