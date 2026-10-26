from pathlib import Path
P=Path(__file__).resolve().parent
old=P.parent/'restored/A22_targeted_noise_selectivity_diagnostic_EN'
header='''#include "work_common.cpp"
using Field=std::array<std::array<PhysicalPort,3>,1560>;
Field load_field(const std::string& path){Field f;std::ifstream in(path);for(auto& cell:f)for(auto& p:cell)if(!(in>>p.cap>>p.lm>>p.ls>>p.le>>p.m))throw std::runtime_error("physical field truncated");return f;}
'''
(P/'src/field.hpp').write_text(header)
s=(old/'src/evaluate.cpp').read_text().replace('#include "work_common.cpp"','#include "field.hpp"')
s=s.replace('argc!=8','argc!=9').replace('auto states=load(argv[3]);','auto field=load_field(argv[8]); auto states=load(argv[3]);').replace(' if(level==-1&&mode!="clean")throw std::runtime_error("noiseless diagnostic requires no decoys");','')
s=s.replace('auto initial=states[(layer-1)*12+lane];','PHYS=field[(layer-1)*12+lane]; auto initial=states[(layer-1)*12+lane];')
(P/'src/evaluate.cpp').write_text(s)
