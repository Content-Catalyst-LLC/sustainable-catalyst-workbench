# Minimal illustrative model for future scientific simulation tools.
function logistic_step(x, r, k, dt)
    return x + dt * r * x * (1 - x / k)
end
