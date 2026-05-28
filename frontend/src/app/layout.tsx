import type { Metadata } from "next";
import { Inter, Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./providers";
import Link from "next/link";
import Navbar from "./components/Navbar";
import CurrentYear from "./components/CurrentYear";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit", display: "swap" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono", display: "swap" });

export const metadata: Metadata = {
  title: "EnvForge | ML Environment Provisioning",
  description: "Generate intelligent, safe, and deterministic ML/AI environment setup scripts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${outfit.variable} ${jetbrainsMono.variable}`} style={{ backgroundColor: "var(--bg-core)" }}>
        <ThemeProvider>
        {/* Navigation Header */}
        <Navbar />

        {/* Main Content */}
        <main style={{ minHeight: "calc(100vh - 140px)" }}>
          {children}
        </main>

        {/* Footer */}
        <footer 
          className="glass-footer" 
          style={{ 
            padding: "2.5rem 0", 
            marginTop: "5rem", 
            color: "var(--text-muted)",
          }}
        >
          <div className="container" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem" }}>
            <p>© <CurrentYear /> EnvForge. Open Source Tooling.</p>
            <div style={{ display: "flex", gap: "1.5rem" }}>
              <Link href="/docs" style={{ transition: "color var(--transition-fast)" }}>Documentation</Link>
              <Link href="/privacy" style={{ transition: "color var(--transition-fast)" }}>Privacy</Link>
            </div>
          </div>
        </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
