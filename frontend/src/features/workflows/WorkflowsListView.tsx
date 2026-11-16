'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  GitFork,
  Plus,
  Sparkles,
  Workflow,
  ArrowRight,
  Layers,
  Copy,
  ExternalLink,
  Search,
  Filter,
} from 'lucide-react';
import { api } from '@/services/api';
import { Workflow as WorkflowType, WorkflowTemplate } from '@/types';
import { useToast } from '@/components/ui/Toast';

export function WorkflowsListView() {
  const router = useRouter();
  const toast = useToast();
  const [workflows, setWorkflows] = useState<WorkflowType[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [activeTab, setActiveTab] = useState<'workflows' | 'templates'>('workflows');
  const [loading, setLoading] = useState(true);
  const [instantiatingId, setInstantiatingId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  useEffect(() => {
    async function loadData() {
      try {
        const [wfList, tplList] = await Promise.all([
          api.listWorkflows(),
          api.listTemplates().catch(() => []),
        ]);
        setWorkflows(wfList);
        setTemplates(tplList);
      } catch (e) {
        console.error('Failed to load workflows', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleInstantiate = async (templateId: string) => {
    setInstantiatingId(templateId);
    try {
      const newWf = await api.instantiateTemplate(templateId);
      toast.success(`Instantiated "${newWf.name}" into workspace!`);
      const updatedList = await api.listWorkflows();
      setWorkflows(updatedList);
      setActiveTab('workflows');
    } catch (e) {
      toast.error('Failed to instantiate template.');
    } finally {
      setInstantiatingId(null);
    }
  };

  const handleCustomize = (template: WorkflowTemplate) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('flowpilot_draft_template', JSON.stringify(template));
    }
    router.push('/studio?from_template=' + template.id);
  };

  const categories = ['ALL', ...Array.from(new Set(templates.map((t) => t.category)))];

  const filteredWorkflows = workflows.filter((w) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (w.description && w.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredTemplates = templates.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = categoryFilter === 'ALL' || t.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Workflows & Templates</h1>
          <p className="text-sm text-[#A3B4CF]">
            Manage, configure, and instantiate autonomous multi-agent pipelines and DAG graphs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/generator"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.35)] text-xs text-[#F1F6FF] font-medium transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#53D7F5]" />
            <span>AI Generator</span>
          </Link>

          <Link
            href="/studio"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/25 border border-white/20 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>New Workflow</span>
          </Link>
        </div>
      </div>

      {/* Navigation Tabs & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-b border-[rgba(67,139,255,0.15)] pb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('workflows')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'workflows'
                ? 'bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white shadow-[0_0_16px_rgba(40,123,250,0.35),inset_0_1px_0_rgba(255,255,255,0.25)] border border-white/20'
                : 'bg-[#111E35]/60 text-[#A3B4CF] hover:text-[#F1F6FF] hover:bg-[#172743] border border-[rgba(67,139,255,0.14)]'
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>My Workflows ({workflows.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('templates')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'templates'
                ? 'bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white shadow-[0_0_16px_rgba(40,123,250,0.35),inset_0_1px_0_rgba(255,255,255,0.25)] border border-white/20'
                : 'bg-[#111E35]/60 text-[#A3B4CF] hover:text-[#F1F6FF] hover:bg-[#172743] border border-[rgba(67,139,255,0.14)]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-[#53D7F5]" />
            <span>Production Templates ({templates.length})</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'templates' && (
            <div className="flex items-center gap-1.5 bg-[#0C1629]/70 px-2.5 py-1.5 rounded-xl border border-[rgba(67,139,255,0.16)] text-xs text-[#A3B4CF]">
              <Filter className="w-3 h-3 text-[#53D7F5]" />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                aria-label="Filter templates by category"
                className="bg-transparent text-[#F1F6FF] text-xs focus:outline-none"
              >
                {categories.map((c) => (
                  <option key={c} value={c} className="bg-[#0C1629] text-[#F1F6FF]">
                    {c}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-[#7285A5] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search workflows & templates..."
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] placeholder-[#7285A5] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.2)]"
            />
          </div>
        </div>
      </div>

      {/* TAB 1: My Workflows Grid */}
      {activeTab === 'workflows' && (
        <>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-44 rounded-3xl bg-[#111E35]/50 animate-pulse border border-[rgba(67,139,255,0.1)]" />
              ))}
            </div>
          ) : filteredWorkflows.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredWorkflows.map((wf) => (
                <div
                  key={wf.id}
                  className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.4)] hover:bg-[#172743]/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] transition-all duration-200 flex flex-col justify-between space-y-5 group hover:-translate-y-1"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-2xl bg-[#287BFA]/15 border border-[#438BFF]/30 text-[#438BFF] flex items-center justify-center shadow-[0_0_12px_rgba(40,123,250,0.2)]">
                        <Workflow className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#28C995]/15 text-[#28C995] border border-[#28C995]/30">
                        ACTIVE
                      </span>
                    </div>

                    <div>
                      <h2 className="text-base font-bold text-[#F1F6FF] group-hover:text-[#53D7F5] transition-colors line-clamp-1">
                        {wf.name}
                      </h2>
                      <p className="text-xs text-[#A3B4CF] mt-1 line-clamp-2 leading-relaxed">
                        {wf.description || 'Configured autonomous workflow pipeline.'}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[rgba(67,139,255,0.12)] flex items-center justify-between">
                    <div className="text-[11px] text-[#7285A5] font-mono">
                      {wf.graph?.nodes?.length || 5} nodes in DAG
                    </div>

                    <Link
                      href={`/studio?workflow_id=${wf.id}`}
                      className="flex items-center gap-1 text-xs text-[#53D7F5] font-semibold hover:gap-1.5 transition-all"
                    >
                      <span>Open in Studio</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] text-center space-y-4 shadow-xl">
              <div className="w-12 h-12 rounded-2xl bg-[#287BFA]/15 border border-[#438BFF]/30 text-[#438BFF] flex items-center justify-center mx-auto shadow-[0_0_16px_rgba(40,123,250,0.2)]">
                <GitFork className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-[#F1F6FF]">No workflows matching your criteria</h3>
                <p className="text-xs text-[#A3B4CF] max-w-sm mx-auto">
                  Instantiate a pre-built production template or let our AI generator synthesize your DAG.
                </p>
              </div>
              <div className="pt-2 flex items-center justify-center gap-3">
                <button
                  onClick={() => setActiveTab('templates')}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/20 border border-white/20 transition-all hover:-translate-y-0.5"
                >
                  Browse Templates
                </button>
                <Link
                  href="/generator"
                  className="px-4 py-2 rounded-xl bg-[#0C1629]/70 text-[#A3B4CF] hover:text-white text-xs font-semibold border border-[rgba(67,139,255,0.18)] transition-all hover:-translate-y-0.5"
                >
                  AI Generator
                </Link>
              </div>
            </div>
          )}
        </>
      )}

      {/* TAB 2: Production Templates Grid */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="p-4 rounded-2xl bg-[#111E35]/70 border border-[rgba(67,139,255,0.2)] text-xs text-[#A3B4CF] flex items-center gap-3 backdrop-blur-xl shadow-lg">
            <Layers className="w-4 h-4 text-[#53D7F5] shrink-0" />
            <span>
              All templates are pre-validated with Kahn&apos;s topological sort and valid node schemas. You can instantiate them directly or customize them in the Visual Studio.
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((tpl) => (
              <div
                key={tpl.id}
                className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.4)] hover:bg-[#172743]/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] transition-all duration-200 flex flex-col justify-between space-y-4 group hover:-translate-y-1"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#0C1629] text-[#53D7F5] border border-[rgba(67,139,255,0.25)]">
                      {tpl.category}
                    </span>
                    {tpl.badge && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#28C995]/15 text-[#28C995] border border-[#28C995]/30">
                        {tpl.badge}
                      </span>
                    )}
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-[#F1F6FF] group-hover:text-[#53D7F5] transition-colors line-clamp-1">
                      {tpl.name}
                    </h3>
                    <p className="text-xs text-[#A3B4CF] mt-1.5 leading-relaxed line-clamp-3">
                      {tpl.description}
                    </p>
                  </div>

                  <div className="p-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.12)] text-[10px] font-mono text-[#7285A5] flex items-center justify-between">
                    <span>{tpl.nodes.length} registered nodes</span>
                    <span>{tpl.edges.length} edges</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-[rgba(67,139,255,0.12)] flex items-center gap-2">
                  <button
                    onClick={() => handleCustomize(tpl)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-[#0C1629]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] font-medium transition-all"
                  >
                    <ExternalLink className="w-3.5 h-3.5 text-[#7285A5]" />
                    <span>Customize</span>
                  </button>

                  <button
                    onClick={() => handleInstantiate(tpl.id)}
                    disabled={instantiatingId === tpl.id}
                    className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/25 border border-white/20 transition-all active:scale-95 disabled:opacity-50"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>{instantiatingId === tpl.id ? 'Adding...' : 'Use Template'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
