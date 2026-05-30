const TOKEN_KEY = "phish_jwt";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function decodeExp(token) {
  try {
    return JSON.parse(atob(token.split(".")[1])).exp * 1000;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  const token = getToken();
  if (!token) return false;
  const exp = decodeExp(token);
  return exp != null && exp > Date.now();
}

// Milliseconds until the current token expires (null if no/invalid token).
export function msUntilExpiry() {
  const token = getToken();
  if (!token) return null;
  const exp = decodeExp(token);
  return exp == null ? null : exp - Date.now();
}

// True when the session is still valid but expires within `withinMs`
// (default 5 min) — use to warn the user before they get logged out.
export function tokenExpiresSoon(withinMs = 5 * 60 * 1000) {
  const left = msUntilExpiry();
  return left != null && left > 0 && left <= withinMs;
}
