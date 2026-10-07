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

  const [formData, setFormData] = useState({
    fullName: 'Sercan Bilir',
    dob: '1987-07-14',
    time: '10:30',
    location: 'Istanbul, TR',
  });
  const [calculating, setCalculating] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    '[13:04:22] SYS: Core engine initialized v2.10',
    '[13:04:22] SEC: Ephemeris matrix vectors loaded successfully',
    '[13:04:22] RDY: Waiting for payload input...',
  ]);

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

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalculating(true);
    
    setTimeout(() => {
      setLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] EXEC: Target -> ${formData.fullName}`,
        `[${new Date().toLocaleTimeString()}] CALC: Ascendant / Midheaven matrix compiled`,
        `[${new Date().toLocaleTimeString()}] AI: High-precision astrological synthesis ready.`
      ]);
      setCalculating(false);
    }, 1000);
  };

  return (
    <div className="flex min-h-screen bg-[#08080a] text-[#dedee2] selection:bg-white/20 selection:text-white">
      
      {/* Linear Ambient Glow Arka Plan Efekti */}
      <div className="pointer-events-none fixed -top-36 left-1/5 h-64 w-[500px] bg-[radial-gradient(circle,rgba(120,119,198,0.08)_0%,transparent_70%)] z-0" />

      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-10 flex w-60 flex-col border-r border-white/[0.06] bg-[#08080a] px-4 py-5">
        
        {/* Workspace Brand */}
        <div className="mb-8 flex items-center justify-between border-b border-white/[0.06] pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-white to-zinc-500 text-[0.75rem] font-black text-black">
              ✦
            </div>
            <span className="text-[0.8rem] font-semibold text-white">Mistik Holding</span>
          </div>
          <span className="rounded bg-white/[0.04] px-1 py-0.5 font-mono text-[0.6rem] text-zinc-500">PRO</span>
        </div>

        {/* Nav Başlığı */}
        <div className="mb-2 px-2 text-[0.65rem] font-semibold uppercase tracking-wider text-zinc-500">
          Platform
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <a href="/dashboard" className="flex items-center gap-2.5 rounded-md bg-white/[0.06] px-2.5 py-1.5 text-[0.75rem] font-medium text-white transition-colors">
            <span className="text-violet-400 text-[0.7rem]">⚡</span> Command Center
          </a>
          <Link href="/videos" className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[0.75rem] font-medium text-zinc-400 hover:bg-white/[0.03] hover:text-zinc-200 transition-colors">
            <span className="opacity-70 text-[0.7rem]">🎬</span> Video Studio
          </Link>
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-white/[0.06] pt-3.5 flex flex-col gap-2">
          <div className="truncate px-1 text-[0.7rem] text-zinc-400">{user?.email}</div>
          <button 
            onClick={handleLogout} 
            className="w-full rounded-md border border-white/[0.06] bg-transparent px-2.5 py-1.5 text-left text-[0.7rem] font-medium text-red-400 hover:bg-red-500/10 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-60 flex-1 px-12 py-10 z-1">
        
        {/* Header */}
        <header className="mb-9 flex items-center justify-between">
          <div>
            <h2 className="text-[1.2rem] font-semibold tracking-tight text-white">Celestial Command Center</h2>
            <p className="mt-0.5 text-[0.75rem] text-zinc-500">Swiss Ephemeris & Multi-Agent Autonomous Orchestration</p>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1 font-mono text-[0.65rem] text-emerald-400 tracking-wide">
            <span className="h-1 w-1 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
            SYSTEM SECURE
          </div>
        </header>

        {error && (
          <div className="mb-5 rounded-md border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-[0.75rem] text-red-300">
            {error}
          </div>
        )}

        {/* Grid Layout */}
        <div className="grid grid-cols-[1.5fr_1fr] gap-4 items-stretch">
          
          {/* Matrix Parameters (Form) */}
          <div className="flex flex-col justify-between rounded-[10px] border border-white/[0.06] bg-[#0c0c0f] p-5 shadow-2xl">
            <div>
              <h3 className="text-[0.8rem] font-semibold text-white">Matrix Parameters</h3>
              <p className="mt-0.5 mb-4 text-[0.7rem] text-zinc-500">Configure coordinate ingestion variables and planetary inputs.</p>
            </div>

            <form onSubmit={handleCalculate} className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-[0.65rem] font-medium uppercase tracking-wider text-zinc-500">Subject Full Name</label>
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                  className="w-full rounded-md border border-white/[0.08] bg-[#050507] px-2.5 py-2 text-[0.75rem] text-white outline-none focus:border-white/20 transition-colors"
                />
              </div>

              <div className="grid grid-cols-[1.2fr_1fr] gap-2.5">
                <div>
                  <label className="mb-1 block text-[0.65rem] font-medium uppercase tracking-wider text-zinc-500">Birth Date</label>
                  <input
                    type="date"
                    value={formData.dob}
                    onChange={(e) => setFormData({...formData, dob: e.target.value})}
                    className="w-full rounded-md border border-white/[0.08] bg-[#050507] px-2.5 py-2 text-[0.75rem] text-white outline-none focus:border-white/20 transition-colors"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-[0.65rem] font-medium uppercase tracking-wider text-zinc-500">UTC Time</label>
                  <input
                    type="text"
                    value={formData.time}
                    onChange={(e) => setFormData({...formData, time: e.target.value})}
                    className="w-full rounded-md border border-white/[0.08] bg-[#050507] px-2.5 py-2 text-[0.75rem] text-white outline-none focus:border-white/20 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-[0.65rem] font-medium uppercase tracking-wider text-zinc-500">Location Coordinates</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full rounded-md border border-white/[0.08] bg-[#050507] px-2.5 py-2 text-[0.75rem] text-white outline-none focus:border-white/20 transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={calculating}
                className="mt-1 w-full rounded-md bg-white py-2 text-[0.75rem] font-semibold text-black tracking-tight shadow-[0_1px_6px_rgba(255,255,255,0.1)] hover:bg-zinc-200 active:scale-[0.99] transition-all cursor-pointer disabled:opacity-50"
              >
                {calculating ? 'Processing Pipeline...' : 'Execute Calculation Pipeline'}
              </button>
            </form>
          </div>

          {/* Right Column (Tokens & Status) */}
          <div className="flex flex-col gap-4">
            
            {/* Token Allocation */}
            <div className="flex flex-col justify-between rounded-[10px] border border-white/[0.06] bg-[#0c0c0f] p-5 shadow-2xl">
              <div>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-[0.8rem] font-semibold text-white">Token Allocation</h3>
                    <p className="text-[0.7rem] text-zinc-500">Available resources</p>
                  </div>
                  <span className="rounded border border-white/[0.06] bg-white/[0.04] px-1.5 py-0.5 font-mono text-[0.6rem] text-violet-400 uppercase">
                    {user?.role || 'FREE'}
                  </span>
                </div>

                <div className="my-1.5 flex items-baseline gap-1.5">
                  <span className="font-mono text-[1.75rem] font-bold tracking-tight text-white">
                    {balance?.balance ?? "0"}
                  </span>
                  <span className="text-[0.7rem] text-zinc-500">tokens remaining</span>
                </div>
              </div>

              <button
                onClick={() => setShowTopUp(true)}
                className="w-full rounded-md border border-white/[0.06] bg-white/[0.04] py-1.5 text-[0.7rem] font-medium text-zinc-200 hover:bg-white/[0.08] transition-colors cursor-pointer"
              >
                + Top Up Tokens
              </button>
            </div>

            {/* Node Status */}
            <div className="rounded-[10px] border border-white/[0.06] bg-[#0c0c0f] p-5 shadow-2xl">
              <h3 className="text-[0.8rem] font-semibold text-white">Node Status</h3>
              <p className="mt-0.5 mb-3 text-[0.7rem] text-zinc-500">Real-time telemetry.</p>
              
              <div className="flex flex-col gap-1.5 font-mono text-[0.7rem]">
                <div className="flex justify-between rounded border border-white/[0.04] bg-[#050507] px-2.5 py-1.5">
                  <span className="text-zinc-500 font-sans">Swiss Core</span>
                  <span className="font-semibold text-emerald-400">v2.10</span>
                </div>
                <div className="flex justify-between rounded border border-white/[0.04] bg-[#050507] px-2.5 py-1.5">
                  <span className="text-zinc-500 font-sans">Latency</span>
                  <span className="font-semibold text-blue-400">18ms</span>
                </div>
              </div>
            </div>

          </div>

          {/* Terminal / Log Stream (Full Width) */}
          <div className="col-span-2 rounded-[10px] border border-white/[0.06] bg-[#0c0c0f] p-5 shadow-2xl">
            <div className="mb-3 flex items-center justify-between border-b border-white/[0.04] pb-2.5">
              <span className="text-[0.75rem] font-semibold text-white">System Output Stream</span>
              <span className="rounded border border-blue-500/20 bg-blue-500/10 px-1.5 py-0.5 font-mono text-[0.6rem] text-blue-400">ACTIVE</span>
            </div>

            <div className="max-h-32 overflow-y-auto rounded-md border border-white/[0.04] bg-[#050507] p-3 font-mono text-[0.7rem] flex flex-col gap-1.5">
              {logs.map((log, index) => (
                <div key={index} className="flex items-start gap-2 text-zinc-500">
                  <span className="text-zinc-700">$</span>
                  <span className={`break-all ${log.includes('EXEC') ? 'text-emerald-400' : 'text-zinc-400'}`}>{log}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </main>

      {showTopUp && <TopUpModal onClose={() => setShowTopUp(false)} />}
    </div>
  );
}