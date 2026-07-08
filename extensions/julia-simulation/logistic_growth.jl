# Optional Julia bridge for future scientific simulation.
# Usage: julia logistic_growth.jl 10 0.25 100 30
N0 = parse(Float64, ARGS[1]); r = parse(Float64, ARGS[2]); K = parse(Float64, ARGS[3]); t = parse(Float64, ARGS[4])
N = K / (1 + ((K - N0) / N0) * exp(-r*t))
println(N)
