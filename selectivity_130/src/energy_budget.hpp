#pragma once
#include <array>
#include <cmath>
#include <ostream>
#include <vector>
#include <algorithm>
struct EnergyTerm{int component;double coefficient,rate,duration;};
static bool ENERGY_ENABLED=true;
static std::ostream* ENERGY_TRACE=nullptr;
struct EnergyBudget{
 std::array<double,9> work{};
 double E=100.,min_event=100.,lower_bound=100.,max_power=0.,pump=0.,elapsed=0.,segments=0.;
 double oldD=0.,decay=0.,pending=0.,step=0.,stepwork=0.,power_start=0.,step_pump=0.;
 std::vector<EnergyTerm> terms;
 static double convolution(double coefficient,double rate,double duration,double horizon){
  if(coefficient==0||duration<=0)return 0.;
  double slow=std::min(10.,rate),diff=std::abs(10.-rate);
  double v=diff>1e-12?std::exp(-slow*duration)*(-std::expm1(-diff*duration))/diff:duration*std::exp(-10.*duration);
  return coefficient*v*std::exp(-10.*std::max(0.,horizon-duration));
 }
 // Integral of 10*D(t), D=100-E, due to a truncated exponential forcing.
 // Calculated from the pump trajectory, never assigned from the balance residual.
 static double pump_term(double c,double rate,double length,double horizon){
  double live;
  if(rate==0.) live=c*(length+std::expm1(-10.*length)/10.);
  else if(std::abs(rate-10.)<1e-10) live=c/10.*(-std::expm1(-10.*length)-10.*length*std::exp(-10.*length));
  else live=c/(10.-rate)*(10.*(-std::expm1(-rate*length))/rate+std::expm1(-10.*length));
  double endD=convolution(c,rate,length,length);
  return live+endD*(-std::expm1(-10.*std::max(0.,horizon-length)));
 }
 void begin(double dt){oldD=100.-E;step=dt;pending=oldD*std::exp(-10.*dt);stepwork=0.;power_start=0.;step_pump=oldD*(-std::expm1(-10.*dt));if(ENERGY_TRACE)terms.clear();}
 void add(int component,double coefficient,double rate,double duration){
  duration=std::max(0.,std::min(step,duration));if(coefficient<=0||duration<=0)return;
  double w=rate>0?coefficient*(-std::expm1(-rate*duration))/rate:coefficient*duration;
  power_start+=coefficient;work[component]+=w;stepwork+=w;pending+=convolution(coefficient,rate,duration,step);
  step_pump+=pump_term(coefficient,rate,duration,step);
  if(ENERGY_TRACE)terms.push_back({component,coefficient,rate,duration});
 }
 void finish(){
  max_power=std::max(max_power,power_start);
  double previous=E;E=100.-pending;min_event=std::min(min_event,E);elapsed+=step;segments++;
  pump+=step_pump;
  if(!(E>0&&E<=100.+1e-9&&E>=lower_bound-1e-8))throw std::runtime_error("reserve invariant failed");
  if(ENERGY_TRACE&&step>0){auto& o=*ENERGY_TRACE;o<<"{\"time\":"<<elapsed-step<<",\"dt\":"<<step<<",\"E0\":"<<previous<<",\"E1\":"<<E<<",\"terms\":[";for(int i=0;i<int(terms.size());i++){if(i)o<<",";auto x=terms[i];o<<"["<<x.component<<","<<x.coefficient<<","<<x.rate<<","<<x.duration<<"]";}o<<"]}\n";}
 }
 double total()const{double v=0;for(auto w:work)v+=w;return v;}
};
static EnergyBudget LAST_ENERGY;
