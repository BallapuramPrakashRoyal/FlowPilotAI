'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  ArrowRight,
  Bot,
  Layers,
  CheckCircle2,
  Workflow,
  Cpu,
  RefreshCw,
  Mail,
  Zap,
} from 'lucide-react';
import { api } from '@/services/api';

export function AIGeneratorView() {
  const router = useRouter();
  const [prompt, setPrompt] = useState(
    'Read my unread Gmail messages every morning, classify urgent messages, summarize important emails, and prepare responses for my approval.'
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<any | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const samplePrompts = [
    'Read my unread Gmail messages, classify urgent messages, summarize emails, and prepare responses for my approval.',
    'Scrape inbound customer inquiries via HTTP webhook, analyze sentiment, extract priority, and post urgent alerts to Slack.',
    'Retrieve monthly invoices from Gmail, extract financial amounts using RAG document search, and create a draft response.',
  ];

  const handleGenerate = async (targetPrompt?: string) => {
    const textToUse = targetPrompt || prompt;
    if (!textToUse.trim()) return;

    setIsGenerating(true);
    setSaveMessage(null);
    try {
      const result = await api.generateWorkflowAI(textToUse);
      setGeneratedResult(result);
    } catch (e: any) {
      console.error('Workflow generation failed', e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveWorkflow = async () => {
    if (!generatedResult) return;
    setIsSaving(true);
    try {
      await api.createWorkflow(
        generatedResult.name,
        generatedResult.description,
        generatedResult.graph
      );
      setSaveMessage('✓ Workflow saved to database!');
      setTimeout(() => setSaveMessage(null), 4000);
    } catch (e: any) {
      setSaveMessage(`Failed to save: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenInStudio = () => {
    if (!generatedResult) return;
    if (typeof window !== 'undefined') {
      localStorage.setItem(
        'flowpilot_studio_import',
        JSON.stringify({
          name: generatedResult.name,
          description: generatedResult.description,
          graph: generatedResult.graph,
        })
      );
    }
    router.push('/studio');
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] mb-2 shadow-[0_0_12px_rgba(40,123,250,0.2)]">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Autonomous AI Workflow Architect</span>
        </div>
        <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">AI Workflow Generator</h1>
        <p className="text-sm text-[#A3B4CF]">
          Describe your objective in natural language. FlowPilot&apos;s multi-agent planner decomposes goals, validates tool registry contracts, and builds an executable DAG.
        </p>
      </div>

      {/* Prompt Input Box */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
        <textarea
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. Fetch unread emails, classify urgency, draft reply, and request approval before dispatching..."
          className="w-full p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-sm text-[#F1F6FF] placeholder-[#7285A5] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_16px_rgba(67,139,255,0.25)] transition-all resize-none"
        />

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#7285A5]">Templates:</span>
            {samplePrompts.map((sp, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setPrompt(sp);
                  handleGenerate(sp);
                }}
                className="px-2.5 py-1 rounded-xl bg-[#0C1629]/70 hover:bg-[#172743] text-[11px] text-[#A3B4CF] hover:text-[#F1F6FF] border border-[rgba(67,139,255,0.12)] transition-all truncate max-w-xs"
              >
                {sp.slice(0, 38)}...
              </button>
            ))}
          </div>

          <button
            onClick={() => handleGenerate()}
            disabled={isGenerating}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-lg shadow-[#287BFA]/30 border border-white/20 transition-all disabled:opacity-50 hover:-translate-y-0.5 active:translate-y-0"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Synthesizing DAG...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-white text-white" />
                <span>Generate Workflow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generated Workflow Plan Results */}
      {generatedResult && (
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[rgba(67,139,255,0.15)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-[#F1F6FF] tracking-tight">{generatedResult.name}</h2>
                <span className="px-2.5 py-0.5 rounded-full bg-[#28C995]/15 text-[#28C995] border border-[#28C995]/30 text-[11px] font-mono">
                  Valid DAG
                </span>
              </div>
              <p className="text-xs text-[#A3B4CF] mt-1">{generatedResult.description}</p>
            </div>

            <div className="flex items-center gap-3">
              {saveMessage && (
                <span className="text-xs font-medium text-[#28C995] bg-[#28C995]/15 px-3 py-1.5 rounded-xl border border-[#28C995]/30">
                  {saveMessage}
                </span>
              )}

              <button
                onClick={handleSaveWorkflow}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#0C1629]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] text-[#F1F6FF] text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-[#53D7F5]" />
                <span>{isSaving ? 'Saving...' : 'Save as Workflow'}</span>
              </button>

              <button
                onClick={handleOpenInStudio}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-[#28C995] to-[#20A27A] hover:from-[#2ED8A0] hover:to-[#24B88A] text-white text-xs font-semibold shadow-md shadow-[#28C995]/20 border border-white/20 transition-all hover:-translate-y-0.5"
              >
                <span>Open in Studio</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* AI Explanation & Integration tags */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#438BFF]" />
              <span>Architectural Explanation</span>
            </div>
            <p className="text-xs text-[#A3B4CF] leading-relaxed bg-[#0C1629]/70 p-4 rounded-2xl border border-[rgba(67,139,255,0.14)]">
              {generatedResult.explanation}
            </p>
          </div>

          {/* Generated Node Sequence Visualizer */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider flex items-center gap-2">
              <Workflow className="w-4 h-4 text-[#53D7F5]" />
              <span>Planned Node Sequence ({generatedResult.graph.nodes.length} nodes)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
              {generatedResult.graph.nodes.map((node: any, i: number) => (
                <div
                  key={node.id}
                  className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] hover:border-[rgba(83,215,245,0.3)] relative flex flex-col justify-between transition-colors shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#287BFA]/15 text-[#53D7F5] border border-[#287BFA]/30">
                      Step {i + 1}
                    </span>
                    <span className="text-[10px] font-mono text-[#7285A5]">{node.type}</span>
                  </div>
                  <div className="text-xs font-semibold text-[#F1F6FF]">{node.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
