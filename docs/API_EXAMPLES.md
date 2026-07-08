# API Examples

## Health

```bash
curl http://127.0.0.1:8088/health
```

## Tools

```bash
curl http://127.0.0.1:8088/tools
```

## Research topic search

```bash
curl "http://127.0.0.1:8088/research/search?q=AI%20governance%20risk"
```

## AI scope-gated library question

```bash
curl -X POST http://127.0.0.1:8088/ai/ask-library \
  -H "Content-Type: application/json" \
  -d '{"question":"How should I evaluate AI governance risk?","mode":"library-guide"}'
```

## Linear algebra solver

```bash
curl -X POST http://127.0.0.1:8088/tools/run \
  -H "Content-Type: application/json" \
  -d '{"tool_id":"linear-system-solver","inputs":{"matrix":[[2,1],[1,3]],"vector":[1,2]}}'
```

## AI governance audit

```bash
curl -X POST http://127.0.0.1:8088/tools/run \
  -H "Content-Type: application/json" \
  -d '{"tool_id":"ai-governance-audit","inputs":{"transparency":3,"human_oversight":4,"data_quality":3,"contestability":2,"harm_risk":4}}'
```
