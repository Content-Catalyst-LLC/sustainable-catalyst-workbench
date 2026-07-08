# WordPress Usage

## Main Workbench page

Create a page at:

```text
/workbench/
```

Recommended page body:

```text
[sc_workbench]
```

## Research Library integration

Add to Research Library pages:

```text
[sc_workbench_ai mode="library-guide"]
[sc_workbench_tools]
```

## Topic-specific tool lists

```text
[sc_workbench_tools topic="risk-resilience"]
[sc_workbench_tools topic="mathematical-modeling"]
[sc_workbench_tools topic="artificial-intelligence-systems"]
[sc_workbench_tools topic="meaning"]
```

## Article-level tool

```text
[sc_workbench tool="linear-system-solver"]
[sc_workbench tool="decision-matrix"]
[sc_workbench tool="risk-resilience-scorecard"]
[sc_workbench tool="ai-governance-audit"]
[sc_workbench tool="sustainability-tradeoff-matrix"]
[sc_workbench tool="qualitative-interpretation-matrix"]
```

## AI panels

```text
[sc_workbench_ai mode="library-guide"]
[sc_workbench_ai mode="article-copilot" topic="systems-modeling"]
[sc_workbench_ai mode="interpretive-copilot" topic="meaning"]
[sc_workbench_ai mode="governance-assistant" topic="artificial-intelligence-systems"]
```
