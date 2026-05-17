import type { Metadata } from "next";
import { Inter, Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider, ThemeToggle } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

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
      <body className={`${inter.variable} ${outfit.variable} ${jetbrainsMono.variable}`}>
        <ThemeProvider>
        {/* Navigation Bar */}
        <nav className="glass-nav" style={{ position: 'sticky', top: 0, zIndex: 50, padding: '1rem 0' }}>
          <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              <a href="/" style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>
                Env<span className="text-gradient">Forge</span>
              </a>
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <a href="/profiles">Profiles</a>
                <a href="/diagnose">Diagnose</a>
                <a href="/troubleshoot">AI Troubleshoot</a>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <ThemeToggle />
              <a href="https://github.com/rishabh0510rishabh/EnvForage" target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
                GitHub
              </a>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main style={{ minHeight: 'calc(100vh - 140px)' }}>
          {children}
        </main>

        {/* Footer */}
        <footer style={{ borderTop: '1px solid var(--border-subtle)', padding: '2rem 0', marginTop: '4rem', color: 'var(--text-muted)' }}>
          <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
            <p>© {new Date().getFullYear()} EnvForge. Open Source Tooling.</p>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <a href="/docs">Documentation</a>
              <a href="/privacy">Privacy</a>
            </div>
          </div>
        </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
