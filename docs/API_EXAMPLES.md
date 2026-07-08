# API Examples

```bash
curl http://127.0.0.1:8088/health
curl http://127.0.0.1:8088/tools
curl http://127.0.0.1:8088/ai/status
```

Run a tool:

```bash
curl -X POST http://127.0.0.1:8088/tools/run \
  -H 'Content-Type: application/json' \
  -d '{"tool_id":"energy-systems-calculator","inputs":{"mode":"building_eui","inputs":"area_m2=1000;annual_kwh=180000"}}'
```
