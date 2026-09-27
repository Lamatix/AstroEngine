import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "AstroEngine | Küresel İmparatorluk",
  description: "7/24 Otonom Kehanet ve Medya Üretim Ekosistemi",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}