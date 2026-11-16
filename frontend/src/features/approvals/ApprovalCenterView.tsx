'use client';

import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Mail,
  Send,
  Edit3,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { api } from '@/services/api';
import { Approval } from '@/types';

export function ApprovalCenterView() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [editingDraft, setEditingDraft] = useState<any | null>(null);
  const [notes, setNotes] = useState('');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.listApprovals('PENDING');
      setApprovals(data);
      if (data.length > 0 && !selectedApproval) {
        setSelectedApproval(data[0]);
        setEditingDraft(data[0].proposal_data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedApproval) return;
    try {
      await api.decideApproval(selectedApproval.id, decision, notes, editingDraft);
      setActionSuccess(
        decision === 'APPROVED'
          ? 'Action authorized! Workflow resumed and email dispatched.'
          : 'Execution rejected and cancelled.'
      );
      fetchApprovals();
      setSelectedApproval(null);
    } catch (e: any) {
      alert(`Decision error: ${e.message}`);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F2B65D]/15 border border-[#F2B65D]/35 text-xs font-semibold text-[#F2B65D] mb-2 shadow-[0_0_12px_rgba(242,182,93,0.2)]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Human-in-the-Loop Governance</span>
          </div>
          <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Approval Center</h1>
          <p className="text-sm text-[#A3B4CF]">
            Review, edit, or reject AI-generated actions before external side effects are committed.
          </p>
        </div>

        <button
          onClick={fetchApprovals}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.35)] text-xs text-[#A3B4CF] hover:text-[#F1F6FF] font-medium transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="p-4 rounded-2xl bg-[#0C2422]/85 border border-[#28C995]/40 text-xs text-[#28C995] flex items-center gap-2 backdrop-blur-xl shadow-lg">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Main Split: Left List + Right Review Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pending List */}
        <div className="p-5 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider">
              Pending Approvals ({approvals.length})
            </span>
          </div>

          {approvals.length === 0 ? (
            <div className="text-center py-16 text-xs text-[#7285A5] space-y-2">
              <CheckCircle2 className="w-8 h-8 text-[#28C995] mx-auto opacity-70" />
              <p>All caught up! No actions currently require human review.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {approvals.map((appr) => (
                <button
                  key={appr.id}
                  onClick={() => {
                    setSelectedApproval(appr);
                    setEditingDraft(appr.proposal_data);
                  }}
                  className={`w-full p-4 rounded-2xl text-left border transition-all ${
                    selectedApproval?.id === appr.id
                      ? 'bg-[#172743]/90 border-[#438BFF] shadow-[0_0_20px_rgba(67,139,255,0.25),inset_0_1px_0_rgba(255,255,255,0.15)] text-[#F1F6FF]'
                      : 'bg-[#0C1629]/60 border-[rgba(67,139,255,0.12)] hover:border-[rgba(83,215,245,0.3)] hover:bg-[#111E35]/70 text-[#A3B4CF]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#F2B65D]/15 text-[#F2B65D] border border-[#F2B65D]/30 uppercase font-semibold">
                      {appr.action_type}
                    </span>
                    <span className="text-[11px] text-[#7285A5] font-mono">
                      {new Date(appr.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-[#F1F6FF] truncate">{appr.title}</div>
                  <div className="text-[11px] text-[#A3B4CF] truncate mt-1">
                    To: {appr.proposal_data?.recipient || 'Client'}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detailed Review & Edit Panel */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] flex flex-col justify-between space-y-6">
          {selectedApproval ? (
            <div className="space-y-5">
              <div className="border-b border-[rgba(67,139,255,0.15)] pb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-[#53D7F5]">Execution ID: {selectedApproval.execution_id.slice(0, 8)}</span>
                </div>
                <h2 className="text-lg font-bold text-[#F1F6FF] tracking-tight">{selectedApproval.title}</h2>
              </div>

              {/* Proposal Payload Editor */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-[#F16B7A]" />
                    <span>AI-Generated Email Proposal</span>
                  </span>
                  <span className="text-[11px] text-[#7285A5]">Editable before approval</span>
                </div>

                <div className="space-y-2.5 bg-[#0C1629]/70 p-4 rounded-2xl border border-[rgba(67,139,255,0.14)]">
                  <div>
                    <label className="text-[11px] text-[#A3B4CF] block mb-1">Recipient</label>
                    <input
                      type="text"
                      value={editingDraft?.recipient || ''}
                      onChange={(e) => setEditingDraft({ ...editingDraft, recipient: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-[#111E35] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)]"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-[#A3B4CF] block mb-1">Subject</label>
                    <input
                      type="text"
                      value={editingDraft?.subject || ''}
                      onChange={(e) => setEditingDraft({ ...editingDraft, subject: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-[#111E35] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)]"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-[#A3B4CF] block mb-1">Message Body</label>
                    <textarea
                      rows={6}
                      value={editingDraft?.body || ''}
                      onChange={(e) => setEditingDraft({ ...editingDraft, body: e.target.value })}
                      className="w-full p-3 rounded-xl bg-[#111E35] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] resize-none font-sans"
                    />
                  </div>
                </div>
              </div>

              {/* Decision Notes */}
              <div>
                <label className="text-[11px] text-[#A3B4CF] block mb-1">Reviewer Notes (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Approved with revised deadline"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] placeholder-[#7285A5] focus:outline-none focus:border-[#438BFF]"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-[rgba(67,139,255,0.12)] flex items-center justify-end gap-3">
                <button
                  onClick={() => handleDecision('REJECTED')}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#F16B7A]/15 hover:bg-[#F16B7A]/25 text-[#F16B7A] border border-[#F16B7A]/35 text-xs font-semibold shadow-md shadow-[#F16B7A]/15 transition-all"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject & Cancel</span>
                </button>

                <button
                  onClick={() => handleDecision('APPROVED')}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-gradient-to-r from-[#28C995] to-[#20A27A] hover:from-[#2ED8A0] hover:to-[#24B88A] text-white text-xs font-semibold shadow-lg shadow-[#28C995]/25 border border-white/20 transition-all active:scale-95"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Dispatch</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-24 text-xs text-[#7285A5]">
              Select a pending approval from the list to inspect context, modify email drafts, and record decision.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
