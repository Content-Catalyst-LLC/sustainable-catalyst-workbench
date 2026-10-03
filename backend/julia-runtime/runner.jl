using LinearAlgebra
using Statistics

parsevec(s) = isempty(s) ? Float64[] : parse.(Float64, split(s, ","))
function parsemat(s)
    isempty(s) && return Matrix{Float64}(undef, 0, 0)
    rows=[parsevec(r) for r in split(s,";")]
    width=length(rows[1])
    any(length(r)!=width for r in rows) && error("ragged matrix")
    reduce(vcat, permutedims.(rows))
end
encvec(v)=join(string.(Float64.(v)),",")
encmat(m)=join([encvec(vec(m[i,:])) for i in axes(m,1)],";")

op=length(ARGS)>=1 ? ARGS[1] : "runtime-info"
va=length(ARGS)>=2 ? parsevec(ARGS[2]) : Float64[]
vb=length(ARGS)>=3 ? parsevec(ARGS[3]) : Float64[]
ma=length(ARGS)>=4 ? parsemat(ARGS[4]) : Matrix{Float64}(undef,0,0)
mb=length(ARGS)>=5 ? parsemat(ARGS[5]) : Matrix{Float64}(undef,0,0)

println("status\tok")
println("juliaVersion\t", VERSION)
println("threads\t", Threads.nthreads())

if op=="runtime-info"
    println("resultKind\truntime-info"); println("result\tready")
elseif op=="vector-dot"
    length(va)==length(vb) || error("vector lengths differ")
    println("resultKind\tscalar"); println("result\t", dot(va,vb))
elseif op=="matrix-multiply"
    println("resultKind\tmatrix"); println("result\t", encmat(ma*mb))
elseif op=="linear-solve"
    println("resultKind\tvector"); println("result\t", encvec(ma\va))
elseif op=="statistics"
    isempty(va) && error("statistics requires vector")
    println("resultKind\tstatistics")
    println("mean\t",mean(va)); println("std\t",length(va)>1 ? std(va) : 0.0)
    println("minimum\t",minimum(va)); println("maximum\t",maximum(va))
else
    error("unsupported operation: "*op)
end
