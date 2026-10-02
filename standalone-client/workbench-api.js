/**
 * Sustainable Catalyst Workbench — standalone API client foundation.
 *
 * Framework-free browser adapter for the canonical FastAPI runtime.
 * WordPress is not required and no authoritative mathematics runs here.
 */
export class SustainableCatalystWorkbenchAPI {
  constructor(options = {}) {
    const baseUrl = options.baseUrl || "https://workbench-api.sustainablecatalyst.com";
    this.baseUrl = String(baseUrl).replace(/\/+$/, "");
    this.timeoutMs = Number.isFinite(options.timeoutMs) ? options.timeoutMs : 30000;
    this.defaultHeaders = Object.assign(
      { "Accept": "application/json", "Content-Type": "application/json" },
      options.headers || {}
    );
  }

  async request(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    const requestId = options.requestId || this.createRequestId();
    const headers = Object.assign({}, this.defaultHeaders, options.headers || {}, {
      "X-Request-ID": requestId,
    });

    const init = {
      method: options.method || "GET",
      headers,
      signal: controller.signal,
    };

    if (options.body !== undefined) {
      init.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(this.baseUrl + path, init);
      const text = await response.text();
      let payload;
      try {
        payload = text ? JSON.parse(text) : {};
      } catch (_error) {
        throw new Error(`Workbench returned non-JSON response (${response.status})`);
      }

      if (!response.ok) {
        const detail = payload.detail || payload.error || `HTTP ${response.status}`;
        const error = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
        error.status = response.status;
        error.payload = payload;
        throw error;
      }

      return {
        data: payload,
        requestId: response.headers.get("X-Request-ID") || requestId,
        runtimeVersion: response.headers.get("X-SC-Workbench-Version") || payload.version || null,
      };
    } finally {
      clearTimeout(timer);
    }
  }

  createRequestId() {
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
      return globalThis.crypto.randomUUID();
    }
    return `scwb-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  health() {
    return this.request("/standalone/v1/health");
  }

  bootstrap() {
    return this.request("/standalone/v1/bootstrap");
  }

  apiContract() {
    return this.request("/standalone/v1/api-contract");
  }

  compatibility() {
    return this.request("/standalone/v1/compatibility");
  }

  clientConfig() {
    return this.request("/standalone/v1/client/config");
  }

  clientAdapter() {
    return this.request("/standalone/v1/client/adapter");
  }

  capabilities() {
    return this.request("/standalone/v1/client/capabilities");
  }

  plan(request) {
    return this.request("/standalone/v1/client/plan", {
      method: "POST",
      body: request,
    });
  }

  compute(request) {
    return this.request("/standalone/v1/client/compute", {
      method: "POST",
      body: request,
    });
  }
}
