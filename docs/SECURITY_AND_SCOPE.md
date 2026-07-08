# Security and Scope

The assistant is restricted to Sustainable Catalyst topics. Out-of-scope questions are redirected.

The preferred production key location is backend `.env`.

WordPress-managed provider keys are supported because the site owner requested it. The plugin encrypts the key using WordPress salts when OpenSSL is available and sends it to the backend through `X-SC-Provider-Key`. This is acceptable for controlled deployments but backend `.env` remains safer.

Do not paste provider keys into chat, GitHub, public HTML, JavaScript, CSS, or logs.
