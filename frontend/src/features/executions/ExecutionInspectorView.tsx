'use client';

import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  RotateCcw,
  ChevronRight,
  Database,
  Terminal,
  Radio,
  Cpu,
  Bot,
  ArrowRight,
  Wrench,
  Check,
  XCircle,
  ShieldCheck,
  AlertOctagon,
  Ban,
  Layers,
} from 'lucide-react';
import { api } from '@/services/api';
import { AgentRun, Execution, ExecutionEvent } from '@/types';

export function ExecutionInspectorView() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedAgentRunId, setSelectedAgentRunId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [cancelling, setCancelling] = useState(false);

  const loadExecutions = async () => {
    try {
      setError(null);
      const data = await api.listExecutions();
      setExecutions(data);
      setSelectedExecution((prev) => {
        if (!prev && data.length > 0) return data[0];
        if (prev) {
          const updated = data.find((d) => d.id === prev.id);
          return updated || prev;
        }
        return null;
      });
    } catch (e) {
      console.error('Failed to load executions:', e);
      setError(e instanceof Error ? e.message : 'Unable to load executions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExecutions();
    const interval = setInterval(loadExecutions, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let active = true;
    if (!selectedExecution) {
      setEvents([]);
      setAgentRuns([]);
      return;
    }
    setEventsLoading(true);
    setEventsError(null);
    api.listExecutionEvents(selectedExecution.id)
      .then((data) => {
        if (active) setEvents(data);
      })
      .catch((e) => {
        if (active) {
          setEvents([]);
          setEventsError(e instanceof Error ? e.message : 'Unable to load execution events.');
        }
      })
      .finally(() => {
        if (active) setEventsLoading(false);
      });
    return () => { active = false; };
  }, [selectedExecution?.id]);

  useEffect(() => {
    if (!selectedExecution) return;
    api.listAgentRuns(selectedExecution.id)
      .then((runs) => {
        setAgentRuns(runs);
        if (runs.length > 0 && !selectedAgentRunId) {
          setSelectedAgentRunId(runs[0].id);
        }
      })
      .catch(() => setAgentRuns([]));
  }, [selectedExecution?.id]);

  const handleCancel = async () => {
    if (!selectedExecution) return;
    try {
      setCancelling(true);
      await api.cancelExecution(selectedExecution.id);
      await loadExecutions();
    } catch (e: any) {
      alert(e.message || 'Failed to cancel execution');
    } finally {
      setCancelling(false);
    }
  };

  const activeNode = selectedExecution?.nodes?.find((n) => n.node_id === selectedNodeId) || selectedExecution?.nodes?.[0];
  const activeAgentRun = agentRuns.find((r) => r.id === selectedAgentRunId) || agentRuns[0];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] mb-2 shadow-[0_0_12px_rgba(40,123,250,0.2)]">
            <Activity className="w-3.5 h-3.5" />
            <span>Execution Observability & Multi-Agent Telemetry</span>
          </div>
          <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Execution Inspector</h1>
          <p className="text-sm text-[#A3B4CF]">
            Inspect live and historical DAG executions, agent handoffs, tool traces, token consumption, and durable recovery.
          </p>
        </div>

        {selectedExecution && ['RUNNING', 'QUEUED', 'WAITING_APPROVAL'].includes(selectedExecution.status) && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#F16B7A]/15 hover:bg-[#F16B7A]/25 text-[#F16B7A] text-xs font-semibold border border-[#F16B7A]/35 shadow-[0_0_16px_rgba(241,107,122,0.2)] transition-all disabled:opacity-50"
          >
            <Ban className="w-3.5 h-3.5" />
            <span>Cancel Execution</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Executions List */}
        <div className="p-5 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-3">
          <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Executions</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0C1629] text-[#53D7F5] border border-[rgba(67,139,255,0.2)]">{executions.length}</span>
          </div>

          {loading ? (
            <div className="text-center py-12 text-xs text-[#7285A5] animate-pulse">
              Loading execution traces...
            </div>
          ) : error ? (
            <div className="text-center py-12 text-xs text-[#F16B7A]">{error}</div>
          ) : executions.length === 0 ? (
            <div className="text-center py-12 text-xs text-[#7285A5]">
              No executions found. Run a workflow or agent plan to inspect traces.
            </div>
          ) : (
            <div className="space-y-2 max-h-[750px] overflow-y-auto pr-1">
              {executions.map((exc) => (
                <button
                  key={exc.id}
                  onClick={() => {
                    setSelectedExecution(exc);
                    setSelectedNodeId(null);
                    setSelectedAgentRunId(null);
                  }}
                  className={`w-full p-3.5 rounded-2xl text-left border transition-all ${
                    selectedExecution?.id === exc.id
                      ? 'bg-[#172743]/90 border-[#438BFF] shadow-[0_0_20px_rgba(67,139,255,0.25),inset_0_1px_0_rgba(255,255,255,0.15)] text-[#F1F6FF]'
                      : 'bg-[#0C1629]/60 border-[rgba(67,139,255,0.12)] hover:border-[rgba(83,215,245,0.3)] hover:bg-[#111E35]/70 text-[#A3B4CF]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[11px] font-mono text-[#F1F6FF] font-semibold truncate">
                      ID: {exc.id.slice(0, 8)}
                    </span>
                    <span
                      className={`text-[9px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider border ${
                        exc.status === 'COMPLETED'
                          ? 'bg-[#28C995]/15 text-[#28C995] border-[#28C995]/30'
                          : exc.status === 'RUNNING'
                          ? 'bg-[#438BFF]/15 text-[#438BFF] border-[#438BFF]/30 animate-pulse'
                          : exc.status === 'WAITING_APPROVAL'
                          ? 'bg-[#F2B65D]/15 text-[#F2B65D] border-[#F2B65D]/30'
                          : exc.status === 'CANCELLED'
                          ? 'bg-[#080F20] text-[#7285A5] border-[rgba(67,139,255,0.15)]'
                          : 'bg-[#F16B7A]/15 text-[#F16B7A] border-[#F16B7A]/30'
                      }`}
                    >
                      {exc.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#A3B4CF] truncate">Trigger: {exc.trigger_type}</div>
                  <div className="text-[10px] text-[#7285A5] font-mono mt-1">
                    {new Date(exc.started_at).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Execution Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedExecution ? (
            <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-6">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                  <div className="text-[10px] text-[#7285A5] uppercase tracking-wider font-semibold">Status</div>
                  <div className="text-xs font-bold text-[#F1F6FF] mt-1">{selectedExecution.status}</div>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                  <div className="text-[10px] text-[#7285A5] uppercase tracking-wider font-semibold">Duration</div>
                  <div className="text-xs font-bold text-[#F1F6FF] mt-1">
                    {selectedExecution.duration_ms ? `${selectedExecution.duration_ms} ms` : 'In progress'}
                  </div>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                  <div className="text-[10px] text-[#7285A5] uppercase tracking-wider font-semibold">Trigger</div>
                  <div className="text-xs font-bold text-[#F1F6FF] mt-1">{selectedExecution.trigger_type}</div>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                  <div className="text-[10px] text-[#7285A5] uppercase tracking-wider font-semibold">Nodes / Tasks</div>
                  <div className="text-xs font-bold text-[#F1F6FF] mt-1">
                    {(selectedExecution.nodes?.length || 0) + agentRuns.length}
                  </div>
                </div>
              </div>

              {/* Error Banner */}
              {selectedExecution.error_message && (
                <div className="p-4 rounded-2xl bg-[#F16B7A]/15 border border-[#F16B7A]/35 text-xs text-[#F16B7A] flex items-start gap-2.5 shadow-[0_0_16px_rgba(241,107,122,0.2)]">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">Execution Interrupted / Failed</div>
                    <div className="mt-0.5">{selectedExecution.error_message}</div>
                  </div>
                </div>
              )}

              {/* Agent Execution Tracing Panel */}
              {agentRuns.length > 0 && (
                <div className="p-5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bot className="w-4 h-4 text-[#438BFF]" />
                      <h2 className="text-xs font-bold text-[#F1F6FF] uppercase tracking-wider">
                        Agent Execution Tracing ({agentRuns.length} Persisted Runs)
                      </h2>
                    </div>
                  </div>

                  {/* Agent Tasks Tabs */}
                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    {agentRuns.map((run) => (
                      <button
                        key={run.id}
                        onClick={() => setSelectedAgentRunId(run.id)}
                        className={`p-3 rounded-2xl border text-left shrink-0 transition-all ${
                          activeAgentRun?.id === run.id
                            ? 'bg-[#172743] border-[#438BFF] shadow-[0_0_16px_rgba(67,139,255,0.3)]'
                            : 'bg-[#111E35]/60 border-[rgba(67,139,255,0.12)] hover:border-[rgba(67,139,255,0.25)]'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 mb-1">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              run.status === 'COMPLETED'
                                ? 'bg-[#28C995]'
                                : run.status === 'WAITING_APPROVAL'
                                ? 'bg-[#F2B65D]'
                                : run.status === 'RUNNING'
                                ? 'bg-[#438BFF] animate-pulse'
                                : 'bg-[#F16B7A]'
                            }`}
                          />
                          <span className="text-[10px] font-mono text-[#53D7F5] uppercase">{run.agent_role}</span>
                        </div>
                        <div className="text-xs font-medium text-[#F1F6FF] truncate max-w-[140px]">
                          {run.task_id || 'unassigned'}
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Active Agent Run Details */}
                  {activeAgentRun && (
                    <div className="p-4 rounded-2xl bg-[#111E35]/70 border border-[rgba(67,139,255,0.14)] space-y-4 text-xs">
                      {/* Telemetry Row */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                        <div>
                          <span className="text-[#7285A5]">Agent Role:</span>
                          <div className="font-semibold text-[#F1F6FF]">{activeAgentRun.agent_role}</div>
                        </div>
                        <div>
                          <span className="text-[#7285A5]">Provider & Model:</span>
                          <div className="font-semibold text-[#F1F6FF]">
                            {activeAgentRun.provider || 'gemini'} ({activeAgentRun.model || 'gemini-1.5-pro'})
                          </div>
                        </div>
                        <div>
                          <span className="text-[#7285A5]">Duration & Tokens:</span>
                          <div className="font-semibold text-[#53D7F5] font-mono">
                            {activeAgentRun.latency_ms} ms | {activeAgentRun.token_count} tokens
                          </div>
                        </div>
                        <div>
                          <span className="text-[#7285A5]">Retries & Status:</span>
                          <div className="font-semibold text-[#F1F6FF]">
                            Retries: {activeAgentRun.retry_count || 0} ({activeAgentRun.status})
                          </div>
                        </div>
                      </div>

                      {/* Tool Invocations */}
                      {activeAgentRun.tools_called && activeAgentRun.tools_called.length > 0 && (
                        <div className="space-y-1.5">
                          <div className="text-[11px] font-semibold text-[#A3B4CF] flex items-center gap-1.5">
                            <Wrench className="w-3.5 h-3.5 text-[#438BFF]" />
                            <span>Tool Invocations</span>
                          </div>
                          <div className="space-y-1.5">
                            {activeAgentRun.tools_called.map((tool: any, idx: number) => (
                              <div
                                key={idx}
                                className="p-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] font-mono text-[10px] text-[#A3B4CF]"
                              >
                                {typeof tool === 'string' ? (
                                  <span>{tool}</span>
                                ) : (
                                  <div>
                                    <span className="text-[#53D7F5] font-bold">{tool.name}</span>
                                    {tool.input && <div className="text-[#7285A5] truncate mt-0.5">Input: {JSON.stringify(tool.input)}</div>}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Handoff Data */}
                      {activeAgentRun.handoff_data && Object.keys(activeAgentRun.handoff_data).length > 0 && (
                        <div className="space-y-1.5">
                          <div className="text-[11px] font-semibold text-[#A3B4CF] flex items-center gap-1.5">
                            <ArrowRight className="w-3.5 h-3.5 text-[#28C995]" />
                            <span>Agent Handoff Data</span>
                          </div>
                          <pre className="p-3 rounded-2xl bg-[#0C1629]/80 border border-[rgba(67,139,255,0.14)] font-mono text-[10px] text-[#F1F6FF] overflow-x-auto max-h-36">
                            {JSON.stringify(activeAgentRun.handoff_data, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Task Input & Output */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <div className="text-[11px] font-mono text-[#7285A5] flex items-center gap-1">
                            <Terminal className="w-3.5 h-3.5 text-[#438BFF]" />
                            <span>Task Input</span>
                          </div>
                          <pre className="p-3 rounded-2xl bg-[#0C1629]/80 border border-[rgba(67,139,255,0.14)] font-mono text-[10px] text-[#A3B4CF] overflow-x-auto max-h-48">
                            {JSON.stringify(activeAgentRun.task_input, null, 2)}
                          </pre>
                        </div>
                        <div className="space-y-1">
                          <div className="text-[11px] font-mono text-[#7285A5] flex items-center gap-1">
                            <Database className="w-3.5 h-3.5 text-[#28C995]" />
                            <span>Task Output</span>
                          </div>
                          <pre className="p-3 rounded-2xl bg-[#0C1629]/80 border border-[rgba(67,139,255,0.14)] font-mono text-[10px] text-[#28C995] overflow-x-auto max-h-48">
                            {JSON.stringify(activeAgentRun.task_output, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Node Sequence Horizontal Timeline */}
              {selectedExecution.nodes && selectedExecution.nodes.length > 0 && (
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider">
                    Workflow Node Flow
                  </div>

                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    {selectedExecution.nodes.map((node) => (
                      <button
                        key={node.id}
                        onClick={() => setSelectedNodeId(node.node_id)}
                        className={`p-3 rounded-2xl border text-left shrink-0 transition-all ${
                          activeNode?.node_id === node.node_id
                            ? 'bg-[#172743] border-[#438BFF] shadow-[0_0_16px_rgba(67,139,255,0.3)]'
                            : 'bg-[#0C1629]/60 border-[rgba(67,139,255,0.12)] hover:border-[rgba(67,139,255,0.25)]'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 mb-1">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              node.status === 'SUCCEEDED'
                                ? 'bg-[#28C995]'
                                : node.status === 'RUNNING'
                                ? 'bg-[#438BFF] animate-ping'
                                : 'bg-[#F2B65D]'
                            }`}
                          />
                          <span className="text-[10px] font-mono text-[#53D7F5] uppercase">{node.status}</span>
                        </div>
                        <div className="text-xs font-medium text-[#F1F6FF] truncate max-w-[120px]">{node.node_type}</div>
                      </button>
                    ))}
                  </div>

                  {/* Active Node Inspector */}
                  {activeNode && (
                    <div className="space-y-4 pt-4 border-t border-[rgba(67,139,255,0.15)]">
                      <div className="flex items-center justify-between text-xs">
                        <div className="font-semibold text-[#F1F6FF]">
                          Node: <span className="font-mono text-[#438BFF]">{activeNode.node_id}</span> ({activeNode.node_type})
                        </div>
                        <span className="text-[11px] text-[#7285A5] font-mono">Retries: {activeNode.retry_count}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                          <div className="text-[11px] font-mono text-[#7285A5] flex items-center gap-1">
                            <Terminal className="w-3.5 h-3.5 text-[#438BFF]" />
                            <span>Resolved Inputs</span>
                          </div>
                          <pre className="p-3.5 rounded-2xl bg-[#0C1629]/80 border border-[rgba(67,139,255,0.14)] text-[11px] font-mono text-[#A3B4CF] overflow-x-auto max-h-56">
                            {JSON.stringify(activeNode.inputs, null, 2)}
                          </pre>
                        </div>

                        <div className="space-y-1.5">
                          <div className="text-[11px] font-mono text-[#7285A5] flex items-center gap-1">
                            <Database className="w-3.5 h-3.5 text-[#28C995]" />
                            <span>Committed Outputs</span>
                          </div>
                          <pre className="p-3.5 rounded-2xl bg-[#0C1629]/80 border border-[rgba(67,139,255,0.14)] text-[11px] font-mono text-[#28C995] overflow-x-auto max-h-56">
                            {JSON.stringify(activeNode.outputs, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Event Timeline */}
              <div className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-2">
                <div className="flex items-center gap-2 text-[11px] font-semibold text-[#A3B4CF] uppercase tracking-wider mb-2">
                  <Radio className="w-3.5 h-3.5 text-[#438BFF]" /> Event Timeline
                </div>
                {eventsLoading ? (
                  <div className="text-xs text-[#7285A5] animate-pulse">Loading event timeline...</div>
                ) : eventsError ? (
                  <div className="text-xs text-[#F16B7A]">{eventsError}</div>
                ) : events.length === 0 ? (
                  <div className="text-xs text-[#7285A5]">No events recorded for this execution.</div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {events.map((event) => (
                      <div key={event.id} className="flex items-start gap-2 text-xs">
                        <span className="text-[#7285A5] font-mono shrink-0">{new Date(event.created_at).toLocaleTimeString()}</span>
                        <span className="text-[#F1F6FF] font-medium">{event.event_type}</span>
                        <span className="text-[#7285A5] truncate">{JSON.stringify(event.payload)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-xs text-[#7285A5]">
              Select an execution to inspect timeline, step latency, and agent traces.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
