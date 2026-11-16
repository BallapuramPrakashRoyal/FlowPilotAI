'use client';

import React, { useState } from 'react';
import {
  Zap,
  GitFork,
  Workflow,
  Sparkles,
  ShieldCheck,
  Lock,
  Database,
  ArrowRight,
  Cpu,
  Mail,
  ChevronRight,
  Terminal,
  Activity,
  UserCheck,
  AlertTriangle,
} from 'lucide-react';
import { AuthView } from '@/features/auth/AuthView';
import { User } from '@/types';

interface PublicLandingViewProps {
  onAuthenticated: (user: User) => void;
}

export function PublicLandingView({ onAuthenticated }: PublicLandingViewProps) {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [activeSection, setActiveSection] = useState<'overview' | 'features' | 'architecture' | 'demo' | 'security' | 'quickstart'>('overview');

  return (
    <div className="min-h-screen bg-[#080F20] text-[#F1F6FF] selection:bg-[#287BFA]/30 selection:text-[#53D7F5] relative overflow-x-hidden font-sans">
      {/* Ambient Fluid Glass Lighting (Hardware-accelerated) */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 w-[650px] h-[550px] rounded-full bg-gradient-to-br from-[#287BFA]/12 via-[#438BFF]/06 to-transparent blur-3xl" />
        <div className="absolute top-1/3 -right-32 w-[600px] h-[500px] rounded-full bg-gradient-to-bl from-[#53D7F5]/10 via-[#287BFA]/05 to-transparent blur-3xl" />
        <div className="absolute -bottom-48 left-1/4 w-[750px] h-[600px] rounded-full bg-gradient-to-t from-[#1E3A8A]/12 via-[#111E35]/06 to-transparent blur-3xl" />
      </div>

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 h-16 px-6 md:px-12 bg-[#080F20]/80 backdrop-blur-2xl border-b border-[rgba(67,139,255,0.15)] flex items-center justify-between shadow-[0_4px_24px_rgba(4,9,20,0.5)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#287BFA] via-[#438BFF] to-[#53D7F5] flex items-center justify-center shadow-lg shadow-[#287BFA]/30 ring-1 ring-white/20">
            <Zap className="w-5 h-5 text-white fill-white" />
          </div>
          <div>
            <div className="font-bold text-[#F1F6FF] tracking-tight flex items-center gap-2 text-sm">
              FlowPilot AI
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#287BFA]/15 text-[#53D7F5] border border-[#287BFA]/30">
                v1.0.0
              </span>
            </div>
            <div className="text-[11px] text-[#7285A5]">Autonomous Automation</div>
          </div>
        </div>

        {/* Desktop Nav Links */}
        <nav className="hidden lg:flex items-center gap-1 bg-[#0C1629]/70 p-1 rounded-xl border border-[rgba(67,139,255,0.15)] backdrop-blur-md">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'features', label: 'Features' },
            { id: 'architecture', label: 'Architecture' },
            { id: 'demo', label: 'Demo Workflow' },
            { id: 'security', label: 'Security' },
            { id: 'quickstart', label: 'Quickstart' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveSection(item.id as any);
                document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth' });
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSection === item.id
                  ? 'bg-[#172743] text-[#53D7F5] shadow-sm'
                  : 'text-[#A3B4CF] hover:text-[#F1F6FF]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* CTA Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAuthModal(true)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/25 border border-white/20 transition-all active:scale-95 flex items-center gap-1.5"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Public Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 py-16 space-y-24">
        {/* HERO SECTION */}
        <section id="overview" className="text-center space-y-6 pt-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111E35]/80 border border-[rgba(67,139,255,0.25)] text-xs font-semibold text-[#53D7F5] backdrop-blur-xl shadow-lg">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous AI Automation Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#F1F6FF] tracking-tight max-w-4xl mx-auto leading-tight">
            Governed Multi-Agent AI Orchestration with <span className="bg-gradient-to-r from-[#287BFA] via-[#438BFF] to-[#53D7F5] bg-clip-text text-transparent">Visual DAG Control</span>
          </h1>

          <p className="text-sm sm:text-base text-[#A3B4CF] max-w-2xl mx-auto leading-relaxed">
            Build, simulate, and execute durable agentic workflows with pgvector RAG, human-in-the-loop approvals, and least-privilege Gmail & cloud integrations.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => setShowAuthModal(true)}
              className="px-6 py-3 rounded-2xl bg-gradient-to-r from-[#287BFA] via-[#438BFF] to-[#53D7F5] text-white text-sm font-semibold shadow-xl shadow-[#287BFA]/30 border border-white/25 transition-all hover:-translate-y-0.5 active:scale-95 flex items-center gap-2"
            >
              <span>Explore Workspace Demo</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#architecture"
              className="px-6 py-3 rounded-2xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.2)] text-[#F1F6FF] text-sm font-semibold backdrop-blur-xl transition-all hover:-translate-y-0.5"
            >
              View System Architecture
            </a>
          </div>

          {/* Core Proof-Point Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 pt-12 text-left">
            {[
              {
                title: 'Durable Celery DAGs',
                desc: 'Topological sort, task persistence, bounded retries, and safe crash recovery.',
                icon: Activity,
                color: '#438BFF',
              },
              {
                title: 'pgvector Real RAG',
                desc: 'Cosine vector similarity search, document chunking, and workspace isolation.',
                icon: Database,
                color: '#53D7F5',
              },
              {
                title: 'Human-in-the-Loop',
                desc: 'Cryptographic authorization gates with idempotency safeguards for side effects.',
                icon: UserCheck,
                color: '#28C995',
              },
              {
                title: 'Multi-LLM Abstraction',
                desc: 'Gemini 1.5, Ollama, and OpenAI orchestration with automated fallback.',
                icon: Cpu,
                color: '#F2B65D',
              },
            ].map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.title}
                  className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.4)] hover:bg-[#172743]/85 shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] transition-all duration-200 group hover:-translate-y-1"
                >
                  <div
                    className="w-10 h-10 rounded-2xl flex items-center justify-center mb-4 shadow-sm"
                    style={{ backgroundColor: `${card.color}20`, color: card.color }}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-[#F1F6FF] group-hover:text-[#53D7F5] transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-xs text-[#A3B4CF] mt-2 leading-relaxed">
                    {card.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* FEATURES BREAKDOWN */}
        <section id="features" className="space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F6FF] tracking-tight">
              Production-Grade Enterprise Capabilities
            </h2>
            <p className="text-xs sm:text-sm text-[#A3B4CF]">
              Designed for governed, observable, and resilient autonomous operations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: 'Visual Workflow Studio',
                badge: 'React Flow Canvas',
                desc: 'Infinite canvas with typed input/output handles, DAG cycle validation, live status pills, and JSON payload inspection.',
                icon: Workflow,
              },
              {
                title: 'Multi-Agent Runtime',
                badge: 'Supervisor Architecture',
                desc: 'Specialized Analyst, Researcher, and Executor subagents with deterministic handoffs and strict tool execution registries.',
                icon: GitFork,
              },
              {
                title: 'AI DAG Generator',
                badge: 'Natural Language Synthesis',
                desc: 'Synthesize complete multi-step executable DAG workflows directly from plain English prompts with schema validation.',
                icon: Sparkles,
              },
              {
                title: 'Least-Privilege Integrations',
                badge: 'OAuth 2.0 & Fernet AES-256',
                desc: 'Workspace-scoped Gmail integration requesting minimal scopes with encrypted refresh-token rotation and revocation.',
                icon: Mail,
              },
              {
                title: 'Real-Time Observability',
                badge: 'WebSocket Streaming',
                desc: 'Sub-second event streaming of node progression, token consumption, execution timelines, and audit logs.',
                icon: Terminal,
              },
              {
                title: 'Approval & Idempotency Center',
                badge: 'Zero Silent Mutations',
                desc: 'Review external action payloads, enforce workspace RBAC permissions, and prevent duplicate sends across crash recovery.',
                icon: ShieldCheck,
              },
            ].map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.title}
                  className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.35)] shadow-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="w-9 h-9 rounded-xl bg-[#287BFA]/15 text-[#438BFF] flex items-center justify-center">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0C1629] text-[#53D7F5] border border-[rgba(67,139,255,0.2)]">
                      {feat.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[#F1F6FF]">{feat.title}</h3>
                  <p className="text-xs text-[#A3B4CF] leading-relaxed">{feat.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ARCHITECTURE OVERVIEW */}
        <section id="architecture" className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F6FF] tracking-tight">
              Modular Monolith & Distributed Worker Topology
            </h2>
            <p className="text-xs sm:text-sm text-[#A3B4CF]">
              Clean separation of visual control plane, async DAG execution, and durable vector persistence.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.2)] space-y-6 shadow-2xl">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div className="p-4 rounded-2xl bg-[#0C1629]/80 border border-[#438BFF]/30 space-y-2">
                <span className="text-[10px] font-mono text-[#53D7F5]">UI LAYER</span>
                <h4 className="text-sm font-bold text-[#F1F6FF]">Next.js 16 App Router</h4>
                <p className="text-[11px] text-[#A3B4CF]">React Flow DAG Studio, Blue Liquid Glass Design System, Recharts</p>
              </div>

              <div className="p-4 rounded-2xl bg-[#0C1629]/80 border border-[#28C995]/30 space-y-2">
                <span className="text-[10px] font-mono text-[#28C995]">API GATEWAY</span>
                <h4 className="text-sm font-bold text-[#F1F6FF]">FastAPI Engine</h4>
                <p className="text-[11px] text-[#A3B4CF]">Argon2id Auth, RBAC, WebSockets, Kahn DAG Validation, Rate Limiter</p>
              </div>

              <div className="p-4 rounded-2xl bg-[#0C1629]/80 border border-[#F2B65D]/30 space-y-2">
                <span className="text-[10px] font-mono text-[#F2B65D]">ORCHESTRATION</span>
                <h4 className="text-sm font-bold text-[#F1F6FF]">Celery + Redis</h4>
                <p className="text-[11px] text-[#A3B4CF]">Durable async task execution, graceful SIGTERM shutdown, Beat cron</p>
              </div>

              <div className="p-4 rounded-2xl bg-[#0C1629]/80 border border-[#8DBBFF]/30 space-y-2">
                <span className="text-[10px] font-mono text-[#8DBBFF]">PERSISTENCE</span>
                <h4 className="text-sm font-bold text-[#F1F6FF]">PostgreSQL (pgvector)</h4>
                <p className="text-[11px] text-[#A3B4CF]">Vector embeddings, connection pooling, transparent dual-mode SQLite</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#080F20]/70 border border-[rgba(67,139,255,0.15)] flex items-center justify-between text-xs text-[#A3B4CF]">
              <span className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#28C995]" />
                All internal ports (PostgreSQL :5432, Redis :6379) isolated within container network.
              </span>
              <span className="font-mono text-[#53D7F5]">Non-Root Containers (UID 1001)</span>
            </div>
          </div>
        </section>

        {/* DEMO WORKFLOW WALKTHROUGH */}
        <section id="demo" className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F6FF] tracking-tight">
              Verified End-to-End Autonomous Pipeline
            </h2>
            <p className="text-xs sm:text-sm text-[#A3B4CF]">
              Real-world Gmail integration combined with RAG knowledge research and human authorization.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.2)] space-y-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              {[
                { step: '01', title: 'Gmail Trigger', sub: 'Fetch Unread Email' },
                { step: '02', title: 'RAG Retrieval', sub: 'pgvector Knowledge Base' },
                { step: '03', title: 'Agent Triage', sub: 'Classify & Draft Reply' },
                { step: '04', title: 'Approval Gate', sub: 'Human Authorization' },
                { step: '05', title: 'Send Action', sub: 'Authorized Dispatch' },
              ].map((item, index) => (
                <div key={item.step} className="flex-1 text-center space-y-2 p-3 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.15)]">
                  <div className="text-[10px] font-mono text-[#53D7F5]">STEP {item.step}</div>
                  <div className="text-xs font-bold text-[#F1F6FF]">{item.title}</div>
                  <div className="text-[10px] text-[#7285A5]">{item.sub}</div>
                </div>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-[#080F20]/70 border border-[rgba(67,139,255,0.15)] text-xs text-[#A3B4CF] flex items-center justify-between">
              <span>Execution State: <strong className="text-[#28C995]">COMPLETED</strong> with cryptographic idempotency key</span>
              <button
                onClick={() => setShowAuthModal(true)}
                className="text-xs text-[#53D7F5] font-semibold hover:underline flex items-center gap-1"
              >
                <span>Run pipeline in studio</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </section>

        {/* SECURITY & GOVERNANCE */}
        <section id="security" className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F6FF] tracking-tight">
              Enterprise Security & Tenant Isolation
            </h2>
            <p className="text-xs sm:text-sm text-[#A3B4CF]">
              Built from day one with zero-trust architectural boundaries.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-[#111E35]/65 border border-[rgba(67,139,255,0.18)] space-y-2">
              <ShieldCheck className="w-5 h-5 text-[#28C995]" />
              <h4 className="text-xs font-bold text-[#F1F6FF]">Argon2id Hashing</h4>
              <p className="text-[11px] text-[#A3B4CF]">RFC 9106 parameterization for credential protection at rest.</p>
            </div>

            <div className="p-5 rounded-2xl bg-[#111E35]/65 border border-[rgba(67,139,255,0.18)] space-y-2">
              <Lock className="w-5 h-5 text-[#438BFF]" />
              <h4 className="text-xs font-bold text-[#F1F6FF]">Fernet AES-256</h4>
              <p className="text-[11px] text-[#A3B4CF]">All OAuth access & refresh tokens encrypted at rest in the database.</p>
            </div>

            <div className="p-5 rounded-2xl bg-[#111E35]/65 border border-[rgba(67,139,255,0.18)] space-y-2">
              <AlertTriangle className="w-5 h-5 text-[#F2B65D]" />
              <h4 className="text-xs font-bold text-[#F1F6FF]">Prompt Injection Defense</h4>
              <p className="text-[11px] text-[#A3B4CF]">Untrusted user content enclosed in immutable safety boundaries.</p>
            </div>

            <div className="p-5 rounded-2xl bg-[#111E35]/65 border border-[rgba(67,139,255,0.18)] space-y-2">
              <UserCheck className="w-5 h-5 text-[#53D7F5]" />
              <h4 className="text-xs font-bold text-[#F1F6FF]">Workspace RBAC</h4>
              <p className="text-[11px] text-[#A3B4CF]">Strict tenant isolation enforced across all database queries and vectors.</p>
            </div>
          </div>
        </section>

        {/* QUICKSTART DOCUMENTATION */}
        <section id="quickstart" className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F6FF] tracking-tight">
              One-Command Production Deployment
            </h2>
            <p className="text-xs sm:text-sm text-[#A3B4CF]">
              Get up and running in under 2 minutes with Docker Compose.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-[#0C1629]/90 border border-[rgba(67,139,255,0.22)] font-mono text-xs text-[#F1F6FF] space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[rgba(67,139,255,0.15)] pb-3">
              <span className="text-[#53D7F5]">bash — Production Stack Initialization</span>
              <span className="text-[10px] text-[#7285A5]">docker-compose.yml</span>
            </div>
            <pre className="text-[#A3B4CF] overflow-x-auto py-2 leading-relaxed">
              <code>{`# 1. Clone & Configure Environment
git clone https://github.com/FlowPilotAI/FlowPilotAI.git && cd FlowPilotAI
cp .env.production.example .env

# 2. Build & Launch Containers
docker compose up -d --build

# 3. Verify Health & Open Dashboard
curl http://localhost:8000/health
open http://localhost:3000`}</code>
            </pre>
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-[rgba(67,139,255,0.15)] bg-[#0C1629]/80 backdrop-blur-xl px-6 md:px-12 py-8 text-center text-xs text-[#7285A5]">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#438BFF]" />
            <span className="font-semibold text-[#F1F6FF]">FlowPilot AI</span>
            <span>— Autonomous AI Workflow Automation Platform</span>
          </div>
          <div>© 2026 FlowPilot AI. All rights reserved.</div>
        </div>
      </footer>

      {/* AUTH MODAL / DRAWER */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in">
          <div className="relative w-full max-w-md">
            <button
              onClick={() => setShowAuthModal(false)}
              className="absolute -top-3 -right-3 z-20 w-8 h-8 rounded-full bg-[#111E35] border border-[rgba(67,139,255,0.3)] text-[#A3B4CF] hover:text-white flex items-center justify-center shadow-lg"
            >
              ✕
            </button>
            <AuthView onAuthenticated={onAuthenticated} />
          </div>
        </div>
      )}
    </div>
  );
}
