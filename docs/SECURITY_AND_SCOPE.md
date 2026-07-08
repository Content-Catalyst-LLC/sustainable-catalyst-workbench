# Security and Scope Notes

## Scope principle

The assistant is not a general chatbot. It should be restricted to the Sustainable Catalyst knowledge map.

## Production requirements before live AI

- Add server-side rate limiting.
- Add request logging without storing sensitive personal data unnecessarily.
- Add out-of-scope refusal behavior.
- Add prompt-injection handling for retrieved documents.
- Add citations to retrieved site materials.
- Add disclaimers for educational analysis.
- Keep calculations deterministic and inspectable.
- Keep OpenAI/API credentials server-side only.

## Professional-advice limits

For law, medicine, psychology, financial, compliance, or regulatory topics, use educational framing and recommend qualified professional review for real-world decisions.
