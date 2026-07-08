// Optional C++ kernel for high-performance scoring loops.
#include <vector>
#include <stdexcept>

double weighted_score(const std::vector<double>& values, const std::vector<double>& weights) {
    if (values.size() != weights.size()) throw std::runtime_error("size mismatch");
    double s = 0.0;
    for (size_t i = 0; i < values.size(); ++i) s += values[i] * weights[i];
    return s;
}
