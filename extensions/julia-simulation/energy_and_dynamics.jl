# Optional Julia bridge for differential equations, energy simulations, and optimization.
# Add DifferentialEquations.jl in a Julia environment for production simulations.
function logistic(N0, r, K, t)
    K / (1 + ((K - N0) / N0) * exp(-r * t))
end
println(logistic(10.0, 0.25, 100.0, 30.0))
