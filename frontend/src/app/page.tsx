"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Zap, Shield, Brain, Cpu } from "lucide-react";

export default function HomePage() {
  const features = [
    {
      icon: Zap,
      title: "Lightning Fast Setup",
      description: "Generate ML environment scripts in seconds, not hours",
    },
    {
      icon: Shield,
      title: "Safety First",
      description: "AI-powered validation prevents harmful configurations",
    },
    {
      icon: Brain,
      title: "AI-Powered",
      description: "Get intelligent recommendations for your setup",
    },
    {
      icon: Cpu,
      title: "Hardware Aware",
      description: "Optimized scripts for your specific hardware",
    },
  ];

  return (
    <div
      className="relative overflow-hidden"
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background:
          "radial-gradient(circle at top left, rgba(34,197,94,0.15), transparent 30%), radial-gradient(circle at bottom right, rgba(59,130,246,0.15), transparent 30%), var(--bg-primary)",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: "300px",
          height: "300px",
          borderRadius: "999px",
          background: "rgba(34,197,94,0.25)",
          filter: "blur(120px)",
          top: "-100px",
          left: "-100px",
          animation: "float 6s ease-in-out infinite",
        }}
      />
      {/* Hero Section */}
<section
  style={{
    paddingTop: "8rem",
    paddingBottom: "6rem",
    position: "relative",
  }}
>
  <div
    className="container"
    style={{
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "4rem",
      alignItems: "center",
    }}
  >
    {/* LEFT */}
    <motion.div
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8 }}
    >
      <h1
        style={{
          fontSize: "5rem",
          fontWeight: 800,
          lineHeight: "1.1",
          marginBottom: "1.5rem",
          background: "linear-gradient(to right, #22c55e, #06b6d4, #3b82f6)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          textShadow: "0 0 30px rgba(34,197,94,0.35)",
        }}
      >
        Build ML Environments Faster ⚡
      </h1>

      <p
        style={{
          fontSize: "1.2rem",
          color: "var(--text-secondary)",
          marginBottom: "2rem",
        }}
      >
        Generate safe and optimized AI/ML setup scripts with a modern developer experience.
      </p>

      <div style={{ display: "flex", gap: "1rem" }}>
        <Link
          href="/diagnose"
          style={{
            padding: "1rem 2rem",
            borderRadius: "16px",
            background: "linear-gradient(to right,#22c55e,#16a34a)",
            color: "white",
            fontWeight: 600,
            textDecoration: "none",
            boxShadow: "0 10px 30px rgba(34,197,94,0.3)",
          }}
        >
          Get Started
        </Link>

        <Link
          href="/profiles"
          style={{
            padding: "1rem 2rem",
            borderRadius: "16px",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "white",
            textDecoration: "none",
            backdropFilter: "blur(10px)",
            background: "rgba(255,255,255,0.05)",
          }}
        >
          Browse Profiles
        </Link>
      </div>
    </motion.div>

    {/* RIGHT */}
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      style={{
        position: "relative",
      }}
    >
      <div
        style={{
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: "24px",
          padding: "2rem",
          backdropFilter: "blur(12px)",
          boxShadow: "0 10px 40px rgba(0,0,0,0.4)",
        }}
      >
        <div
          style={{
            height: "300px",
            borderRadius: "20px",
            background:
              "linear-gradient(135deg, rgba(34,197,94,0.2), rgba(59,130,246,0.2))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "2rem",
            fontWeight: 700,
            color: "white",
          }}
        >
          ⚡ AI Powered Setup
        </div>
      </div>
    </motion.div>
  </div>
</section>

      {/* Features Section */}
      <section style={{ paddingTop: '4rem', paddingBottom: '4rem', background: 'rgba(0,0,0,0.2)' }}>
        <div className="container">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.6 }}>
            <h2 style={{ textAlign: 'center', fontSize: '2.5rem', marginBottom: '4rem' }}>Why Choose EnvForge?</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem' }}>
              {features.map((feature, i) => {
                const Icon = feature.icon;
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + i * 0.1 }}
                    className="glass-panel"
                    style={{
  padding: "2rem",
  textAlign: "center",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "24px",
  backdropFilter: "blur(10px)",
  transition: "all 0.3s ease",
  boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
}}
                  >
                    <Icon
  size={45}
  color="#22c55e"
  style={{
    margin: "0 auto 1rem",
    filter: "drop-shadow(0 0 12px rgba(34,197,94,0.6))",
  }}
/>
                    <h3 style={{ marginBottom: '0.75rem' }}>{feature.title}</h3>
                    <p style={{ color: 'var(--text-secondary)' }}>{feature.description}</p>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section style={{ paddingTop: '4rem', paddingBottom: '4rem' }}>
        <div className="container">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.6 }}>
            <h2 style={{ textAlign: 'center', fontSize: '2.5rem', marginBottom: '4rem' }}>How It Works</h2>
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              {[
                { num: 1, title: "Run Diagnostics", desc: "Use `envforge diagnose` to analyze your system" },
                { num: 2, title: "Choose Profile", desc: "Select your ML framework (PyTorch, TensorFlow, etc.)" },
                { num: 3, title: "Verify Compatibility", desc: "EnvForge checks your hardware compatibility" },
                { num: 4, title: "Generate Script", desc: "Get a safe, optimized setup script" },
              ].map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  style={{ display: 'flex', gap: '2rem', marginBottom: i < 3 ? '2rem' : 0, alignItems: 'flex-start' }}
                >
                  <div style={{ background: 'var(--brand-primary)', color: 'white', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, flexShrink: 0 }}>
                    {step.num}
                  </div>
                  <div style={{ paddingTop: '0.5rem' }}>
                    <h4 style={{ marginBottom: '0.5rem' }}>{step.title}</h4>
                    <p style={{ color: 'var(--text-secondary)' }}>{step.desc}</p>
                  </div>
                  {i < 3 && <div style={{ width: '2px', background: 'var(--border-strong)', margin: '-2rem 0 0 0', flexGrow: 1 }} />}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ paddingTop: '4rem', paddingBottom: '6rem', background: 'rgba(99, 102, 241, 0.05)', marginTop: '2rem' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.6, duration: 0.6 }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '1.5rem' }}>Ready to Set Up Your Environment?</h2>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Start with diagnostics or explore our ML profiles
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link href="/diagnose" className="btn btn-primary" style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}>
                Run Diagnostics
              </Link>
              <Link href="/profiles" className="btn btn-secondary" style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}>
                View Profiles
              </Link>
              <Link href="/troubleshoot" className="btn btn-secondary" style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}>
                AI Troubleshoot
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
