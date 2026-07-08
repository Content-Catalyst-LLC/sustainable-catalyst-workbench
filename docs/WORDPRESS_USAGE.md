# WordPress Usage

Install `sustainable-catalyst-workbench-plugin-v0.6.0.zip` from Plugins → Add New → Upload Plugin.

Use:

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

Settings:

- Backend URL: `http://127.0.0.1:8088` for local testing.
- Production backend: use HTTPS, for example `https://api.sustainablecatalyst.com`.
- Enable scope gate.
- Keep debug mode disabled on the public site.
- Prefer backend `.env` for provider keys in production. WordPress-managed OpenAI key storage is available for controlled use.
