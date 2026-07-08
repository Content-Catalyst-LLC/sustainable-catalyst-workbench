// Optional C++ kernel placeholder for future high-performance scoring/simulation.
#include <vector>
double weighted_score(const std::vector<double>& values, const std::vector<double>& weights){
  double n=0.0,d=0.0; for(size_t i=0;i<values.size() && i<weights.size();++i){n += values[i]*weights[i]; d += weights[i];} return d==0?0:n/d;
}
