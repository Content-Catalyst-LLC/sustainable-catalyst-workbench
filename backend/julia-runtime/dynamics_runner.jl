using LinearAlgebra

parsevec(s) = isempty(s) ? Float64[] : parse.(Float64, split(s, ","))
function parsemat(s)
    isempty(s) && return Matrix{Float64}(undef, 0, 0)
    rows=[parsevec(r) for r in split(s,";")]
    width=length(rows[1])
    any(length(r)!=width for r in rows) && error("ragged matrix")
    return reduce(vcat, permutedims.(rows))
end
encvec(v)=join(string.(Float64.(v)),",")

model=ARGS[1]
u0=parsevec(ARGS[2])
t0=parse(Float64,ARGS[3])
t1=parse(Float64,ARGS[4])
samples=parse(Int,ARGS[5])
params=parsevec(ARGS[6])
A=parsemat(ARGS[7])

rate=params[1]; r=params[2]; K=params[3]; omega=params[4]; damping=params[5]

function f(model,t,u)
    if model=="exponential-decay"
        return [-rate*u[1]]
    elseif model=="logistic"
        return [r*u[1]*(1-u[1]/K)]
    elseif model=="harmonic-oscillator"
        return [u[2],-(omega^2)*u[1]]
    elseif model=="damped-oscillator"
        return [u[2],-2*damping*u[2]-(omega^2)*u[1]]
    elseif model=="linear-system"
        return A*u
    else
        error("unsupported model: "*model)
    end
end

dt=(t1-t0)/(samples-1)
times=collect(range(t0,t1,length=samples))
states=Vector{Vector{Float64}}()
u=copy(u0)
push!(states,copy(u))
t=t0

for i in 2:samples
    k1=f(model,t,u)
    k2=f(model,t+dt/2,u .+ (dt/2).*k1)
    k3=f(model,t+dt/2,u .+ (dt/2).*k2)
    k4=f(model,t+dt,u .+ dt.*k3)
    u = u .+ (dt/6).*(k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4)
    t=times[i]
    push!(states,copy(u))
end

println("status\tok")
println("juliaVersion\t",VERSION)
println("method\tfixed-step-rk4")
println("time\t",encvec(times))
println("states\t",join(encvec.(states),";"))
