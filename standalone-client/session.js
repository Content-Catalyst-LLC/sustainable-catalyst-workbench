/**
 * Workbench v12.1 standalone session client.
 *
 * Tokens are held in memory by default. Persistence is opt-in and should be
 * supplied by the embedding application if its threat model permits it.
 */
export class StandaloneSessionClient {
  constructor(api, options = {}) {
    this.api = api;
    this.token = options.token || null;
  }

  async authConfig() {
    return this.api.request("/standalone/v1/auth/config");
  }

  async createAnonymousSession(options = {}) {
    const response = await this.api.request("/standalone/v1/auth/session/anonymous", {
      method: "POST",
      body: {
        ttlSeconds: options.ttlSeconds || 3600,
        clientLabel: options.clientLabel || "standalone-app"
      }
    });
    this.token = response.data.token;
    return response;
  }

  async verifySession(token = this.token) {
    if (!token) throw new Error("No Workbench session token available");
    return this.api.request("/standalone/v1/auth/session/verify", {
      method: "POST",
      body: { token }
    });
  }

  async refreshSession(options = {}) {
    if (!this.token) throw new Error("No Workbench session token available");
    const response = await this.api.request("/standalone/v1/auth/session/refresh", {
      method: "POST",
      body: {
        token: this.token,
        ttlSeconds: options.ttlSeconds || 3600
      }
    });
    this.token = response.data.token;
    return response;
  }

  async me() {
    if (!this.token) throw new Error("No Workbench session token available");
    return this.api.request("/standalone/v1/auth/session/me", {
      headers: { "Authorization": `Bearer ${this.token}` }
    });
  }

  clear() {
    this.token = null;
  }
}
