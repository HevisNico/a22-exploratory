#include "work_common.cpp"
using Field=std::array<std::array<PhysicalPort,3>,1560>;
Field load_field(const std::string& path){Field f;std::ifstream in(path);for(auto& cell:f)for(auto& p:cell)if(!(in>>p.cap>>p.lm>>p.ls>>p.le>>p.m))throw std::runtime_error("physical field truncated");return f;}
