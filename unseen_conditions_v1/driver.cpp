// Preregistered held-out-condition point experiment. Not an interval certificate.
#ifdef REFERENCE_KERNEL
#include "reference_vendor/field.hpp"
static std::array<double,3> ACTUATION={1.,1.,1.};
#else
#include "vendor/field.hpp"
#endif
#include <numeric>

using States=std::array<State,1560>;
using Actuation=std::array<std::array<double,3>,1560>;

static Actuation load_actuation(const std::string& path){
    Actuation h;std::ifstream f(path);
    for(auto& row:h)for(auto& x:row)if(!(f>>x)||x<.8||x>1.2)
        throw std::runtime_error("invalid actuation field");
    std::string extra;if(f>>extra)throw std::runtime_error("actuation trailing data");return h;
}

static States initial_states(const std::string& mode,const Field& field){
    States s;
    for(int i=0;i<1560;i++){
        s[i]={{std::log(.3),std::log(1.2),std::log(.3)},.08,R,0,0};
        if(mode.rfind("static_",0)==0){
            int id=std::stoi(mode.substr(7)),templ=id/2;if(id<0||id>=12)throw std::runtime_error("candidate ID");
            double g[3];
            if(templ<3){double side[]={1.,1.5,2.};g[0]=g[2]=i<72?3.:side[templ];g[1]=3.;}
            else{double value=templ==3?2.:templ==4?3.:4.;g[0]=g[1]=g[2]=value;}
            for(int p=0;p<3;p++)s[i].z[p]=std::log(std::min(g[p],field[i][p].cap));
            s[i].b=id%2?1.1:.5;
        }
    }
    return s;
}

static States load_states(const std::string& path){
    States s;std::ifstream f(path);
    for(auto& x:s){for(double& z:x.z)if(!(f>>z))throw std::runtime_error("checkpoint gain");
        if(!(f>>x.b>>x.q>>x.time>>x.phase)||x.phase!=0||x.b<.08||x.b>1.1)
            throw std::runtime_error("checkpoint state");}
    std::string extra;if(f>>extra)throw std::runtime_error("checkpoint trailing data");return s;
}

static std::vector<Pulse> shifted_incoming(const Row& row,int seed,int layer,int lane,int stage,int cut_layer,int cut_lane){
    std::vector<Pulse> in;
    for(int p=0;p<3;p++){
        if(layer==cut_layer&&lane==cut_lane&&p==1)continue;
        std::map<long long,int> counts;int ordinal=0;
        for(const auto& e:row[(lane+p+11)%12]){
            int occurrence=counts[e.label]++;
            auto z=noise(seed,layer,lane,p,stage,e.label<0?-1-ordinal:e.label,occurrence);++ordinal;
            in.push_back({e.time+.1+.03*z.second,e.label,std::exp(.1*z.first-.005),p,e.lineage});
        }
    }
    return in;
}

static void block_metrics(std::ostream& o,const Row& row,const std::vector<double>& dates,int offset){
    int n=dates.size(),blocks=(n+127)/128;
    std::vector<bool> complete(blocks,true);
    long long missing=0,duplicate=0,ambiguous=0,outside=0,order=0,events=0,pairs=0;double sumsq=0;
    auto by_time=[&](double time){int block=0;while(block+1<blocks&&time>=dates[(block+1)*128]+15.6)++block;return block;};
    for(const auto& lane:row){
        std::vector<int> count(n,0);std::vector<double> time(n);long long previous=-1;
        for(auto e:lane){
            ++events;long long k=e.label-offset;
            if(k<0||k>=n){complete[by_time(e.time)]=false;if(e.label<0)++ambiguous;else ++outside;continue;}
            ++count[k];time[k]=e.time;
            if(previous>k){++order;complete[k/128]=false;complete[previous/128]=false;}previous=k;
        }
        for(int k=0;k<n;k++){
            if(count[k]!=1)complete[k/128]=false;
            if(count[k]==0)++missing;if(count[k]>1)duplicate+=count[k]-1;
        }
        for(int k=0;k+1<n;k++)if(count[k]==1&&count[k+1]==1){double expected=dates[k+1]-dates[k];double e=(time[k+1]-time[k]-expected)/expected;sumsq+=e*e;++pairs;}
    }
    o<<"\"words\":[";for(int k=0;k<blocks;k++){if(k)o<<",";o<<(complete[k]?"true":"false");}
    o<<"],\"complete_words\":"<<std::count(complete.begin(),complete.end(),true)
     <<",\"expected_words\":"<<blocks<<",\"missing_labels\":"<<missing<<",\"duplicate_labels\":"<<duplicate
     <<",\"ambiguous_events\":"<<ambiguous<<",\"outside_labels\":"<<outside<<",\"order_violations\":"<<order
     <<",\"final_events\":"<<events<<",\"interval_pairs\":"<<pairs<<",\"relative_interval_rms\":";
    if(pairs)o<<std::sqrt(sumsq/pairs);else o<<"null";
}

static void self_test(){
    for(auto& p:PHYS)p={4.,LM,std::log(8.)/1.06,LE,M};ENERGY_ENABLED=true;FREEZE_GAINS=true;
    std::cout<<std::setprecision(17)<<"{\"status\":\"PASS\",\"isolated_gain_checks\":[";
    bool first=true;double last_charge=-1.;
    for(double h:{.8,1.,1.2}){
        ACTUATION={h,h,h};State before={{std::log(.3),std::log(.3),std::log(.3)},1.1,R,0,0},after;double diag[8];
        std::vector<Pulse> in{{0.,0,1.,1,{}}};auto out=cell_run(in,before,true,false,0,after,diag);
        double expected=.75*.3*h;
        if(!out.empty()||std::abs(LAST_ENERGY.work[0]-expected)>1e-11)throw std::runtime_error("isolated main gain/work check");
        if(after.q<=last_charge)throw std::runtime_error("isolated charge did not increase with H");last_charge=after.q;
        if(!first)std::cout<<",";first=false;
        std::cout<<"{\"H\":"<<h<<",\"main_admission_work\":"<<LAST_ENERGY.work[0]<<",\"expected\":"<<expected<<",\"terminal_charge\":"<<after.q<<"}";
    }
    Row row;row[0].push_back({0.,0,{}});
    auto uncut=shifted_incoming(row,930901,1,0,101,0,0);
    auto cut=shifted_incoming(row,930901,1,0,101,1,0);
    auto left=shifted_incoming(row,930901,1,11,101,1,0);
    auto right=shifted_incoming(row,930901,1,1,101,1,0);
    if(uncut.size()!=1||!cut.empty()||left.size()!=1||right.size()!=1)throw std::runtime_error("cut mapping check");
    std::cout<<"],\"central_link_removed_only\":true}\n";
}

int main(int argc,char** argv){
    int at_layer=0,at_lane=0;
    try{
        if(argc==2&&std::string(argv[1])=="--selftest"){self_test();return 0;}
        if(argc!=15)throw std::runtime_error("mode seed field H checkpoint source cut_layer cut_lane n start schedule stage output label_offset");
        std::string mode=argv[1],dest=argv[13],schedule=argv[11];int seed=std::stoi(argv[2]),source=std::stoi(argv[6]);
        int cut_layer=std::stoi(argv[7]),cut_lane=std::stoi(argv[8]),n=std::stoi(argv[9]),stage=std::stoi(argv[12]),offset=std::stoi(argv[14]);double start=std::stod(argv[10]);
        if(source<0||source>=12||n<1||n>4096||start<0||cut_layer<0||cut_layer>130||cut_lane<0||cut_lane>=12||offset<0)
            throw std::runtime_error("invalid argument");
        if(mode!="learn"&&mode!="active"&&mode!="frozen"&&mode.rfind("static_",0)!=0)throw std::runtime_error("invalid mode");
        if(schedule!="train"&&schedule!="test")throw std::runtime_error("invalid schedule");
        auto field=load_field(argv[3]);auto h=load_actuation(argv[4]);States states=initial_states(mode,field);
        bool frozen=mode=="frozen"||mode.rfind("static_",0)==0;
        if(mode=="active"||mode=="frozen")states=load_states(argv[5]);
        ENERGY_ENABLED=true;FREEZE_GAINS=frozen;
        double gaps[]={20.,22.,21.,24.,20.,23.};std::vector<double> dates(n);Row row;
        for(int i=0;i<n;i++){dates[i]=i?dates[i-1]+(schedule=="train"?8.:gaps[(i-1)%6]):start;row[source].push_back({dates[i],offset+i,{}});}
        std::array<double,9> work{};long long inputs=0,fires=0;double lower=100.,dz=0,db=0;
        std::vector<long long> layers;
        for(int layer=1;layer<=130;layer++){
            at_layer=layer;Row next;long long events=0;
            for(int lane=0;lane<12;lane++){
                at_lane=lane;int idx=(layer-1)*12+lane;PHYS=field[idx];ACTUATION=h[idx];
                auto in=shifted_incoming(row,seed,layer,lane,stage,cut_layer,cut_lane);
                for(const auto& e:in)if(e.time<states[idx].time-1e-8)throw std::runtime_error("nonchronological continuation");
                State terminal;double diag[8];next[lane]=cell_run(in,states[idx],frozen,false,offset+std::max(0,n-128),terminal,diag);
                if(terminal.phase!=0)throw std::runtime_error("terminal not READY");
                for(int p=0;p<3;p++){
                    if(terminal.z[p]>std::log(field[idx][p].cap)+1e-12)throw std::runtime_error("gain exceeds physical cap");
                    if(frozen&&terminal.z[p]!=states[idx].z[p])throw std::runtime_error("frozen gain moved");
                    if(terminal.z[p]<states[idx].z[p]-1e-12)throw std::runtime_error("gain decreased");dz+=terminal.z[p]-states[idx].z[p];
                }
                if(frozen&&terminal.b!=states[idx].b)throw std::runtime_error("frozen b moved");db+=terminal.b-states[idx].b;
                for(int k=0;k<9;k++)work[k]+=LAST_ENERGY.work[k];lower=std::min(lower,LAST_ENERGY.lower_bound);
                if(lower<=0)throw std::runtime_error("resource feasibility unassessed");
                inputs+=in.size();events+=next[lane].size();states[idx]=terminal;
            }
            fires+=events;layers.push_back(events);row=std::move(next);
        }
        std::ofstream st(dest+".states");st<<std::setprecision(17);
        for(const auto& s:states){for(double z:s.z)st<<z<<' ';st<<s.b<<' '<<s.q<<' '<<s.time<<' '<<s.phase<<'\n';}
        st.close();if(!st)throw std::runtime_error("state output");
        std::ofstream o(dest);o<<std::setprecision(17)<<"{\"status\":\"OK_POINT_NOT_CERTIFIED\",\"mode\":\""<<mode<<"\",\"source_dates\":[";
        for(int i=0;i<n;i++){if(i)o<<",";o<<dates[i];}
        o<<"],";block_metrics(o,row,dates,offset);
        o<<",\"work_components\":[";for(int k=0;k<9;k++){if(k)o<<",";o<<work[k];}
        o<<"],\"work_total\":"<<std::accumulate(work.begin(),work.end(),0.)<<",\"resource_lower_bound\":"<<lower
         <<",\"sum_delta_z\":"<<dz<<",\"sum_delta_b\":"<<db<<",\"input_pulses\":"<<inputs<<",\"fires\":"<<fires<<",\"layer_event_counts\":[";
        for(int i=0;i<130;i++){if(i)o<<",";o<<layers[i];}
        o<<"],\"outputs\":[";
        for(int lane=0;lane<12;lane++){if(lane)o<<",";o<<"[";for(size_t k=0;k<row[lane].size();k++){if(k)o<<",";auto e=row[lane][k];o<<"["<<e.time<<","<<e.label<<"]";}o<<"]";}
        o<<"]}\n";o.close();if(!o)throw std::runtime_error("result output");
    }catch(const std::exception& e){
        std::string message=e.what();std::cerr<<"layer="<<at_layer<<" lane="<<at_lane<<" "<<message<<'\n';
        bool domain=message=="root bracket"||message=="auxiliary not regenerated"||message=="raw/error overlap"
            ||message=="raw overlap"||message=="own raw/error overlap"||message=="finite-path resource bound not positive"
            ||message=="resource feasibility unassessed";
        return domain?10:2;
    }
}
