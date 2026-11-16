'use client';

import React, { useEffect, useState } from 'react';
import {
  Shield,
  Key,
  Users,
  Building,
  CheckCircle2,
  Lock,
  Cpu,
  Save,
} from 'lucide-react';
import { api } from '@/services/api';
import { AIConfig, AIProvider } from '@/types';

export function SettingsView() {
  const [apiKey, setApiKey] = useState('');
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [provider, setProvider] = useState('');
  const [model, setModel] = useState('');
  const [requestLimit, setRequestLimit] = useState('');
  const [dailyTokenLimit, setDailyTokenLimit] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);

  useEffect(() => {
    Promise.all([api.getAIConfig(), api.listAIProviders()])
      .then(([aiConfig, aiProviders]) => {
        setConfig(aiConfig);
        setProviders(aiProviders);
        setProvider(aiConfig.default_provider);
        setModel(aiConfig.default_model);
        setRequestLimit(String(aiConfig.request_limit));
        setDailyTokenLimit(String(aiConfig.daily_token_limit));
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Unable to load AI settings.'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateAIConfig({
        default_provider: provider,
        default_model: model,
        ...(apiKey ? { api_key: apiKey } : {}),
        request_limit: Number(requestLimit),
        daily_token_limit: Number(dailyTokenLimit),
        sensitive_fields: config.sensitive_fields,
      });
      setConfig(updated);
      setApiKey('');
      setSavedNotice(true);
      setTimeout(() => setSavedNotice(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to save AI settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Settings & Security</h1>
        <p className="text-sm text-[#A3B4CF]">
          Configure workspace access, AI provider keys, encrypted credential storage, and RBAC governance.
        </p>
      </div>

      {savedNotice && (
        <div className="p-4 rounded-2xl bg-[#0C2422]/85 border border-[#28C995]/40 text-xs text-[#28C995] flex items-center gap-2 backdrop-blur-xl shadow-lg">
          <CheckCircle2 className="w-4 h-4" />
          <span>Settings saved securely!</span>
        </div>
      )}
      {error && <div className="p-4 rounded-2xl bg-[#24121B]/85 border border-[#F16B7A]/40 text-xs text-[#F16B7A] backdrop-blur-xl">{error}</div>}

      {/* Workspace Settings */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#F1F6FF] border-b border-[rgba(67,139,255,0.15)] pb-3">
          <Building className="w-4 h-4 text-[#438BFF]" />
          <span>Workspace Profile</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-[#A3B4CF] block mb-1.5 font-medium">Workspace Name</label>
            <input
              type="text"
              defaultValue="Acme Autonomous Ops"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] transition-all"
            />
          </div>
          <div>
            <label className="text-xs text-[#A3B4CF] block mb-1.5 font-medium">Slug Identifier</label>
            <input
              type="text"
              disabled
              defaultValue="acme-ops"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/50 border border-[rgba(67,139,255,0.1)] text-xs text-[#7285A5] font-mono cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {/* AI Provider Configuration */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#F1F6FF] border-b border-[rgba(67,139,255,0.15)] pb-3">
          <Cpu className="w-4 h-4 text-[#53D7F5]" />
          <span>AI Engine Configuration</span>
        </div>

        {loading ? (
          <div className="text-xs text-[#7285A5] animate-pulse">Loading AI configuration...</div>
        ) : !config ? (
          <div className="text-xs text-[#7285A5]">AI configuration is unavailable.</div>
        ) : <div className="space-y-4">
          <div>
            <label className="text-xs text-[#A3B4CF] block mb-1.5 font-medium">Google Gemini API Key</label>
            <div className="relative">
              <Key className="w-4 h-4 text-[#7285A5] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] font-mono transition-all"
              />
            </div>
            <p className="text-[11px] text-[#7285A5] mt-1">Leave blank to keep the existing encrypted key.</p>
          </div>

          <div>
            <label className="text-xs text-[#A3B4CF] block mb-1.5 font-medium">Default Provider</label>
            <select
              value={provider}
              onChange={(e) => {
                const next = providers.find((item) => item.id === e.target.value);
                setProvider(e.target.value);
                if (next?.models[0]) setModel(next.models[0]);
              }}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] font-mono transition-all"
            >
              {providers.map((item) => <option key={item.id} value={item.id} className="bg-[#0C1629] text-[#F1F6FF]">{item.id}{item.configured ? '' : ' (not configured)'}</option>)}
            </select>
          </div>

          <div>
            <label className="text-xs text-[#A3B4CF] block mb-1.5 font-medium">Default Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] font-mono transition-all"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="text-xs text-[#A3B4CF] font-medium">Request Limit
              <input type="number" min="1" value={requestLimit} onChange={(e) => setRequestLimit(e.target.value)} className="mt-1.5 w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] font-mono" />
            </label>
            <label className="text-xs text-[#A3B4CF] font-medium">Daily Token Limit
              <input type="number" min="1" value={dailyTokenLimit} onChange={(e) => setDailyTokenLimit(e.target.value)} className="mt-1.5 w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] font-mono" />
            </label>
          </div>
        </div>}
      </div>

      {/* Security & Cryptography Info */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#F1F6FF] border-b border-[rgba(67,139,255,0.15)] pb-3">
          <Lock className="w-4 h-4 text-[#28C995]" />
          <span>Security & Protection Active</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-1">
            <div className="font-semibold text-[#F1F6FF]">Password Hashing</div>
            <div className="text-[#28C995] font-mono text-[11px]">Argon2id (RFC 9106)</div>
          </div>
          <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-1">
            <div className="font-semibold text-[#F1F6FF]">OAuth Secrets</div>
            <div className="text-[#28C995] font-mono text-[11px]">Fernet AES Symmetric</div>
          </div>
          <div className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-1">
            <div className="font-semibold text-[#F1F6FF]">RBAC Isolation</div>
            <div className="text-[#28C995] font-mono text-[11px]">Tenant-Scoped Session</div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving || loading || !config}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/25 border border-white/20 transition-all active:scale-95 disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>
    </div>
  );
}
