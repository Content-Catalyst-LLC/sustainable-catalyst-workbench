# API Examples

```bash
curl http://127.0.0.1:8088/health
curl http://127.0.0.1:8088/ai/status
curl http://127.0.0.1:8088/tools
```

Run a tool:

```bash
curl -X POST http://127.0.0.1:8088/tools/run \
  -H 'Content-Type: application/json' \
  -d '{"tool_id":"energy-systems-calculator","inputs":{"mode":"electricity_cost_emissions","inputs":"kwh=500;rate=0.16;kgco2_per_kwh=0.4"}}'
```
