'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  GitFork,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Play,
  Layers,
  ChevronRight,
  TrendingUp,
  Cpu,
  Compass,
  History,
  Bot,
  Zap,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api } from '@/services/api';
import { AnalyticsOverview } from '@/types';

export function DashboardView() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const stats = await api.getAnalytics();
        setData(stats);
      } catch (e) {
        console.error('Failed to load analytics', e);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const totalExecs = data?.total_executions ?? (data ? data.successful_executions + data.failed_executions : 0);
  const successRate = data?.success_rate_percent ?? (totalExecs > 0 && data ? Math.round((data.successful_executions / totalExecs) * 1000) / 10 : 0);
  const failureRate = data?.failure_rate_percent ?? (totalExecs > 0 && data ? Math.round((data.failed_executions / totalExecs) * 1000) / 10 : 0);

  const statsCards = [
    {
      title: 'Total Workflows',
      value: data ? data.total_workflows : 0,
      sub: `${data ? data.active_workflows : 0} active`,
      icon: GitFork,
      color: '#438BFF',
      accentGlow: 'rgba(67, 139, 255, 0.25)',
      href: '/workflows',
    },
    {
      title: 'Total Executions',
      value: totalExecs,
      sub: `${successRate}% success rate`,
      icon: CheckCircle2,
      color: '#28C995',
      accentGlow: 'rgba(40, 201, 149, 0.25)',
      href: '/executions',
    },
    {
      title: 'Pending Approvals',
      value: data ? data.pending_approvals : 0,
      sub: 'Awaiting human authorization',
      icon: AlertCircle,
      color: '#F2B65D',
      accentGlow: 'rgba(242, 182, 93, 0.25)',
      href: '/approvals',
      highlight: data && data.pending_approvals > 0,
    },
    {
      title: 'Avg Latency',
      value: data && data.avg_duration_ms > 0 ? `${data.avg_duration_ms}ms` : '0ms',
      sub: 'Topological async DAG',
      icon: Clock,
      color: '#53D7F5',
      accentGlow: 'rgba(83, 215, 245, 0.25)',
      href: '/analytics',
    },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Hero Liquid Glass Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#0C1629]/95 via-[#111E35]/90 to-[#172743]/85 p-7 border border-[rgba(67,139,255,0.22)] shadow-[0_16px_40px_rgba(4,9,20,0.6),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl transition-all">
        {/* Subtle decorative inner corner glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-[#53D7F5]/10 via-[#287BFA]/05 to-transparent rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-3.5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] shadow-[0_0_12px_rgba(40,123,250,0.25)]">
            <Zap className="w-3.5 h-3.5 text-[#53D7F5]" />
            <span>Autonomous Multi-Agent Orchestration & Real RAG</span>
          </div>

          <h2 className="text-2xl lg:text-3xl font-bold text-[#F1F6FF] tracking-tight leading-tight">
            Design, Automate & Observe AI Workflows with Fluid Precision.
          </h2>

          <p className="text-sm text-[#A3B4CF] leading-relaxed">
            FlowPilot combines durable multi-agent execution, pgvector knowledge retrieval, Gmail OAuth 2.0 side-effects, and human-in-the-loop governance inside a high-speed asynchronous engine.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              href="/generator"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/30 border border-white/20 transition-all hover:-translate-y-0.5 active:translate-y-0"
            >
              <Sparkles className="w-4 h-4 text-white" />
              <span>Generate AI Workflow</span>
            </Link>

            <Link
              href="/onboarding"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#111E35]/80 hover:bg-[#172743] text-[#F1F6FF] text-xs font-semibold border border-[rgba(67,139,255,0.2)] hover:border-[rgba(83,215,245,0.35)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] transition-all hover:-translate-y-0.5"
            >
              <Compass className="w-4 h-4 text-[#28C995]" />
              <span>Interactive Guided Setup</span>
            </Link>

            <Link
              href="/studio"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#111E35]/50 hover:bg-[#172743] text-[#A3B4CF] hover:text-white text-xs font-semibold border border-[rgba(67,139,255,0.12)] transition-all hover:-translate-y-0.5"
            >
              <GitFork className="w-4 h-4 text-[#438BFF]" />
              <span>Open Studio</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.title}
              href={card.href}
              className={`p-5 rounded-2xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.4)] hover:bg-[#172743]/85 shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_8px_24px_rgba(4,9,20,0.35)] transition-all duration-200 group relative hover:-translate-y-1 ${
                card.highlight ? 'ring-1 ring-[#F2B65D]/50 shadow-[0_0_20px_rgba(242,182,93,0.15)]' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-[#A3B4CF]">{card.title}</span>
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 shadow-sm"
                  style={{
                    backgroundColor: `${card.color}20`,
                    color: card.color,
                    boxShadow: `0 0 12px ${card.accentGlow}`,
                  }}
                >
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className="text-2xl font-bold text-[#F1F6FF] mb-1 tracking-tight font-sans">
                {loading ? <span className="text-[#7285A5] animate-pulse">--</span> : card.value}
              </div>

              <div className="text-xs text-[#7285A5] flex items-center justify-between">
                <span>{card.sub}</span>
                <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-[#53D7F5]" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Secondary Metrics Bar: AI Token Usage & Integrations */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* AI Tokens & Cost */}
        <div className="p-5 rounded-2xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_8px_24px_rgba(4,9,20,0.3)] flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-[#A3B4CF]">Total Tokens Consumed</span>
            <div className="text-xl font-bold text-[#F1F6FF] font-mono">
              {loading ? '--' : (data?.total_tokens_consumed ?? 0).toLocaleString()}
            </div>
            <span className="text-[11px] font-medium text-[#28C995] flex items-center gap-1">
              Est. Cost: ${data?.estimated_cost_usd?.toFixed(4) ?? '0.0000'} USD
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[#287BFA]/15 border border-[#438BFF]/35 flex items-center justify-center shadow-[0_0_16px_rgba(40,123,250,0.2)]">
            <Cpu className="w-5 h-5 text-[#438BFF]" />
          </div>
        </div>

        {/* Execution Reliability Rate */}
        <div className="p-5 rounded-2xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_8px_24px_rgba(4,9,20,0.3)] flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-[#A3B4CF]">Reliability Breakdown</span>
            <div className="text-xl font-bold text-[#F1F6FF]">
              {loading ? '--' : `${successRate}% Pass`}
            </div>
            <span className="text-[11px] text-[#7285A5]">
              {data?.successful_executions ?? 0} Succeeded · {data?.failed_executions ?? 0} Failed ({failureRate}%)
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[#28C995]/15 border border-[#28C995]/35 flex items-center justify-center shadow-[0_0_16px_rgba(40,201,149,0.2)]">
            <CheckCircle2 className="w-5 h-5 text-[#28C995]" />
          </div>
        </div>

        {/* Connected Integrations */}
        <div className="p-5 rounded-2xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_8px_24px_rgba(4,9,20,0.3)] flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-[#A3B4CF]">Connected Integrations</span>
            <div className="text-xl font-bold text-[#F1F6FF]">
              {loading ? '--' : `${data?.connected_integrations_count ?? 0} Active`}
            </div>
            <Link href="/integrations" className="text-[11px] text-[#53D7F5] hover:underline flex items-center gap-1 font-medium">
              <span>Manage Integration Hub</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[#F2B65D]/15 border border-[#F2B65D]/35 flex items-center justify-center shadow-[0_0_16px_rgba(242,182,93,0.2)]">
            <Layers className="w-5 h-5 text-[#F2B65D]" />
          </div>
        </div>
      </div>

      {/* Main Split: Execution Volume Chart & Recent Executions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Execution Throughput (7 Days)</h3>
              <p className="text-xs text-[#7285A5]">Persisted asynchronous DAG runs over the last week</p>
            </div>
            <div className="flex items-center gap-2 text-xs font-medium text-[#28C995] bg-[#28C995]/15 px-3 py-1 rounded-full border border-[#28C995]/30 shadow-[0_0_10px_rgba(40,201,149,0.2)]">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Live Database Telemetry</span>
            </div>
          </div>

          <div className="h-64 w-full pt-4">
            {loading ? (
              <div className="h-full flex items-center justify-center text-xs text-[#7285A5] animate-pulse">
                Loading database metrics...
              </div>
            ) : data && data.execution_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.execution_trends}>
                  <defs>
                    <linearGradient id="execBlueGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#438BFF" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#438BFF" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="date"
                    stroke="#7285A5"
                    fontSize={11}
                    tickLine={false}
                    axisLine={{ stroke: 'rgba(67, 139, 255, 0.15)' }}
                  />
                  <YAxis
                    stroke="#7285A5"
                    fontSize={11}
                    tickLine={false}
                    axisLine={{ stroke: 'rgba(67, 139, 255, 0.15)' }}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0C1629',
                      borderColor: 'rgba(67, 139, 255, 0.3)',
                      borderRadius: '1rem',
                      boxShadow: '0 8px 32px rgba(4, 9, 20, 0.6)',
                      fontSize: '12px',
                      color: '#F1F6FF',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="executions"
                    stroke="#438BFF"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#execBlueGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-[#7285A5]">
                No execution trends recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Recent Executions Feed */}
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Recent Executions</h3>
                <p className="text-xs text-[#7285A5]">Latest DAG dispatches</p>
              </div>
              <Link href="/executions" className="text-xs text-[#53D7F5] hover:underline flex items-center gap-1 font-medium">
                <span>View all</span>
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-2">
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 rounded-xl bg-[#0C1629]/60 animate-pulse border border-[rgba(67,139,255,0.08)]" />
                  ))}
                </div>
              ) : data && data.recent_activity.length > 0 ? (
                data.recent_activity.slice(0, 5).map((act) => (
                  <Link
                    key={act.id}
                    href={`/executions?selected=${act.id}`}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-[#0C1629]/60 border border-[rgba(67,139,255,0.12)] hover:border-[rgba(83,215,245,0.3)] hover:bg-[#172743]/80 transition-all group"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`w-2 h-2 rounded-full shrink-0 ${
                          act.status === 'COMPLETED'
                            ? 'bg-[#28C995] shadow-[0_0_8px_rgba(40,201,149,0.7)]'
                            : act.status === 'FAILED'
                            ? 'bg-[#F16B7A] shadow-[0_0_8px_rgba(241,107,122,0.7)]'
                            : act.status === 'WAITING_APPROVAL'
                            ? 'bg-[#F2B65D] shadow-[0_0_8px_rgba(242,182,93,0.7)]'
                            : 'bg-[#438BFF] shadow-[0_0_8px_rgba(67,139,255,0.7)]'
                        }`}
                      />
                      <div className="truncate">
                        <div className="text-xs font-medium text-[#F1F6FF] truncate group-hover:text-[#53D7F5] transition-colors">
                          {act.workflow_name}
                        </div>
                        <div className="text-[10px] text-[#7285A5] font-mono">
                          {act.id.slice(0, 8)} · {act.duration_ms}ms
                        </div>
                      </div>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 border ${
                        act.status === 'COMPLETED'
                          ? 'bg-[#28C995]/15 text-[#28C995] border-[#28C995]/30'
                          : act.status === 'FAILED'
                          ? 'bg-[#F16B7A]/15 text-[#F16B7A] border-[#F16B7A]/30'
                          : act.status === 'WAITING_APPROVAL'
                          ? 'bg-[#F2B65D]/15 text-[#F2B65D] border-[#F2B65D]/30'
                          : 'bg-[#438BFF]/15 text-[#438BFF] border-[#438BFF]/30'
                      }`}
                    >
                      {act.status}
                    </span>
                  </Link>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-[#7285A5]">
                  No executions recorded yet.
                </div>
              )}
            </div>
          </div>

          <Link
            href="/studio"
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#0C1629]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] font-medium transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
          >
            <Play className="w-3.5 h-3.5 text-[#438BFF] fill-[#438BFF]" />
            <span>Launch New Run in Studio</span>
          </Link>
        </div>
      </div>

      {/* Lower Row: Agent Observability Activity & Recent Audit Log Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Activity */}
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#438BFF]" />
              <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Recent Agent Activity</h3>
            </div>
            <Link href="/executions" className="text-xs text-[#53D7F5] hover:underline flex items-center gap-1 font-medium">
              <span>View telemetry</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-2">
            {loading ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-14 rounded-xl bg-[#0C1629]/60 animate-pulse border border-[rgba(67,139,255,0.08)]" />
                ))}
              </div>
            ) : data && data.recent_agent_runs && data.recent_agent_runs.length > 0 ? (
              data.recent_agent_runs.slice(0, 4).map((run) => (
                <div
                  key={run.id}
                  className="p-3 rounded-xl bg-[#0C1629]/60 border border-[rgba(67,139,255,0.12)] flex items-center justify-between hover:border-[rgba(67,139,255,0.25)] transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-semibold text-[#F1F6FF] flex items-center gap-2">
                      <span>{run.agent_role}</span>
                      <span className="text-[10px] font-mono text-[#7285A5]">({run.task_id || 'task'})</span>
                    </div>
                    <div className="text-[11px] text-[#A3B4CF]">
                      Tokens: <span className="font-mono text-[#53D7F5]">{run.token_count}</span> · Latency: <span className="font-mono text-[#F1F6FF]">{run.latency_ms}ms</span>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      run.status === 'COMPLETED'
                        ? 'bg-[#28C995]/15 text-[#28C995] border-[#28C995]/30'
                        : run.status === 'FAILED'
                        ? 'bg-[#F16B7A]/15 text-[#F16B7A] border-[#F16B7A]/30'
                        : 'bg-[#438BFF]/15 text-[#438BFF] border-[#438BFF]/30'
                    }`}
                  >
                    {run.status}
                  </span>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-xs text-[#7285A5]">
                No agent executions recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Audit Log Stream */}
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-[#28C995]" />
              <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Recent Audit Activity</h3>
            </div>
            <span className="text-[10px] font-mono text-[#7285A5] px-2 py-0.5 rounded bg-[#0C1629] border border-[rgba(67,139,255,0.15)]">Immutable Audit Trail</span>
          </div>

          <div className="space-y-2">
            {loading ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-14 rounded-xl bg-[#0C1629]/60 animate-pulse border border-[rgba(67,139,255,0.08)]" />
                ))}
              </div>
            ) : data && data.recent_audit_logs && data.recent_audit_logs.length > 0 ? (
              data.recent_audit_logs.slice(0, 4).map((audit) => (
                <div
                  key={audit.id}
                  className="p-3 rounded-xl bg-[#0C1629]/60 border border-[rgba(67,139,255,0.12)] flex items-center justify-between hover:border-[rgba(67,139,255,0.25)] transition-colors"
                >
                  <div className="space-y-0.5 truncate pr-2">
                    <div className="text-xs font-semibold text-[#F1F6FF] truncate font-mono">
                      {audit.action}
                    </div>
                    <div className="text-[10px] text-[#7285A5] truncate">
                      {audit.resource_type}: {audit.resource_id ? audit.resource_id.slice(0, 8) : 'workspace'}
                    </div>
                  </div>
                  <span className="text-[10px] text-[#7285A5] font-mono shrink-0">
                    {audit.created_at ? new Date(audit.created_at).toLocaleTimeString() : 'Recent'}
                  </span>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-xs text-[#7285A5]">
                No audit activity recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
