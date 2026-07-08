# AI Providers: Gemini, DeepSeek, and OpenAI

Sustainable Catalyst Workbench v0.7.3 supports a compact provider menu:

- `disabled`
- `gemini`
- `deepseek`
- `openai`

Groq is intentionally not included in this release. The goal is a stable, easy-to-debug provider stack rather than provider sprawl.

## Recommended path

For the first free/low-cost deployment:

```env
SC_WORKBENCH_AI_PROVIDER=gemini
GEMINI_API_KEY=your_key
SC_WORKBENCH_GEMINI_MODEL=gemini-3.5-flash
```

For a low-cost OpenAI-compatible alternative:

```env
SC_WORKBENCH_AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
SC_WORKBENCH_DEEPSEEK_MODEL=deepseek-v4-flash
SC_WORKBENCH_DEEPSEEK_THINKING=disabled
```

For OpenAI later:

```env
SC_WORKBENCH_AI_PROVIDER=openai
OPENAI_API_KEY=your_key
SC_WORKBENCH_OPENAI_MODEL=gpt-4.1-mini
```

## WordPress-managed provider keys

Production preference is backend `.env` secrets. If you need WordPress to forward a provider key:

1. Use HTTPS for both WordPress and the backend.
2. Select the provider in `SC Workbench → Settings`.
3. Paste the provider key into the provider-key field.
4. Confirm that `/ai/status` shows the expected provider.

The plugin forwards keys server-to-server using:

- `X-SC-Provider-Key`
- `X-SC-AI-Provider`
- provider-specific compatibility headers when needed

## Safety behavior

The same Sustainable Catalyst scope gate and professional-disclaimer rules apply regardless of provider. Provider choice changes generation infrastructure, not the ethical boundary of the Workbench.
