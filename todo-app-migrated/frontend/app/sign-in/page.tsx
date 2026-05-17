"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Mode = "login" | "register";

export default function SignInPage() {
  const router = useRouter();
  const { setToken } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const fn = mode === "login" ? api.login : api.register;
      const { access_token } = await fn(email, password);
      setToken(access_token);
      router.replace("/tasks");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Todo</h1>
      <div className="tabs">
        <button className={`tab ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>
          Sign in
        </button>
        <button className={`tab ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>
          Register
        </button>
      </div>
      <form className="card" onSubmit={onSubmit}>
        <label>
          Email
          <input
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label style={{ display: "block", marginTop: "0.75rem" }}>
          Password
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            minLength={6}
            required
          />
        </label>
        <button className="btn" type="submit" disabled={busy} style={{ marginTop: "1rem" }}>
          {busy ? "…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
