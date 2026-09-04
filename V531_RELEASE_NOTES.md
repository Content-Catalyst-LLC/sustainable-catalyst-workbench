# Workbench v5.3.1 — Settings & Backend Connection Repair

Workbench v5.3.1 makes backend configuration a first-class WordPress setting and refines the homepage Computational Instrument.

## Settings repair

- Adds **Workbench → Settings** in WordPress admin.
- Adds a visible Backend URL field with `https://workbench-api.sustainablecatalyst.com` as the canonical production value.
- Adds a server-side **Test connection** action for CAS (`/v510/status`), Graph Mathematics (`/v520/status`), and Blackboard/Creative/Prototype services (`/v530/status`).
- Shows the effective configuration source: Workbench settings, `wp-config.php`, or not configured.
- Retains `SCWB_WORKBENCH_BACKEND_URL` as an advanced deployment override.
- Retains the `scwb_workbench_backend_url` filter for managed deployments.
- Adds a compact execution-boundary panel so backend compute, local Runner access, and physical-device programming are not conflated.

## Homepage instrument refinement

The `[sc_workbench_homepage_instrument]` shortcode is visually tightened into a denser black computational surface. It cycles through graph, sound, form, and physical-system transformations while keeping CAS, 2D/3D graphing, harmonics, parametric form, and MCU/FPGA capability visible in one line.

## Backend

No new numerical backend capability is introduced in v5.3.1. The production backend remains the certified v5.3.0 runtime and does **not** require redeployment for this patch.
