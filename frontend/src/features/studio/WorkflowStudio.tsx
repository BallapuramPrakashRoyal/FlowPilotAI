'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ReactFlow, Controls, Background, MiniMap, applyNodeChanges, applyEdgeChanges,
  Node, Edge, Connection, OnNodesChange, OnEdgesChange, OnConnect, ReactFlowInstance,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AlertTriangle, Check, CheckCircle, ChevronDown, ChevronRight, Copy, GripVertical, LayoutTemplate, Play, Redo2, Save, Search, Settings2, TestTube2, Trash2, Undo2, Upload, X } from 'lucide-react';
import { nodeTypes } from './CustomNodes';
import { api } from '@/services/api';
import { Workflow, WorkflowGraph } from '@/types';

type StudioNode = Node<{ type: string; label: string; config: Record<string, unknown> }>;
type PaletteItem = { type: string; label: string; category: string };
const INITIAL_NODES: StudioNode[] = [
  { id: 'node-1', type: 'gmailTrigger', position: { x: 80, y: 160 }, data: { type: 'gmailTrigger', label: 'Gmail: Fetch Unread', config: { folder: 'INBOX', unread_only: true, max_results: 5 } } },
  { id: 'node-2', type: 'textClassifier', position: { x: 400, y: 160 }, data: { type: 'textClassifier', label: 'AI Analyst: Urgency Triage', config: { categories: ['Urgent', 'Important', 'Spam'] } } },
  { id: 'node-3', type: 'aiAgent', position: { x: 720, y: 160 }, data: { type: 'aiAgent', label: 'AI Drafter: Generate Response', config: { role: 'Executive Assistant', tone: 'Professional' } } },
  { id: 'node-4', type: 'humanApproval', position: { x: 1040, y: 160 }, data: { type: 'humanApproval', label: 'Human Review: Approve Email', config: { timeout_hours: 24, action: 'SEND_GMAIL_MESSAGE' } } },
  { id: 'node-5', type: 'output', position: { x: 1360, y: 160 }, data: { type: 'output', label: 'Dispatch Approved Email', config: { destination: 'Gmail API' } } },
];
const INITIAL_EDGES: Edge[] = ['1-2', '2-3', '3-4', '4-5'].map((pair) => {
  const [source, target] = pair.split('-');
  return { id: `e${pair}`, source: `node-${source}`, target: `node-${target}`, sourceHandle: 'output', targetHandle: 'input', animated: true, style: { stroke: '#8065E8' } };
});
const PALETTE: PaletteItem[] = [
  ['manualTrigger', 'Manual Trigger', 'Triggers'], ['scheduleTrigger', 'Schedule Trigger', 'Triggers'], ['gmailTrigger', 'Gmail Trigger', 'Triggers'],
  ['aiAgent', 'AI Agent', 'AI'], ['llmCompletion', 'LLM Completion', 'AI'], ['textClassifier', 'Text Classifier', 'AI'],
  ['textSummarizer', 'Text Summarizer', 'AI'], ['dataExtractor', 'Data Extractor', 'AI'],
  ['informationExtractor', 'Information Extractor', 'AI'], ['aiDecision', 'AI Decision', 'AI'],
  ['condition', 'Condition Branch', 'Logic'], ['transform', 'Data Transform', 'Logic'], ['humanApproval', 'Human Approval', 'Approvals'],
  ['output', 'Workflow Output', 'Outputs'], ['httpIntegration', 'HTTP Integration', 'Integrations'], ['delay', 'Delay Timer', 'Utilities'], ['notification', 'Notification', 'Utilities'],
].map(([type, label, category]) => ({ type, label, category }));
const CATEGORIES = [...new Set(PALETTE.map((item) => item.category))];

function graphFrom(nodes: StudioNode[], edges: Edge[], viewport?: { x: number; y: number; zoom: number }): WorkflowGraph {
  return { nodes: nodes.map((n) => ({ id: n.id, type: n.data.type || n.type || 'unknown', label: n.data.label || n.id, position: n.position, config: n.data.config || {} })), edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle || undefined, targetHandle: e.targetHandle || undefined })), viewport };
}
function cloneState(nodes: StudioNode[], edges: Edge[]) { return { nodes: nodes.map((n) => ({ ...n, position: { ...n.position }, data: { ...n.data, config: { ...n.data.config } } })), edges: edges.map((e) => ({ ...e })) }; }

export function WorkflowStudio() {
  const [nodes, setNodes] = useState<StudioNode[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<Edge[]>(INITIAL_EDGES);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('Autonomous Gmail Triaging & Draft');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [status, setStatus] = useState('Saved');
  const [notice, setNotice] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>(Object.fromEntries(CATEGORIES.map((c) => [c, true])));
  const [validation, setValidation] = useState<{ ok: boolean; errors: string[] } | null>(null);
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });
  const [history, setHistory] = useState<{ nodes: StudioNode[]; edges: Edge[] }[]>([]);
  const [future, setFuture] = useState<{ nodes: StudioNode[]; edges: Edge[] }[]>([]);
  const flowRef = useRef<ReactFlowInstance<StudioNode, Edge> | null>(null);
  const draggingType = useRef<string | null>(null);
  const selectedNode = nodes.find((n) => n.id === selectedId) || null;

  const commit = useCallback((nextNodes: StudioNode[], nextEdges: Edge[]) => {
    setHistory((h) => [...h.slice(-49), cloneState(nodes, edges)]);
    setFuture([]);
    setNodes(nextNodes); setEdges(nextEdges); setStatus('Unsaved changes');
  }, [nodes, edges]);
  const onNodesChange: OnNodesChange<StudioNode> = useCallback((changes) => {
    setNodes((current) => applyNodeChanges(changes, current) as StudioNode[]);
    if (changes.some((change) => change.type !== 'select')) setStatus('Unsaved changes');
  }, []);
  const onEdgesChange: OnEdgesChange = useCallback((changes) => { setEdges((current) => applyEdgeChanges(changes, current)); setStatus('Unsaved changes'); }, []);
  const onConnect: OnConnect = useCallback((connection: Connection) => {
    if (!connection.source || !connection.target || connection.source === connection.target) return;
    const source = nodes.find((n) => n.id === connection.source);
    const target = nodes.find((n) => n.id === connection.target);
    if (!source || !target || source.data.type.toLowerCase().includes('output') || target.data.type.toLowerCase().includes('trigger')) return;
    if (edges.some((e) => e.source === connection.source && e.target === connection.target && (e.sourceHandle || '') === (connection.sourceHandle || ''))) return;
    commit(nodes, [...edges, { ...connection, id: `e-${connection.source}-${connection.target}-${Date.now()}`, animated: true, style: { stroke: '#438BFF' } }]);
  }, [nodes, edges, commit]);
  const selectedItems = useMemo(() => PALETTE.filter((p) => p.label.toLowerCase().includes(search.toLowerCase())), [search]);

  useEffect(() => {
    const load = async () => {
      const params = new URLSearchParams(window.location.search);
      const queryId = params.get('workflowId') || params.get('workflow_id') || params.get('id');
      try {
        let imported: unknown = localStorage.getItem('flowpilot_studio_import');
        const draftTemplate = typeof window !== 'undefined' ? sessionStorage.getItem('flowpilot_draft_template') : null;
        if (queryId) {
          imported = await api.getWorkflow(queryId);
        } else if (draftTemplate) {
          imported = JSON.parse(draftTemplate);
          sessionStorage.removeItem('flowpilot_draft_template');
        } else if (imported) {
          imported = JSON.parse(imported as string);
        }
        if (imported) {
          const value = imported as Workflow & { workflow?: Workflow };
          const workflow = value.graph ? value : value.workflow || value;
          if (workflow.name) setWorkflowName(workflow.name);
          if (workflow.id) setWorkflowId(workflow.id);
          if (workflow.graph?.nodes) setNodes(workflow.graph.nodes.map((n) => ({ id: n.id, type: n.type, position: n.position || { x: 100, y: 100 }, data: { type: n.type, label: n.label || n.id, config: n.config || {} } })));
          if (workflow.graph?.edges) setEdges(workflow.graph.edges.map((e) => ({ ...e, animated: true, style: { stroke: '#438BFF' } })));
          setStatus('Saved');
        }
      } catch { setNotice('Unable to load the requested workflow.'); }
      localStorage.removeItem('flowpilot_studio_import');
      const savedViewport = localStorage.getItem('flowpilot_studio_viewport');
      if (savedViewport) try { const saved = JSON.parse(savedViewport); setViewport(saved); flowRef.current?.setViewport(saved); } catch {}
    };
    load();
  }, []);
  useEffect(() => { localStorage.setItem('flowpilot_studio_viewport', JSON.stringify(viewport)); }, [viewport]);
  const undo = useCallback(() => { const previous = history.at(-1); if (!previous) return; setFuture((f) => [...f, cloneState(nodes, edges)]); setHistory((h) => h.slice(0, -1)); setNodes(previous.nodes); setEdges(previous.edges); setStatus('Unsaved changes'); }, [history, nodes, edges]);
  const redo = useCallback(() => { const next = future.at(-1); if (!next) return; setHistory((h) => [...h, cloneState(nodes, edges)]); setFuture((f) => f.slice(0, -1)); setNodes(next.nodes); setEdges(next.edges); setStatus('Unsaved changes'); }, [future, nodes, edges]);
  const addNode = useCallback((type: string, label: string, position?: { x: number; y: number }) => {
    const node: StudioNode = { id: `node-${Date.now()}`, type, position: position || { x: 240, y: 180 }, data: { type, label, config: {} } };
    commit([...nodes, node], edges); setSelectedId(node.id);
  }, [nodes, edges, commit]);
  const deleteSelected = useCallback(() => { if (!selectedId) return; commit(nodes.filter((n) => n.id !== selectedId), edges.filter((e) => e.source !== selectedId && e.target !== selectedId)); setSelectedId(null); }, [selectedId, nodes, edges, commit]);
  useEffect(() => {
    const keyHandler = (event: KeyboardEvent) => {
      if ((event.target as HTMLElement)?.tagName === 'INPUT' || (event.target as HTMLElement)?.tagName === 'TEXTAREA') return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); if (event.shiftKey) redo(); else undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if (event.key === 'Delete' || event.key === 'Backspace') deleteSelected();
    };
    window.addEventListener('keydown', keyHandler); return () => window.removeEventListener('keydown', keyHandler);
  }, [redo, undo, deleteSelected]);
  const duplicateSelected = () => { if (!selectedNode) return; addNode(selectedNode.data.type, `${selectedNode.data.label} copy`, { x: selectedNode.position.x + 40, y: selectedNode.position.y + 40 }); };
  const autoLayout = () => { const positioned = nodes.map((n, index) => ({ ...n, position: { x: 80 + (index % 4) * 300, y: 100 + Math.floor(index / 4) * 180 } })); commit(positioned, edges); flowRef.current?.fitView({ padding: 0.2 }); };
  const validateLocal = () => {
    const errors: string[] = [];
    if (!nodes.some((n) => n.data.type.toLowerCase().includes('trigger'))) errors.push('Add at least one trigger node.');
    if (!nodes.length) errors.push('Add at least one node.');
    const indegree = new Map(nodes.map((n) => [n.id, 0])); edges.forEach((e) => indegree.set(e.target, (indegree.get(e.target) || 0) + 1));
    if (nodes.length && [...indegree.values()].every((value) => value > 0)) errors.push('Graph must have a starting node.');
    const result = { ok: errors.length === 0, errors }; setValidation(result); return result;
  };
  const save = async () => { setStatus('Saving...'); try { const graph = graphFrom(nodes, edges, viewport); let id = workflowId; if (id) await api.updateWorkflow(id, { name: workflowName, graph }); else { const result = await api.createWorkflow(workflowName, 'Saved from Workflow Studio', graph); id = result.id; setWorkflowId(id); } setStatus('Saved'); return id; } catch { setStatus('Error saving'); setNotice('Could not save workflow.'); return null; } };
  const validate = async () => {
    const local = validateLocal();
    if (!local.ok) { setValidation(local); return local; }
    const id = await save();
    if (!id) return { ok: false, errors: ['Save the workflow before validating it.'] };
    try {
      const result = await api.validateWorkflow(id);
      const mapped = { ok: result.is_valid, errors: result.errors };
      setValidation(mapped);
      return mapped;
    } catch (error) {
      const mapped = { ok: false, errors: [error instanceof Error ? error.message : 'Validation failed.'] };
      setValidation(mapped);
      return mapped;
    }
  };
  const execute = async (test = false) => { const result = await validate(); if (!result.ok) return; const id = await save(); if (!id) return; if (test) { setNotice('Test passed: workflow is valid and ready to execute.'); return; } try { const execution = await api.executeWorkflow(id); setNotice(`Execution dispatched: ${execution.id.slice(0, 8)}`); } catch (error: unknown) { setNotice(error instanceof Error ? error.message : 'Execution failed.'); } };
  const onDrop = (event: React.DragEvent) => { event.preventDefault(); const type = draggingType.current; const item = PALETTE.find((p) => p.type === type); if (!item || !flowRef.current) return; addNode(item.type, item.label, flowRef.current.screenToFlowPosition({ x: event.clientX, y: event.clientY })); draggingType.current = null; };

  return <div className="h-[calc(100vh-4rem)] flex flex-col bg-[#080F20] text-[#F1F6FF] overflow-hidden">
    <div className="h-14 px-5 border-b border-[rgba(67,139,255,0.15)] bg-[#0C1629]/80 backdrop-blur-xl flex items-center justify-between shrink-0 shadow-[0_4px_20px_rgba(4,9,20,0.4)]">
      <div className="flex items-center gap-3">
        <input
          aria-label="Workflow name"
          value={workflowName}
          onChange={(e) => { setWorkflowName(e.target.value); setStatus('Unsaved changes'); }}
          className="text-sm font-semibold bg-transparent border-b border-transparent focus:border-[#438BFF] focus:outline-none px-1 py-0.5 text-[#F1F6FF]"
        />
        <span className="text-xs text-[#7285A5]">{status}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <button title="Undo" onClick={undo} disabled={!history.length} className="toolbar"><Undo2 /></button>
        <button title="Redo" onClick={redo} disabled={!future.length} className="toolbar"><Redo2 /></button>
        <button title="Auto-layout" onClick={autoLayout} className="toolbar"><LayoutTemplate /></button>
        <button onClick={() => { void validate(); }} className="action"><CheckCircle />Validate</button>
        <button onClick={() => { void save(); }} className="action"><Save />Save</button>
        <button onClick={() => { void execute(true); }} className="action"><TestTube2 />Test</button>
        <button onClick={async () => { const id = workflowId || await save(); if (!id) return; try { await api.publishWorkflow(id, 'Published from Workflow Studio'); setNotice('Workflow published successfully.'); } catch (error) { setNotice(error instanceof Error ? error.message : 'Publish failed.'); } }} className="action"><Upload />Publish</button>
        <button onClick={() => { void execute(); }} className="primary"><Play />Execute</button>
      </div>
    </div>
    <div className="flex-1 flex overflow-hidden">
      <aside className="w-64 border-r border-[rgba(67,139,255,0.15)] bg-[#0C1629]/75 backdrop-blur-xl p-4 flex flex-col gap-4 shrink-0 shadow-[inset_-1px_0_1px_rgba(255,255,255,0.05)]">
        <div className="text-xs font-semibold text-[#A3B4CF] tracking-wider uppercase">Node Library</div>
        <div className="relative"><Search className="icon" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search nodes..." className="search" /></div>
        <div className="flex-1 overflow-y-auto space-y-2">{CATEGORIES.map((category) => { const items = selectedItems.filter((p) => p.category === category); if (!items.length) return null; const open = openCategories[category]; return <div key={category}><button onClick={() => setOpenCategories((c) => ({ ...c, [category]: !c[category] }))} className="category">{open ? <ChevronDown /> : <ChevronRight />}{category}<span>{items.length}</span></button>{open && items.map((item) => <button key={item.type} draggable onDragStart={() => { draggingType.current = item.type; }} onClick={() => addNode(item.type, item.label)} className="palette-item"><GripVertical /><span>{item.label}</span><span className="text-[#53D7F5]">+</span></button>)}</div>; })}</div>
      </aside>
      <main className="flex-1 relative" onDrop={onDrop} onDragOver={(e) => e.preventDefault()}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onInit={(instance) => { flowRef.current = instance; }}
          onMove={(_, next) => setViewport(next)}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, n) => setSelectedId(n.id)}
          onPaneClick={() => setSelectedId(null)}
          nodeTypes={nodeTypes}
          defaultViewport={viewport}
          fitView={false}
          deleteKeyCode={null}
        >
          <Background color="#172743" gap={20} size={1.5} />
          <Controls className="!bg-[#0C1629]/80 !backdrop-blur-md !border-[rgba(67,139,255,0.2)] !fill-[#F1F6FF] shadow-xl" />
          <MiniMap nodeColor="#438BFF" maskColor="rgba(8, 15, 32, 0.75)" className="!bg-[#0C1629]/80 !backdrop-blur-md !border-[rgba(67,139,255,0.2)] shadow-xl" />
        </ReactFlow>
        {validation && <div className={`absolute bottom-4 left-4 p-3 rounded-2xl border text-xs flex items-center gap-2 backdrop-blur-xl shadow-2xl ${validation.ok ? 'bg-[#28C995]/15 border-[#28C995]/35 text-[#28C995]' : 'bg-[#F16B7A]/15 border-[#F16B7A]/35 text-[#F16B7A]'}`}>{validation.ok ? <Check /> : <AlertTriangle />}{validation.ok ? 'Workflow is valid.' : validation.errors.join(' ') }<button onClick={() => setValidation(null)}><X /></button></div>}
        {notice && <button onClick={() => setNotice(null)} className="absolute top-4 right-4 z-10 rounded-xl bg-[#0C1629]/90 backdrop-blur-xl border border-[rgba(67,139,255,0.25)] px-3 py-2 text-xs text-[#F1F6FF] shadow-2xl">{notice}</button>}
      </main>
      <aside className="w-80 border-l border-[rgba(67,139,255,0.15)] bg-[#0C1629]/75 backdrop-blur-xl p-5 shrink-0 overflow-y-auto shadow-[inset_1px_0_1px_rgba(255,255,255,0.05)]">
        <div className="flex items-center justify-between border-b border-[rgba(67,139,255,0.15)] pb-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#A3B4CF] uppercase tracking-wider"><Settings2 className="w-4 text-[#438BFF]" />Inspector</div>
          {selectedNode && <div className="flex gap-1"><button title="Duplicate" onClick={duplicateSelected} className="icon-button"><Copy /></button><button title="Delete" onClick={deleteSelected} className="icon-button"><Trash2 /></button></div>}
        </div>
        {selectedNode ? <Inspector node={selectedNode} onChange={(data) => { commit(nodes.map((n) => n.id === selectedNode.id ? { ...n, data } : n), edges); }} /> : <div className="text-center py-12 text-xs text-[#7285A5]">Select a node to configure its parameters.</div>}
      </aside>
    </div>
    <style jsx>{`.toolbar,.action,.primary,.icon-button{display:flex;align-items:center;gap:6px;border-radius:10px;font-size:12px;padding:7px 11px;transition:all .2s ease}.toolbar{background:#111E35;border:1px solid rgba(67,139,255,.18);color:#A3B4CF}.toolbar:hover:not(:disabled){background:#172743;color:#F1F6FF;border-color:rgba(83,215,245,.35)}.toolbar svg{width:14px}.toolbar:disabled{opacity:.35}.action{color:#A3B4CF;background:#111E35;border:1px solid rgba(67,139,255,.18)}.action:hover{color:#F1F6FF;background:#172743;border-color:rgba(83,215,245,.35);box-shadow:0 0 12px rgba(67,139,255,.15)}.action svg,.primary svg{width:14px}.primary{background:linear-gradient(135deg,#287BFA 0%,#438BFF 100%);color:white;font-weight:600;border:1px solid rgba(255,255,255,.2);box-shadow:0 4px 16px rgba(40,123,250,.35)}.primary:hover{background:linear-gradient(135deg,#3786FF 0%,#53D7F5 100%);box-shadow:0 6px 20px rgba(67,139,255,.45);transform:translateY(-1px)}.icon{position:absolute;left:10px;top:9px;width:14px;color:#7285A5}.search{width:100%;padding:7px 10px 7px 31px;border-radius:10px;background:#111E35;border:1px solid rgba(67,139,255,.18);color:#F1F6FF;font-size:12px;outline:none;transition:border-color .2s}.search:focus{border-color:#438BFF;box-shadow:0 0 12px rgba(67,139,255,.25)}.category{width:100%;display:flex;align-items:center;gap:5px;padding:5px 2px;color:#7285A5;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em}.category svg{width:13px}.category span{margin-left:auto}.palette-item{width:100%;display:flex;align-items:center;gap:7px;padding:9px;border-radius:10px;background:#111E35;border:1px solid rgba(67,139,255,.12);text-align:left;font-size:12px;color:#F1F6FF;transition:all .2s ease}.palette-item:hover{background:#172743;border-color:rgba(83,215,245,.3);transform:translateY(-1px);box-shadow:0 4px 12px rgba(4,9,20,.3)}.palette-item svg{width:13px;color:#7285A5}.palette-item span:nth-child(2){flex:1}.icon-button{padding:5px;color:#7285A5;border-radius:6px;transition:all .2s}.icon-button:hover{color:#53D7F5;background:#172743}.icon-button svg{width:15px}`}</style>
  </div>;
}

function Inspector({ node, onChange }: { node: StudioNode; onChange: (data: StudioNode['data']) => void }) {
  const config = node.data.config || {};
  const setConfig = (key: string, value: unknown) => onChange({ ...node.data, config: { ...config, [key]: value } });
  const requiredFields: Record<string, string[]> = { llmCompletion: ['prompt'], scheduleTrigger: ['cron'], httpIntegration: ['url'], transform: ['mapping'] };
  const configErrors = (requiredFields[node.data.type] || []).filter((key) => config[key] === undefined || config[key] === '');
  const fields: Record<string, { key: string; label: string; type?: string }[]> = {
    scheduleTrigger: [{ key: 'cron', label: 'Cron expression' }], gmailTrigger: [{ key: 'folder', label: 'Folder' }, { key: 'unread_only', label: 'Unread only', type: 'checkbox' }], aiAgent: [{ key: 'task', label: 'Task' }, { key: 'role', label: 'Role' }, { key: 'tone', label: 'Tone' }, { key: 'max_iterations', label: 'Maximum iterations', type: 'number' }], llmCompletion: [{ key: 'provider', label: 'Provider' }, { key: 'model', label: 'Model' }, { key: 'system_prompt', label: 'System instructions' }, { key: 'prompt', label: 'User prompt' }, { key: 'temperature', label: 'Temperature', type: 'number' }, { key: 'output_format', label: 'Output format' }], textClassifier: [{ key: 'provider', label: 'Provider' }, { key: 'text', label: 'Input text' }, { key: 'categories', label: 'Categories (JSON)' }], textSummarizer: [{ key: 'provider', label: 'Provider' }, { key: 'text', label: 'Input text' }, { key: 'summary_length', label: 'Summary length' }], dataExtractor: [{ key: 'provider', label: 'Provider' }, { key: 'fields', label: 'Fields (JSON)' }], informationExtractor: [{ key: 'provider', label: 'Provider' }, { key: 'schema', label: 'Output schema (JSON)' }], aiDecision: [{ key: 'provider', label: 'Provider' }, { key: 'criteria', label: 'Decision criteria' }], delay: [{ key: 'seconds', label: 'Delay (seconds)', type: 'number' }], httpIntegration: [{ key: 'url', label: 'Request URL' }, { key: 'method', label: 'Method' }], humanApproval: [{ key: 'timeout_hours', label: 'Timeout (hours)', type: 'number' }],
  };
  const nodeFields = fields[node.data.type] || [];
  return <div className="space-y-4 pt-4"><label className="block text-[11px] text-[#A3B4CF]">Display label<input value={node.data.label} onChange={(e) => onChange({ ...node.data, label: e.target.value })} className="field" /></label>{nodeFields.map((field) => <label key={field.key} className="block text-[11px] text-[#A3B4CF]">{field.label}<input type={field.type || 'text'} checked={field.type === 'checkbox' ? Boolean(config[field.key]) : undefined} value={field.type === 'checkbox' ? undefined : String(config[field.key] ?? '')} onChange={(e) => setConfig(field.key, field.type === 'checkbox' ? e.target.checked : field.type === 'number' ? Number(e.target.value) : e.target.value)} className={`field ${configErrors.includes(field.key) ? 'invalid' : ''}`} />{configErrors.includes(field.key) && <span className="error">Required for this node.</span>}</label>)}<label className="block text-[11px] text-[#A3B4CF]">Configuration JSON<textarea rows={7} value={JSON.stringify(config, null, 2)} onChange={(e) => { try { onChange({ ...node.data, config: JSON.parse(e.target.value) }); } catch {} }} className="field font-mono" /></label><style jsx>{`.field{display:block;width:100%;margin-top:5px;padding:7px 9px;border-radius:10px;background:#111E35;border:1px solid rgba(67,139,255,.18);color:#F1F6FF;font-size:12px;outline:none;transition:border-color .2s}.field:focus{border-color:#438BFF;box-shadow:0 0 12px rgba(67,139,255,.25)}.invalid{border-color:#F16B7A}.error{display:block;margin-top:3px;color:#F16B7A;font-size:10px}`}</style></div>;
}
