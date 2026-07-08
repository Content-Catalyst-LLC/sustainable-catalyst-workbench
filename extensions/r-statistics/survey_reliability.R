# Optional R bridge for survey and psychometrics workflows.
# Usage later: Rscript survey_reliability.R responses.csv
cronbach_alpha <- function(df) {
  k <- ncol(df)
  item_vars <- apply(df, 2, var, na.rm = TRUE)
  total_var <- var(rowSums(df, na.rm = TRUE), na.rm = TRUE)
  if (k <= 1 || total_var == 0) return(NA_real_)
  (k / (k - 1)) * (1 - sum(item_vars, na.rm = TRUE) / total_var)
}
