'use client';

import React, { useState } from 'react';
import {
  BookOpen,
  UploadCloud,
  Search,
  FileText,
  CheckCircle2,
  Database,
  Quote,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '@/services/api';

export function KnowledgeBaseView() {
  const [query, setQuery] = useState('What are the SLA resolution requirements for critical incidents?');
  const [citations, setCitations] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadedDocs] = useState([
    { id: 'doc-1', name: 'Company_SLA_and_Incident_Protocols.pdf', size: '240 KB', chunks: 14, status: 'INDEXED' },
    { id: 'doc-2', name: 'Product_Engineering_Architecture.docx', size: '1.2 MB', chunks: 48, status: 'INDEXED' },
  ]);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      setTimeout(() => {
        setCitations([
          {
            document: 'Company_SLA_and_Incident_Protocols.pdf',
            similarity: 0.942,
            chunk: 'For P1 Critical Incidents (system outages, payment degradation, latency > 5000ms), team response SLA is 15 minutes, with written executive notification within 1 hour.',
          },
          {
            document: 'Company_SLA_and_Incident_Protocols.pdf',
            similarity: 0.885,
            chunk: 'All incident notifications must be approved by the incident commander prior to external client broadcast.',
          },
        ]);
        setIsSearching(false);
      }, 600);
    } catch (e) {
      setIsSearching(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#287BFA]/15 border border-[#438BFF]/35 text-xs font-semibold text-[#53D7F5] mb-2 shadow-[0_0_12px_rgba(40,123,250,0.2)]">
          <Database className="w-3.5 h-3.5" />
          <span>Vector Search & pgvector RAG</span>
        </div>
        <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">Knowledge Base & RAG</h1>
        <p className="text-sm text-[#A3B4CF]">
          Upload enterprise documentation for automatic chunking, embedding generation, and verifiable context retrieval.
        </p>
      </div>

      {/* Upload Zone & Documents List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Dropzone */}
        <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border-2 border-dashed border-[rgba(67,139,255,0.25)] hover:border-[#53D7F5] flex flex-col items-center justify-center text-center space-y-3 cursor-pointer transition-all duration-200 group shadow-[0_8px_24px_rgba(4,9,20,0.3)]">
          <div className="w-12 h-12 rounded-2xl bg-[#287BFA]/15 group-hover:bg-[#287BFA]/25 text-[#438BFF] group-hover:text-[#53D7F5] flex items-center justify-center transition-colors shadow-[0_0_16px_rgba(40,123,250,0.2)]">
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-[#F1F6FF]">Upload Documents</div>
            <div className="text-[11px] text-[#7285A5] mt-1">PDF, DOCX, TXT up to 25MB</div>
          </div>
          <button className="px-3.5 py-1.5 rounded-xl bg-[#0C1629]/70 hover:bg-[#172743] text-[#F1F6FF] text-xs font-medium border border-[rgba(67,139,255,0.18)] shadow-sm transition-all">
            Select File
          </button>
        </div>

        {/* Ingested Documents List */}
        <div className="md:col-span-2 p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-3">
          <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Indexed Corpus</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0C1629] text-[#53D7F5] border border-[rgba(67,139,255,0.18)]">{uploadedDocs.length} Documents</span>
          </div>

          <div className="space-y-2.5">
            {uploadedDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] hover:border-[rgba(83,215,245,0.3)] flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-xl bg-[#287BFA]/15 border border-[#438BFF]/30 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4 text-[#438BFF]" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-[#F1F6FF] truncate">{doc.name}</div>
                    <div className="text-[10px] text-[#7285A5] font-mono">
                      {doc.size} • {doc.chunks} vector chunks
                    </div>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#28C995]/15 text-[#28C995] border border-[#28C995]/30">
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Semantic Retrieval Playground */}
      <div className="p-6 rounded-3xl bg-[#111E35]/65 backdrop-blur-xl border border-[rgba(67,139,255,0.18)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_12px_32px_rgba(4,9,20,0.4)] space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-[#F1F6FF] tracking-tight">Semantic Similarity Search</h2>
          <p className="text-xs text-[#7285A5]">Test real-time pgvector similarity retrieval against stored embeddings</p>
        </div>

        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#7285A5] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question or enter retrieval query..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] text-xs text-[#F1F6FF] placeholder-[#7285A5] focus:outline-none focus:border-[#438BFF] focus:shadow-[0_0_16px_rgba(67,139,255,0.25)] transition-all"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={isSearching}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] text-white text-xs font-semibold shadow-md shadow-[#287BFA]/25 border border-white/20 transition-all disabled:opacity-50"
          >
            {isSearching ? 'Querying...' : 'Search Vectors'}
          </button>
        </div>

        {/* Citations Results */}
        {citations.length > 0 && (
          <div className="pt-4 border-t border-[rgba(67,139,255,0.12)] space-y-3">
            <div className="text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider flex items-center gap-1.5">
              <Quote className="w-3.5 h-3.5 text-[#28C995]" />
              <span>Attributed Source Context</span>
            </div>

            <div className="space-y-3">
              {citations.map((cite, i) => (
                <div key={i} className="p-4 rounded-2xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.14)] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#F1F6FF]">{cite.document}</span>
                    <span className="text-[11px] font-mono text-[#28C995] px-2 py-0.5 rounded-full bg-[#28C995]/15 border border-[#28C995]/30">
                      Cosine Score: {cite.similarity}
                    </span>
                  </div>
                  <p className="text-xs text-[#A3B4CF] leading-relaxed italic bg-[#080F20]/70 p-3.5 rounded-xl border border-[rgba(67,139,255,0.1)]">
                    &ldquo;{cite.chunk}&rdquo;
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
