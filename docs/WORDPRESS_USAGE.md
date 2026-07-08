# WordPress Usage

Install `sustainable-catalyst-workbench-plugin-v0.4.2.zip`.

Use this shortcode on the Research Library page:

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

Recommended approach:

- Keep the original Research Library pathways.
- Do not paste the full topic map into the Research Library page.
- Do not use an "All Maps" button.
- Treat the Workbench as one compact utility block.

Settings:

- Backend URL: `http://127.0.0.1:8088` for local testing.
- Production: use an HTTPS backend such as `https://api.sustainablecatalyst.com`.
- Enable AI panels: enabled.
- Enable scope gate: enabled.
- Debug mode: disabled.

Provider key:

- Preferred: set `OPENAI_API_KEY` in backend `.env`.
- Supported for local/testing: paste key in WordPress settings. It is encrypted using WordPress salts when OpenSSL is available.

## Visual Analytics Tab

Use the standard compact shortcode:

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

The widget now includes four tabs:

```text
Ask | Calculators | Visualize | Pathways
```

The **Visualize** tab sends chart inputs to the backend tool `visual-analytics-studio`. The backend must be running for SVG graph generation.
