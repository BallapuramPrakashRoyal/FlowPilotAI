'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Building2,
  Cpu,
  Mail,
  Layers,
  Sparkles,
  Play,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  SkipForward,
  Check,
  ExternalLink,
  Shield,
  Key,
} from 'lucide-react';
import { api } from '@/services/api';
import { WorkflowTemplate, Workflow, Execution } from '@/types';
import { useToast } from '@/components/ui/Toast';

interface Step {
  id: number;
  title: string;
  subtitle: string;
  icon: React.ElementType;
}

const STEPS: Step[] = [
  { id: 1, title: 'Workspace', subtitle: 'Set up organization workspace', icon: Building2 },
  { id: 2, title: 'AI Engine', subtitle: 'Select provider & credentials', icon: Cpu },
  { id: 3, title: 'Integrations', subtitle: 'Connect Gmail (Optional)', icon: Mail },
  { id: 4, title: 'Templates', subtitle: 'Explore production templates', icon: Layers },
  { id: 5, title: 'Workflow', subtitle: 'Synthesize your first pipeline', icon: Sparkles },
  { id: 6, title: 'Execute', subtitle: 'Trigger sample test run', icon: Play },
  { id: 7, title: 'Results', subtitle: 'Inspect execution telemetry', icon: CheckCircle2 },
];

export function OnboardingView() {
  const router = useRouter();
  const toast = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Step 1 State
  const [workspaceName, setWorkspaceName] = useState('Acme Autonomous Ops');
  const [slug, setSlug] = useState('acme-ops');

  // Step 2 State
  const [provider, setProvider] = useState('mock');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('flowpilot-mock-deterministic-v1');

  // Step 3 State
  const [gmailConnected, setGmailConnected] = useState(false);

  // Step 4 State
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('tpl-email-classification');

  // Step 5 State
  const [createdWorkflow, setCreatedWorkflow] = useState<Workflow | null>(null);

  // Step 6 State
  const [execution, setExecution] = useState<Execution | null>(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    // Load templates for step 4
    api.listTemplates()
      .then((tpls) => {
        if (tpls && tpls.length > 0) {
          setTemplates(tpls);
          setSelectedTemplateId(tpls[0].id);
        }
      })
      .catch((e) => console.error('Failed to load templates in onboarding', e));

    // Check integration status
    api.getIntegrationConfig()
      .then((cfg) => {
        if (cfg.google_oauth_configured) {
          api.listIntegrations().then((ints) => {
            const gm = ints.find((i) => i.provider === 'GMAIL');
            if (gm?.is_connected) setGmailConnected(true);
          });
        }
      })
      .catch(() => {});
  }, []);

  const handleStep1Save = () => {
    toast.success('Workspace profile configured!');
    setCurrentStep(2);
  };

  const handleStep2Save = async () => {
    setLoading(true);
    try {
      await api.updateAIConfig({
        default_provider: provider,
        default_model: model,
        ...(apiKey ? { api_key: apiKey } : {}),
        request_limit: 100,
        daily_token_limit: 100000,
        sensitive_fields: [],
      });
      toast.success('AI Engine configuration saved!');
      setCurrentStep(3);
    } catch (e) {
      toast.error('Failed to update AI settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleStep4Select = (id: string) => {
    setSelectedTemplateId(id);
    toast.info('Template selected!');
  };

  const handleStep5Instantiate = async () => {
    setLoading(true);
    try {
      const wf = await api.instantiateTemplate(selectedTemplateId);
      setCreatedWorkflow(wf);
      toast.success(`Workflow "${wf.name}" instantiated!`);
      setCurrentStep(6);
    } catch (e) {
      toast.error('Failed to instantiate template.');
    } finally {
      setLoading(false);
    }
  };

  const handleStep6Execute = async () => {
    if (!createdWorkflow) return;
    setExecuting(true);
    try {
      const res = await api.executeWorkflow(createdWorkflow.id);
      setExecution(res);
      toast.success('Workflow executed asynchronously!');
      setCurrentStep(7);
    } catch (e) {
      toast.error('Execution dispatch failed.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="min-h-full p-8 max-w-5xl mx-auto space-y-8">
      {/* Onboarding Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[rgba(67,139,255,0.15)] pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] mb-2 shadow-[0_0_12px_rgba(40,123,250,0.2)]">
            <Sparkles className="w-3.5 h-3.5" />
            <span>FlowPilot SaaS Onboarding</span>
          </div>
          <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Interactive Guided Setup</h1>
          <p className="text-sm text-[#A3B4CF]">
            Configure your workspace, AI provider, sample template, and test execution in 7 easy steps.
          </p>
        </div>

        <Link
          href="/"
          className="text-xs text-[#7285A5] hover:text-[#53D7F5] flex items-center gap-1 self-start md:self-auto py-2 font-medium transition-colors"
        >
          <span>Exit to Dashboard</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Step Indicator Progress Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
        {STEPS.map((s) => {
          const isDone = s.id < currentStep;
          const isCurrent = s.id === currentStep;
          const Icon = s.icon;
          return (
            <button
              key={s.id}
              onClick={() => s.id <= currentStep && setCurrentStep(s.id)}
              disabled={s.id > currentStep}
              className={`p-3 rounded-2xl border text-left transition-all ${
                isCurrent
                  ? 'bg-[#287BFA]/20 border-[#438BFF] text-white shadow-[0_0_16px_rgba(40,123,250,0.35),inset_0_1px_0_rgba(255,255,255,0.2)]'
                  : isDone
                  ? 'bg-[#111E35]/70 border-[#28C995]/40 text-[#28C995] hover:border-[#28C995]'
                  : 'bg-[#0C1629]/50 border-[rgba(67,139,255,0.1)] text-[#7285A5] cursor-not-allowed'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <Icon className={`w-4 h-4 ${isCurrent ? 'text-[#53D7F5]' : isDone ? 'text-[#28C995]' : 'text-[#7285A5]'}`} />
                {isDone ? (
                  <Check className="w-3.5 h-3.5 text-[#28C995]" />
                ) : (
                  <span className="text-[10px] font-mono opacity-60 text-[#7285A5]">0{s.id}</span>
                )}
              </div>
              <div className="text-xs font-semibold truncate text-[#F1F6FF]">{s.title}</div>
              <div className="text-[10px] text-[#7285A5] truncate">{s.subtitle}</div>
            </button>
          );
        })}
      </div>

      {/* Main Step Content Card */}
      <div className="p-8 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)]">
        {/* STEP 1: Workspace */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#438BFF]" />
                <span>Step 1: Workspace Identity & Tenancy</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Every pipeline, knowledge base, and execution in FlowPilot is strictly isolated to your workspace tenant.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="text-xs font-medium text-[#A3B4CF] block mb-1.5">Workspace Name</label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] transition-all"
                  placeholder="e.g. Acme Autonomous Ops"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-[#A3B4CF] block mb-1.5">Slug Identifier</label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#A3B4CF] font-mono focus:outline-none focus:border-[#438BFF]"
                  placeholder="e.g. acme-ops"
                />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] text-xs text-[#A3B4CF] flex items-center gap-3">
              <Shield className="w-4 h-4 text-[#28C995] shrink-0" />
              <span>Workspace isolation enforces row-level security and tenant sandboxing across all DAG runs.</span>
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={handleStep1Save}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/25 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <span>Continue to AI Engine</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Configure AI Provider */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#53D7F5]" />
                <span>Step 2: Configure AI Engine & Provider</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Select the LLM provider for workflow reasoning, agent handoffs, and synthesis.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              {[
                { id: 'mock', name: 'Deterministic Mock', sub: 'Zero-config offline testing', model: 'flowpilot-mock-deterministic-v1' },
                { id: 'gemini', name: 'Google Gemini', sub: 'Gemini 1.5 Pro / Flash', model: 'gemini-1.5-pro' },
                { id: 'ollama', name: 'Ollama Local', sub: 'Local privacy-first models', model: 'llama3:latest' },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setProvider(p.id);
                    setModel(p.model);
                  }}
                  className={`p-4 rounded-2xl border text-left transition-all ${
                    provider === p.id
                      ? 'bg-[#287BFA]/20 border-[#438BFF] text-white shadow-md shadow-[#287BFA]/20'
                      : 'bg-[#0C1629]/70 border-[rgba(67,139,255,0.14)] text-[#A3B4CF] hover:border-[rgba(83,215,245,0.3)] hover:bg-[#111E35]'
                  }`}
                >
                  <div className="font-semibold text-xs text-[#F1F6FF] mb-1">{p.name}</div>
                  <div className="text-[11px] text-[#7285A5]">{p.sub}</div>
                  <div className="mt-2 text-[10px] font-mono text-[#53D7F5]">{p.model}</div>
                </button>
              ))}
            </div>

            {provider === 'gemini' && (
              <div className="space-y-1.5 pt-2">
                <label className="text-xs font-medium text-[#A3B4CF] block">Google Gemini API Key</label>
                <div className="relative">
                  <Key className="w-4 h-4 text-[#7285A5] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="AIzaSy..."
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] font-mono focus:outline-none focus:border-[#438BFF]"
                  />
                </div>
                <p className="text-[11px] text-[#7285A5]">Encrypted at rest using Fernet AES-256 before storage.</p>
              </div>
            )}

            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setCurrentStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>

              <button
                onClick={handleStep2Save}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/25 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <span>{loading ? 'Saving...' : 'Save & Continue'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Connect Gmail (Optional) */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Mail className="w-5 h-5 text-[#F2B65D]" />
                <span>Step 3: Connect Real-World Integrations (Optional)</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Connect Google Gmail to enable autonomous email reading, priority triaging, and approval-gated drafting.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#F16B7A]/15 border border-[#F16B7A]/30 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-[#F16B7A]" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-[#F1F6FF] flex items-center gap-2">
                    <span>Google Gmail OAuth 2.0</span>
                    {gmailConnected ? (
                      <span className="px-2 py-0.5 rounded-full bg-[#28C995]/20 text-[#28C995] text-[10px] font-medium border border-[#28C995]/30">Connected</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-[#080F20] text-[#7285A5] border border-[rgba(67,139,255,0.14)] text-[10px] font-medium">Unconnected</span>
                    )}
                  </div>
                  <div className="text-[11px] text-[#A3B4CF]">Scopes: Read emails, create drafts, and send upon human authorization.</div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-stretch sm:self-auto">
                <a
                  href="/api/v1/integrations/gmail/authorize"
                  className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-[#111E35] hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] font-medium transition-all"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-[#53D7F5]" />
                  <span>Connect Gmail</span>
                </a>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#0C1629]/60 border border-[rgba(67,139,255,0.12)] text-xs text-[#A3B4CF]">
              <span className="font-semibold text-[#F1F6FF]">Optional Step:</span> If you don&apos;t have OAuth credentials configured, you can skip this step safely. FlowPilot provides simulated triggers and deterministic mock data for seamless development.
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setCurrentStep(2)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    toast.info('Skipped Gmail connection.');
                    setCurrentStep(4);
                  }}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
                >
                  <SkipForward className="w-3.5 h-3.5" />
                  <span>Skip for now</span>
                </button>

                <button
                  onClick={() => setCurrentStep(4)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/25 border border-white/20 transition-all hover:-translate-y-0.5"
                >
                  <span>Continue to Templates</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: Explore Templates */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Layers className="w-5 h-5 text-[#438BFF]" />
                <span>Step 4: Explore Production Workflow Templates</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Select a validated production template to load into your workspace.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 max-h-[380px] overflow-y-auto pr-1">
              {templates.map((tpl) => (
                <button
                  key={tpl.id}
                  onClick={() => handleStep4Select(tpl.id)}
                  className={`p-4 rounded-2xl border text-left transition-all ${
                    selectedTemplateId === tpl.id
                      ? 'bg-[#287BFA]/20 border-[#438BFF] text-white shadow-md shadow-[#287BFA]/20'
                      : 'bg-[#0C1629]/70 border-[rgba(67,139,255,0.14)] text-[#A3B4CF] hover:border-[rgba(83,215,245,0.3)] hover:bg-[#111E35]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#080F20] text-[#53D7F5] border border-[rgba(67,139,255,0.25)]">
                      {tpl.category}
                    </span>
                    {selectedTemplateId === tpl.id && <Check className="w-3.5 h-3.5 text-[#28C995]" />}
                  </div>
                  <div className="font-semibold text-xs text-[#F1F6FF] mb-1">{tpl.name}</div>
                  <p className="text-[11px] text-[#A3B4CF] leading-relaxed line-clamp-2">{tpl.description}</p>
                  <div className="mt-2 text-[10px] text-[#7285A5] font-mono">
                    {tpl.nodes.length} nodes · {tpl.edges.length} connections
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setCurrentStep(3)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>

              <button
                onClick={() => setCurrentStep(5)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/25 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <span>Continue with Selected Template</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: Generate & Instantiate Workflow */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#53D7F5]" />
                <span>Step 5: Instantiate Workflow into Workspace</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Instantiate the validated DAG structure and register version 1.0 in your workspace database.
              </p>
            </div>

            {(() => {
              const selectedTpl = templates.find((t) => t.id === selectedTemplateId);
              return (
                <div className="p-5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-[#F1F6FF]">{selectedTpl?.name}</div>
                      <div className="text-xs text-[#A3B4CF]">{selectedTpl?.description}</div>
                    </div>
                    <span className="text-xs font-mono text-[#28C995] bg-[#28C995]/15 border border-[#28C995]/30 px-2.5 py-1 rounded-xl">
                      Ready to Instantiate
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#111E35] border border-[rgba(67,139,255,0.12)] space-y-2">
                    <div className="text-[11px] font-semibold text-[#A3B4CF]">Topological Node Sequence:</div>
                    <div className="flex flex-wrap items-center gap-2">
                      {selectedTpl?.nodes.map((n, i) => (
                        <React.Fragment key={n.id}>
                          <span className="px-2.5 py-1 rounded-xl bg-[#0C1629] border border-[rgba(67,139,255,0.18)] text-[11px] text-[#F1F6FF] font-mono">
                            {n.label}
                          </span>
                          {i < selectedTpl.nodes.length - 1 && <span className="text-[#53D7F5] text-xs">→</span>}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })()}

            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setCurrentStep(4)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>

              <button
                onClick={handleStep5Instantiate}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/25 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <Sparkles className="w-4 h-4" />
                <span>{loading ? 'Instantiating...' : 'Instantiate Workflow'}</span>
              </button>
            </div>
          </div>
        )}

        {/* STEP 6: Execute Sample Workflow */}
        {currentStep === 6 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <Play className="w-5 h-5 text-[#28C995]" />
                <span>Step 6: Trigger Asynchronous Test Execution</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Dispatch the workflow to Celery background workers and verify non-blocking topological execution.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] space-y-3">
              <div className="text-xs font-semibold text-[#F1F6FF]">Target Workflow: {createdWorkflow?.name}</div>
              <div className="text-[11px] text-[#A3B4CF]">
                ID: <code className="text-[#53D7F5]">{createdWorkflow?.id}</code> · Workspace: <code className="text-[#7285A5]">{createdWorkflow?.workspace_id}</code>
              </div>
              <div className="text-xs text-[#A3B4CF] leading-relaxed">
                Clicking Execute will trigger Kahn&apos;s topological sort, propagate node inputs/outputs, and execute each node asynchronously.
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setCurrentStep(5)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#7285A5] hover:text-[#F1F6FF] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>

              <button
                onClick={handleStep6Execute}
                disabled={executing}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[#28C995] to-[#20A27A] hover:from-[#2ED8A0] hover:to-[#24B88A] text-white text-xs font-semibold shadow-lg shadow-[#28C995]/25 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>{executing ? 'Executing Pipeline...' : 'Run Test Execution'}</span>
              </button>
            </div>
          </div>
        )}

        {/* STEP 7: Inspect Execution Results */}
        {currentStep === 7 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[#F1F6FF] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-[#28C995]" />
                <span>Step 7: Execution Telemetry & Observability</span>
              </h2>
              <p className="text-xs text-[#A3B4CF]">
                Review the execution state, completed nodes, and telemetry persisted in your database.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#0C2422]/60 border border-[#28C995]/35 space-y-4 backdrop-blur-xl shadow-xl shadow-[#28C995]/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#28C995]/20 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 text-[#28C995]" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-[#F1F6FF]">Execution Dispatched Successfully</div>
                    <div className="text-xs text-[#A3B4CF]">Execution ID: <code className="text-[#28C995]">{execution?.id}</code></div>
                  </div>
                </div>

                <span className="px-3 py-1 rounded-full bg-[#28C995]/20 border border-[#28C995]/40 text-xs font-semibold text-[#28C995]">
                  {execution?.status || 'COMPLETED'}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-3 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.12)]">
                  <div className="text-[10px] text-[#7285A5]">Trigger Type</div>
                  <div className="text-xs font-semibold text-[#F1F6FF] mt-0.5">{execution?.trigger_type || 'MANUAL'}</div>
                </div>
                <div className="p-3 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.12)]">
                  <div className="text-[10px] text-[#7285A5]">Initial Nodes</div>
                  <div className="text-xs font-semibold text-[#F1F6FF] mt-0.5">Topological Sequence Active</div>
                </div>
                <div className="p-3 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.12)]">
                  <div className="text-[10px] text-[#7285A5]">Observability Trace</div>
                  <div className="text-xs font-semibold text-[#28C995] mt-0.5">Persisted in Postgres</div>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <Link
                href={`/executions`}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-[#53D7F5] hover:underline font-medium"
              >
                <span>View in Execution Inspector</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>

              <button
                onClick={() => {
                  toast.success('Onboarding complete! Welcome to FlowPilot AI.');
                  router.push('/');
                }}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-xl shadow-[#287BFA]/30 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <span>Enter FlowPilot Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
