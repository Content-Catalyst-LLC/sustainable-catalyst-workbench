-- Optional Haskell bridge for typed rule validation.
module ScopeRules where

data Duty = HumanReview | AuditLog | Documentation deriving (Eq, Show)
data Risk = HighImpact | SensitiveData | SafetyCritical deriving (Eq, Show)

requiredDuties :: Risk -> [Duty]
requiredDuties HighImpact = [HumanReview, AuditLog, Documentation]
requiredDuties SensitiveData = [Documentation, AuditLog]
requiredDuties SafetyCritical = [HumanReview, AuditLog]
