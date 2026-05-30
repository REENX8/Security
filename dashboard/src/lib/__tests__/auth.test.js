import { describe, it, expect, beforeEach, vi } from "vitest";

// Minimal localStorage stub (no jsdom in this project's test env).
const _store = {};
vi.stubGlobal("localStorage", {
  getItem: (k) => (k in _store ? _store[k] : null),
  setItem: (k, v) => { _store[k] = String(v); },
  removeItem: (k) => { delete _store[k]; },
});

const {
  setToken, clearToken, isAuthenticated, msUntilExpiry, tokenExpiresSoon,
} = await import("../auth.js");

// Build a fake JWT with a given exp (seconds since epoch). Only the payload
// segment is decoded by the client, so header/signature can be placeholders.
function fakeJwt(expSeconds) {
  const payload = btoa(JSON.stringify({ sub: "admin", exp: expSeconds }));
  return `header.${payload}.sig`;
}

describe("auth token expiry", () => {
  beforeEach(() => clearToken());

  it("treats a future-dated token as authenticated", () => {
    setToken(fakeJwt(Math.floor(Date.now() / 1000) + 3600));
    expect(isAuthenticated()).toBe(true);
    expect(msUntilExpiry()).toBeGreaterThan(0);
  });

  it("treats an expired token as not authenticated", () => {
    setToken(fakeJwt(Math.floor(Date.now() / 1000) - 10));
    expect(isAuthenticated()).toBe(false);
  });

  it("flags a soon-to-expire token", () => {
    setToken(fakeJwt(Math.floor(Date.now() / 1000) + 60)); // 1 min left
    expect(tokenExpiresSoon()).toBe(true);          // within default 5 min
    expect(tokenExpiresSoon(30 * 1000)).toBe(false); // not within 30 s
  });

  it("returns null/false with no token", () => {
    expect(msUntilExpiry()).toBeNull();
    expect(tokenExpiresSoon()).toBe(false);
    expect(isAuthenticated()).toBe(false);
  });
});
