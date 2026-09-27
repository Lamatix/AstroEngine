"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, fullName);
      router.push("/login");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 420, margin: "0 auto" }}>
        <h2>Create Account</h2>
        {error && <p className="error-text">{error}</p>}
        <form onSubmit={handleSubmit}>
          <input className="input" placeholder="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <input className="input" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input className="input" type="password" placeholder="Password (min 8 chars)" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          <button className="btn" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Creating..." : "Sign Up"}
          </button>
        </form>
        <p style={{ marginTop: "1rem" }}>
          Already have an account? <Link href="/login">Log in</Link>
        </p>
      </div>
    </main>
  );
}
