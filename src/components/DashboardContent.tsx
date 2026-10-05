"use client";

import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Activity, Server, Zap, GitBranch, Shield, Globe,
  CheckCircle, AlertCircle, Lock, Cloud, Github
} from "lucide-react";

// --- Constants & Metadata ---
const CHECK_META: Record<string, { label: string; description: string }> = {
  tlsEnforced: {
    label: "TLS/HTTPS enforced",
    description: "Force HTTPS across all endpoints.",
  },
  sslCertificateExpiry: {
    label: "SSL Certificate Validity",
    description: "Checks if HTTPS is enforced + certificate isn't expired.",
  },
  enhancedSecretsScanning: {
    label: "Enhanced Secrets Scanning",
    description: "Scans all repository files for exposed secrets and API keys.",
  },
  dnsSecurityChecks: {
    label: "DNS Security Checks",
    description: "Validates SPF, DKIM, DMARC records.",
  },
  dependencyVulnerabilityScanning: {
    label: "Dependency Vulnerability Scanning",
    description: "Scans dependencies for known security vulnerabilities.",
  },
  adminMfa: {
    label: "Admin MFA enabled",
    description: "MFA required on all admin accounts (AWS/GitHub).",
  },
  rootAccountSecurity: {
    label: "Root Account Security",
    description: "AWS root account follows best practices.",
  },
  publicBuckets: {
    label: "No public S3 buckets",
    description: "Detects any world-readable buckets.",
  },
};

// --- Mock Helpers ---
async function mockFetchConnections() {
  return new Promise((res) =>
    setTimeout(() => res({ aws: true, github: false }), 800)
  );
}

async function mockFetchResults(enabled: string[]) {
  const now = new Date().toISOString();
  // Simulate random results
  const fakeResults = enabled.map(key => ({
    key,
    status: Math.random() > 0.2 ? "pass" : "fail",
    lastRunAt: now,
    details: Math.random() > 0.2 ? "Check passed" : "Critical issue found"
  }));

  return new Promise((res) =>
    setTimeout(() => res(fakeResults), 1500)
  );
}

// --- Components ---

function AnimatedMetricCard({ title, value, total, subtitle, icon, color, delay }: any) {
  const progress = total ? (typeof value === 'number' ? value / total : 0) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
    >
      <div className={`absolute -right-4 -top-4 h-24 w-24 rounded-full opacity-20 bg-${color}-500 blur-2xl`} />
      <div className="relative z-10">
        <div className="mb-4 flex items-center justify-between">
          <div className={`rounded-lg bg-${color}-500/20 p-2 text-${color}-400`}>
            {icon}
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-3xl font-bold text-white">{value}</div>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}

          {total !== undefined && (
            <div className="mt-2 h-2 w-full rounded-full bg-slate-700">
              <motion.div
                className={`h-2 rounded-full bg-${color}-500`}
                initial={{ width: 0 }}
                animate={{ width: `${progress * 100}%` }}
                transition={{ duration: 1, delay: delay + 0.5 }}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function AnimatedCheckCard({ keyName, enabled, onToggle, result, delay }: any) {
  const meta = CHECK_META[keyName];
  const isPass = result?.status === "pass";
  const isFail = result?.status === "fail";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay }}
      className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-colors hover:bg-white/10"
    >
      <div className="flex items-start justify-between">
        <div className="mr-4 flex-1">
          <h4 className="mb-2 text-lg font-semibold text-white">{meta.label}</h4>
          <p className="text-sm text-slate-400">{meta.description}</p>
        </div>

        <label className="relative inline-flex cursor-pointer items-center">
          <input
            type="checkbox"
            checked={enabled}
            onChange={() => onToggle(keyName)}
            className="peer sr-only"
          />
          <div className="peer h-6 w-11 rounded-full bg-slate-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-focus:outline-none dark:border-gray-600"></div>
        </label>
      </div>

      {/* Result Status Area */}
      {result && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className={`mt-4 rounded-xl p-3 ${
            isPass ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
          }`}
        >
          <div className="flex items-center gap-2">
            {isPass ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
            <span className="font-medium">{result.details}</span>
          </div>
          <p className="mt-1 text-xs opacity-70">
            Last checked: {new Date(result.lastRunAt).toLocaleTimeString()}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}

// --- Main Page Component ---

export default function DashboardContent() {
  const [connections, setConnections] = useState<any>({ aws: false, github: false });
  const [enabledChecks, setEnabledChecks] = useState(Object.keys(CHECK_META));
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load initial state
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      const conns = await mockFetchConnections();
      setConnections(conns);
      setIsLoading(false);
    };
    loadData();
  }, []);

  const handleToggle = (key: string) => {
    setEnabledChecks((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const runChecks = async () => {
    setRunning(true);
    // In a real app, this would call your Python API
    const res = await mockFetchResults(enabledChecks);
    setResults(res as any[]);
    setRunning(false);
  };

  const passCount = results.filter((r) => r.status === "pass").length;
  const passRate = results.length ? Math.round((passCount / results.length) * 100) : 0;

  return (
    <div className="relative min-h-screen p-4 sm:p-8 text-white">
      {/* Background Blobs */}
      <div className="fixed -left-4 top-0 h-72 w-72 animate-blob rounded-full bg-purple-500 opacity-20 mix-blend-multiply blur-3xl filter" />
      <div className="fixed -right-4 top-0 h-72 w-72 animate-blob rounded-full bg-indigo-500 opacity-20 mix-blend-multiply blur-3xl filter animation-delay-2000" />

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative z-10 mx-auto max-w-7xl"
      >
        {/* Header */}
        <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-4xl font-bold text-transparent">
              TrustStack Dashboard
            </h1>
          </div>

          <button
            onClick={runChecks}
            disabled={running || isLoading}
            className={`group relative flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white shadow-lg transition-all ${
              running ? "bg-slate-700 cursor-not-allowed" : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:scale-105 hover:shadow-indigo-500/25"
            }`}
          >
            {running ? (
              <>
                <Zap className="animate-spin" size={18} /> Scanning...
              </>
            ) : (
              <>
                <Zap size={18} /> Run Security Checks
              </>
            )}
          </button>
        </div>

        {/* Stats Grid */}
        <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <AnimatedMetricCard
            title="Active Integrations"
            value={Object.values(connections).filter(Boolean).length}
            total={2}
            icon={<Globe />}
            color="blue"
            delay={0.1}
          />
          <AnimatedMetricCard
            title="Checks Enabled"
            value={enabledChecks.length}
            total={Object.keys(CHECK_META).length}
            icon={<Shield />}
            color="green"
            delay={0.2}
          />
          <AnimatedMetricCard
            title="Pass Rate"
            value={`${passRate}%`}
            subtitle={results.length ? `${passCount}/${results.length} Passing` : "No data yet"}
            icon={<Activity />}
            color="purple"
            delay={0.3}
          />
           <AnimatedMetricCard
            title="System Status"
            value="Healthy"
            icon={<Server />}
            color="orange"
            delay={0.4}
          />
        </div>

        {/* Integration Status */}
        <section className="mb-8">
          <h2 className="mb-6 text-xl font-bold text-white">Integrations</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
              <div className="flex items-center gap-4">
                <div className="rounded-lg bg-orange-500/20 p-3 text-orange-500">
                  <Cloud size={24} />
                </div>
                <div>
                  <h3 className="font-semibold">AWS Cloud</h3>
                  <p className="text-sm text-slate-400">Infrastructure scanning</p>
                </div>
              </div>
              <div className={`rounded-full px-3 py-1 text-xs font-medium ${connections.aws ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'}`}>
                {connections.aws ? 'Connected' : 'Disconnected'}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
              <div className="flex items-center gap-4">
                <div className="rounded-lg bg-white/10 p-3 text-white">
                  <Github size={24} />
                </div>
                <div>
                  <h3 className="font-semibold">GitHub</h3>
                  <p className="text-sm text-slate-400">Code & Secret scanning</p>
                </div>
              </div>
              <div className={`rounded-full px-3 py-1 text-xs font-medium ${connections.github ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'}`}>
                {connections.github ? 'Connected' : 'Disconnected'}
              </div>
            </div>
          </div>
        </section>

        {/* Security Checks Grid */}
        <section>
          <h2 className="mb-6 text-xl font-bold text-white">Active Security Checks</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Object.keys(CHECK_META).map((key, index) => (
              <AnimatedCheckCard
                key={key}
                keyName={key}
                enabled={enabledChecks.includes(key)}
                onToggle={handleToggle}
                result={results.find((r) => r.key === key)}
                delay={index * 0.05}
              />
            ))}
          </div>
        </section>
      </motion.div>
    </div>
  );
}
