# Optional R bridge for future psychometrics/statistics expansion.
# Reads CSV-like item response rows from stdin and prints Cronbach alpha.
x <- read.csv(file("stdin"), header=FALSE)
k <- ncol(x)
item_vars <- apply(x, 2, var)
total_var <- var(rowSums(x))
alpha <- if (k > 1 && total_var > 0) (k/(k-1)) * (1 - sum(item_vars)/total_var) else NA
cat(alpha, "\n")
