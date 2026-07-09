# Workbench v1.5.0 — Exportable Calculation Reports

Phase 5 adds export-ready calculation reports to Sustainable Catalyst Workbench.

## What changed

- New backend report engine: `backend/app/engines/calculation_reports.py`
- New FastAPI router: `backend/app/routers/reports.py`
- New backend endpoint: `POST /reports/calculation`
- New WordPress REST proxy: `/wp-json/sc-workbench/v1/calculation-report`
- Updated result export row with:
  - Print/PDF
  - Markdown Report
  - HTML Report
  - Copy Report
  - Download JSON
- New backend tests: `backend/tests/test_v150_exportable_calculation_reports.py`

## Report sections

Each report is organized as a reviewable calculation note:

1. Purpose and summary
2. Formula
3. Inputs and units
4. Computed results
5. Sensitivity or graph review
6. Assumptions
7. Validation checks
8. Method
9. Interpretation and next review
10. Warnings and professional boundary

## Backend example

```bash
curl -X POST "$WORKBENCH_URL/reports/calculation" \
  -H 'Content-Type: application/json' \
  -d '{"source_result":{"ok":true,"tool":"Example","summary":"Example summary","values":{"formula":"y=x^2","inputs":{"x":2},"results":{"y":4}}}}'
```

## Boundary

Reports are educational, analytical, and decision-support artifacts. They are not stamped engineering calculations, compliance certifications, assurance statements, or substitutes for licensed professional judgment.
