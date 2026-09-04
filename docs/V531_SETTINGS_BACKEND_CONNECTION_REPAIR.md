# v5.3.1 Settings & Backend Connection Repair

The WordPress plugin now exposes backend configuration through **Workbench → Settings**. The saved option is `scwb_workbench_backend_url`.

Resolution order:

1. shortcode/backend override when explicitly supplied;
2. `SCWB_WORKBENCH_BACKEND_URL` constant in `wp-config.php`;
3. saved Workbench backend URL setting;
4. `scwb_workbench_backend_url` filter.

The administrator can test the entered URL before or after saving it. The test is performed server-side by WordPress and checks the v5.1 CAS, v5.2 Graph Mathematics, and v5.3 Blackboard/Creative/Prototype status endpoints.

The canonical Sustainable Catalyst production backend is `https://workbench-api.sustainablecatalyst.com`.
