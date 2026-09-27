"use client";

import { useState } from "react";
import { createTopUpCheckout } from "@/lib/api";

const PACKAGES = [
  { id: "starter_100", label: "100 Credits", price: "$4.99" },
  { id: "growth_500", label: "500 Credits", price: "$19.99" },
  { id: "pro_1500", label: "1500 Credits", price: "$49.99" },
];

export default function TopUpModal({ onClose }: { onClose: () => void }) {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handlePurchase(packageId: string) {
    setError(null);
    setLoadingId(packageId);
    try {
      const { checkout_url } = await createTopUpCheckout(packageId);
      window.location.href = checkout_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not start checkout");
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50,
      }}
    >
      <div className="card" style={{ maxWidth: 480, width: "90%" }}>
        <h3>Top Up Credits</h3>
        {error && <p className="error-text">{error}</p>}
        <div className="grid">
          {PACKAGES.map((pkg) => (
            <div key={pkg.id} className="card" style={{ margin: 0 }}>
              <strong>{pkg.label}</strong>
              <p>{pkg.price}</p>
              <button className="btn" onClick={() => handlePurchase(pkg.id)} disabled={loadingId === pkg.id}>
                {loadingId === pkg.id ? "Redirecting..." : "Buy"}
              </button>
            </div>
          ))}
        </div>
        <button className="btn btn-secondary" style={{ marginTop: "1rem" }} onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
