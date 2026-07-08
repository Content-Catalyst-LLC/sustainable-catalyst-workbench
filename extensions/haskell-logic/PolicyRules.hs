module PolicyRules where

data Oversight = NoOversight | Advisory | Meaningful | Binding deriving (Eq, Show)
data HarmRisk = Low | Moderate | High deriving (Eq, Show)

data Deployment = Deployment
  { oversight :: Oversight
  , harmRisk :: HarmRisk
  , contestable :: Bool
  } deriving (Eq, Show)

requiresEscalation :: Deployment -> Bool
requiresEscalation d =
  harmRisk d == High && (oversight d /= Binding || not (contestable d))
