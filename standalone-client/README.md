# Workbench Standalone Client Foundation

`workbench-api.js` is a framework-neutral browser client for the canonical Workbench FastAPI backend.

It does **not** depend on WordPress, `wpApiSettings`, a WordPress REST nonce, React, or another frontend framework.

```js
import { SustainableCatalystWorkbenchAPI } from "./workbench-api.js";

const api = new SustainableCatalystWorkbenchAPI({
  baseUrl: "https://workbench-api.sustainablecatalyst.com",
});

const result = await api.compute({
  operation: "exact",
  expression: "1/3 + 1/6",
});

console.log(result.data);
```

The browser client does not execute authoritative mathematics. It submits structured requests to FastAPI and preserves request/runtime identity returned by the backend.
