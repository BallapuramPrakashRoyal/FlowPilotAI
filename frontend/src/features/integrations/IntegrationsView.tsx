'use client';

import React, { useEffect, useState } from 'react';
import {
  Mail,
  GitBranch,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Shield,
  RefreshCw,
  Key,
  Lock,
  Sliders,
  Info,
  Check,
} from 'lucide-react';
import { api } from '@/services/api';
import { Integration, IntegrationConfig } from '@/types';

export function IntegrationsView() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [integrationConfig, setIntegrationConfig] = useState<IntegrationConfig | null>(null);
  const [gmailPreview, setGmailPreview] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchIntegrations = async () => {
    try {
      setErrorMsg(null);
      const [data, configData] = await Promise.all([
        api.listIntegrations(),
        api.getIntegrationConfig().catch(() => null),
      ]);
      setIntegrations(data);
      if (configData) setIntegrationConfig(configData);

      const gmail = data.find((i) => i.provider === 'GMAIL');
      if (gmail?.is_connected) {
        try {
          const preview = await api.getGmailPreview();
          setGmailPreview(preview);
        } catch {
          setGmailPreview(null);
        }
      } else {
        setGmailPreview(null);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load integrations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('connected') === 'gmail') {
        setSuccessMsg('Gmail connected successfully via Google OAuth 2.0.');
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
  }, []);

  const handleConnectGmail = () => {
    if (!integrationConfig?.google_oauth_configured) {
      setErrorMsg(
        'Google OAuth 2.0 credentials are not configured in backend/.env. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.',
      );
      return;
    }
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${apiBase}/api/v1/integrations/gmail/authorize`;
  };

  const handleDisconnect = async (id: string) => {
    if (!confirm('Are you sure you want to disconnect this integration and revoke OAuth credentials?')) return;
    try {
      setActionLoading(true);
      setErrorMsg(null);
      await api.disconnectIntegration(id);
      setSuccessMsg('Integration disconnected successfully and credentials revoked.');
      await fetchIntegrations();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to disconnect integration.');
    } finally {
      setActionLoading(false);
    }
  };

  const gmailIntegration = integrations.find((i) => i.provider === 'GMAIL');

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] mb-2 shadow-[0_0_12px_rgba(40,123,250,0.2)]">
            <Shield className="w-3.5 h-3.5" />
            <span>OAuth 2.0 & AES-256 Symmetric Encryption</span>
          </div>
          <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Integration Hub</h1>
          <p className="text-sm text-[#A3B4CF]">
            Manage external workspace connections, OAuth permissions, security scopes, and integration policies.
          </p>
        </div>
        <button
          onClick={fetchIntegrations}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.35)] text-xs text-[#A3B4CF] hover:text-[#F1F6FF] transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-2xl bg-[#0C2422]/85 border border-[#28C995]/40 text-xs text-[#28C995] flex items-center justify-between backdrop-blur-xl shadow-lg shadow-[#28C995]/10">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-[#A3B4CF] hover:text-white">✕</button>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-[#24121B]/85 border border-[#F16B7A]/40 text-xs text-[#F16B7A] flex items-center justify-between backdrop-blur-xl shadow-lg shadow-[#F16B7A]/10">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-[#A3B4CF] hover:text-white">✕</button>
        </div>
      )}

      {/* OAuth Configuration Status Banner */}
      {integrationConfig && !integrationConfig.google_oauth_configured && (
        <div className="p-5 rounded-3xl bg-[#172743]/70 border border-[#F2B65D]/35 space-y-2 backdrop-blur-xl shadow-xl">
          <div className="flex items-center gap-2 text-xs font-bold text-[#F2B65D]">
            <Key className="w-4 h-4" />
            <span>Google OAuth 2.0 Credentials Required for Live Gmail Access</span>
          </div>
          <p className="text-xs text-[#A3B4CF] leading-relaxed">
            Live Gmail operations require Google OAuth credentials. Set <code className="text-[#F2B65D] font-mono px-1 py-0.5 rounded bg-black/40">GOOGLE_CLIENT_ID</code> and <code className="text-[#F2B65D] font-mono px-1 py-0.5 rounded bg-black/40">GOOGLE_CLIENT_SECRET</code> in your backend environment file. See <a href="/docs/GMAIL_SETUP.md" target="_blank" className="underline text-[#53D7F5] font-medium">docs/GMAIL_SETUP.md</a> for setup instructions.
          </p>
        </div>
      )}

      {/* Integration Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Gmail Card (Active) */}
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.2)] hover:border-[rgba(83,215,245,0.4)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] flex flex-col justify-between space-y-6 transition-all">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-[#F16B7A]/15 border border-[#F16B7A]/30 flex items-center justify-center text-[#F16B7A] shadow-[0_0_16px_rgba(241,107,122,0.2)]">
                <Mail className="w-6 h-6" />
              </div>
              <span
                className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${
                  gmailIntegration?.is_connected
                    ? 'bg-[#28C995]/15 text-[#28C995] border-[#28C995]/30'
                    : 'bg-[#080F20] text-[#7285A5] border-[rgba(67,139,255,0.15)]'
                }`}
              >
                {gmailIntegration?.is_connected ? 'Connected' : 'Not Connected'}
              </span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#F1F6FF]">Google Gmail</h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#287BFA]/15 text-[#53D7F5] border border-[#287BFA]/30 font-mono">Available</span>
              </div>
              <p className="text-xs text-[#A3B4CF] mt-1 leading-relaxed">
                Retrieve unread emails, classify threads, extract actionable insights, create drafts, and send approved responses.
              </p>
            </div>

            {gmailIntegration?.is_connected ? (
              <div className="p-3 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] text-xs text-[#F1F6FF] font-mono space-y-2">
                <div className="flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5 text-[#28C995]" />
                  <span className="truncate">{gmailIntegration.account_email || 'Authenticated User'}</span>
                </div>
                <div className="text-[10px] text-[#28C995] flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Token Encrypted at Rest (AES-256)
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] text-xs text-[#A3B4CF] space-y-1">
                <div className="flex items-center gap-1.5 text-[#F1F6FF]">
                  <Info className="w-3.5 h-3.5 text-[#438BFF]" />
                  <span>Real Connection Required</span>
                </div>
                <p className="text-[11px] text-[#7285A5]">
                  Connect your Google account to authorize AI agent email triage and human-in-the-loop email dispatch.
                </p>
              </div>
            )}

            {/* Permission Scopes */}
            <div className="space-y-1.5 pt-2 border-t border-[rgba(67,139,255,0.12)]">
              <div className="text-[11px] font-semibold text-[#A3B4CF]">Minimum Necessary OAuth Scopes:</div>
              <ul className="text-[10px] font-mono text-[#7285A5] space-y-1">
                <li className="flex items-center gap-1 text-[#A3B4CF]">
                  <span className="text-[#438BFF]">•</span> gmail.readonly (Read message metadata)
                </li>
                <li className="flex items-center gap-1 text-[#A3B4CF]">
                  <span className="text-[#438BFF]">•</span> gmail.compose (Create draft replies)
                </li>
                <li className="flex items-center gap-1 text-[#A3B4CF]">
                  <span className="text-[#438BFF]">•</span> gmail.send (Send approved emails only)
                </li>
                <li className="flex items-center gap-1 text-[#A3B4CF]">
                  <span className="text-[#438BFF]">•</span> userinfo.email (Identify workspace account)
                </li>
              </ul>
            </div>
          </div>

          <div>
            {gmailIntegration?.is_connected ? (
              <button
                onClick={() => handleDisconnect(gmailIntegration.id)}
                disabled={actionLoading}
                className="w-full py-2.5 rounded-xl bg-[#F16B7A]/15 hover:bg-[#F16B7A]/25 text-[#F16B7A] text-xs font-semibold border border-[#F16B7A]/35 transition-all shadow-md shadow-[#F16B7A]/15 disabled:opacity-50"
              >
                Disconnect & Revoke Credentials
              </button>
            ) : (
              <button
                onClick={handleConnectGmail}
                disabled={actionLoading}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/30 border border-white/20 transition-all flex items-center justify-center gap-2 hover:-translate-y-0.5 active:translate-y-0"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Connect with Google OAuth</span>
              </button>
            )}
          </div>
        </div>

        {/* GitHub Card (Planned) */}
        <div className="p-6 rounded-3xl bg-[#111E35]/40 backdrop-blur-xl border border-[rgba(67,139,255,0.1)] flex flex-col justify-between space-y-6 opacity-75">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-[#172743] border border-[rgba(67,139,255,0.15)] flex items-center justify-center text-[#A3B4CF]">
                <GitBranch className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-[#0C1629] text-[#7285A5] border border-[rgba(67,139,255,0.12)]">
                Planned
              </span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#F1F6FF]">GitHub</h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0C1629] text-[#7285A5] border border-[rgba(67,139,255,0.12)] font-mono">Coming Soon</span>
              </div>
              <p className="text-xs text-[#7285A5] mt-1 leading-relaxed">
                Subscribe to repository issues, pull requests, automated code reviews, and release notes triage.
              </p>
            </div>

            <div className="p-3 rounded-2xl bg-[#0C1629]/50 border border-[rgba(67,139,255,0.1)] text-xs text-[#7285A5] space-y-1">
              <div className="text-[11px] font-semibold text-[#A3B4CF]">Planned Scopes:</div>
              <div className="text-[10px] font-mono text-[#7285A5]">repo:status, read:org, write:discussion</div>
            </div>
          </div>

          <button
            disabled
            className="w-full py-2.5 rounded-xl bg-[#0C1629]/70 text-[#7285A5] text-xs font-semibold cursor-not-allowed border border-[rgba(67,139,255,0.1)]"
          >
            Planned Integration
          </button>
        </div>

        {/* Slack Card (Planned) */}
        <div className="p-6 rounded-3xl bg-[#111E35]/40 backdrop-blur-xl border border-[rgba(67,139,255,0.1)] flex flex-col justify-between space-y-6 opacity-75">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-[#172743] border border-[rgba(67,139,255,0.15)] flex items-center justify-center text-[#53D7F5]">
                <MessageSquare className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-[#0C1629] text-[#7285A5] border border-[rgba(67,139,255,0.12)]">
                Planned
              </span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#F1F6FF]">Slack Workspace</h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0C1629] text-[#7285A5] border border-[rgba(67,139,255,0.12)] font-mono">Coming Soon</span>
              </div>
              <p className="text-xs text-[#7285A5] mt-1 leading-relaxed">
                Dispatch interactive human approval cards to Slack channels and handle decisions directly in-channel.
              </p>
            </div>

            <div className="p-3 rounded-2xl bg-[#0C1629]/50 border border-[rgba(67,139,255,0.1)] text-xs text-[#7285A5] space-y-1">
              <div className="text-[11px] font-semibold text-[#A3B4CF]">Planned Scopes:</div>
              <div className="text-[10px] font-mono text-[#7285A5]">chat:write, incoming-webhook, commands</div>
            </div>
          </div>

          <button
            disabled
            className="w-full py-2.5 rounded-xl bg-[#0C1629]/70 text-[#7285A5] text-xs font-semibold cursor-not-allowed border border-[rgba(67,139,255,0.1)]"
          >
            Planned Integration
          </button>
        </div>
      </div>

      {/* Workspace Integration Settings */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-[#438BFF]" />
          <h2 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Workspace Integration Policies</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-2">
            <div className="font-semibold text-[#F1F6FF]">Human Approval Enforcement</div>
            <p className="text-[#A3B4CF] text-[11px] leading-relaxed">
              Every email dispatch operation requires explicit approval in the Approval Center before sending. Agents cannot bypass approval.
            </p>
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#28C995]">
              <Check className="w-3 h-3" /> Enforced by Server Code
            </span>
          </div>
          <div className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-2">
            <div className="font-semibold text-[#F1F6FF]">Prompt Injection Defense</div>
            <p className="text-[#A3B4CF] text-[11px] leading-relaxed">
              Untrusted external email content is fenced inside isolated boundary tags. Email bodies are never treated as trusted system instructions.
            </p>
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#28C995]">
              <Check className="w-3 h-3" /> Active Fencing & Delimiters
            </span>
          </div>
          <div className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-2">
            <div className="font-semibold text-[#F1F6FF]">Token Encryption at Rest</div>
            <p className="text-[#A3B4CF] text-[11px] leading-relaxed">
              OAuth refresh and access tokens are encrypted using symmetric Fernet AES-256 keys and are never sent to frontend clients.
            </p>
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#28C995]">
              <Check className="w-3 h-3" /> AES-256 Enabled
            </span>
          </div>
        </div>
      </div>

      {/* Live Gmail Inbox Inspection Preview */}
      {gmailIntegration?.is_connected ? (
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Gmail Live Inbox Stream</h3>
              <p className="text-xs text-[#7285A5]">
                {gmailPreview?.unread_count || 0} unread messages ready for autonomous triaging
              </p>
            </div>
            <button
              onClick={fetchIntegrations}
              className="text-xs text-[#53D7F5] hover:underline inline-flex items-center gap-1 font-medium"
            >
              <RefreshCw className="w-3 h-3" /> Refresh Messages
            </button>
          </div>

          {gmailPreview?.sample_threads && gmailPreview.sample_threads.length > 0 ? (
            <div className="space-y-3">
              {gmailPreview.sample_threads.map((msg: any) => (
                <div
                  key={msg.id}
                  className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] flex items-start justify-between gap-4"
                >
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#F1F6FF]">{msg.subject}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#F16B7A]/20 text-[#F16B7A] border border-[#F16B7A]/30">
                        UNREAD
                      </span>
                    </div>
                    <div className="text-[11px] text-[#438BFF] font-mono">From: {msg.sender}</div>
                    <p className="text-xs text-[#A3B4CF] line-clamp-2">{msg.snippet || msg.body}</p>
                  </div>
                  <div className="text-[10px] text-[#7285A5] font-mono shrink-0">
                    {msg.received_at ? new Date(msg.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-[#7285A5] rounded-2xl bg-[#0C1629]/50 border border-[rgba(67,139,255,0.1)]">
              No unread emails currently found in connected Gmail inbox.
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Gmail Live Inbox Stream</h3>
            <p className="text-xs text-[#7285A5]">
              Connect your Gmail account above to view live unread messages and enable autonomous triaging.
            </p>
          </div>
          <button
            onClick={handleConnectGmail}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/30 border border-white/20 transition-all"
          >
            Connect Gmail
          </button>
        </div>
      )}
    </div>
  );
}
