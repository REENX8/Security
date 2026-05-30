import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { setToken } from "../lib/auth.js";

function normalizeBase(raw) {
  let v = (raw || "http://localhost:8000").replace(/\/+$/, "");
  if (v && !/^https?:\/\//i.test(v)) v = `https://${v}`;
  return v;
}

const BASE_URL = normalizeBase(import.meta.env.VITE_API_URL);

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const resp = await fetch(`${BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.detail || data.error || `HTTP ${resp.status}`);
      }
      setToken(data.access_token);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-7 flex items-center gap-3">
          <img src="/shield.svg" alt="" className="h-9 w-9" />
          <div>
            <div className="text-sm font-bold leading-tight text-white">Phishing Detector</div>
            <div className="text-xs text-slate-400">ระบบตรวจจับเว็บฟิชชิง</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              ชื่อผู้ใช้
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              รหัสผ่าน
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-950/50 px-3 py-2 text-xs text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบ"}
          </button>
        </form>
      </div>
    </div>
  );
}
