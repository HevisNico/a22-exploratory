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
 void begin(double dt){step=dt;}
 void add(int component,double coefficient,double rate,double duration){
  duration=std::max(0.,std::min(step,duration));if(coefficient<=0||duration<=0)return;
  double w=rate>0?coefficient*(-std::expm1(-rate*duration))/rate:coefficient*duration;
  work[component]+=w;
 }
 void finish(){}
 double total()const{double v=0;for(auto w:work)v+=w;return v;}
};
static EnergyBudget LAST_ENERGY;
