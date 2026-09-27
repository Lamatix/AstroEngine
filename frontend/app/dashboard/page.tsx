"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getCreditBalance, getMe, logout, CreditBalance } from "@/lib/api";
import TopUpModal from "@/components/TopUpModal";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [showTopUp, setShowTopUp] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [me, bal] = await Promise.all([getMe(), getCreditBalance()]);
        setUser(me);
        setBalance(bal);
      } catch (err) {
        router.push("/login");
      }
    }
    load();
  }, [router]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <main className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Dashboard</h2>
        <button className="btn btn-secondary" onClick={handleLogout}>Log Out</button>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="grid">
        <div className="card">
          <h3>Account</h3>
          <p>{user?.email}</p>
          <span className="badge badge-completed">{user?.role}</span>
        </div>
        <div className="card">
          <h3>Credit Balance</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700 }}>{balance?.balance ?? "-"}</p>
          <button className="btn" onClick={() => setShowTopUp(true)}>Top Up</button>
        </div>
        <div className="card">
          <h3>Video Studio</h3>
          <p>Create Reels, Shorts, or full YouTube videos.</p>
          <Link className="btn" href="/videos">Open Studio</Link>
        </div>
      </div>

      {showTopUp && <TopUpModal onClose={() => setShowTopUp(false)} />}
    </main>
  );
}
