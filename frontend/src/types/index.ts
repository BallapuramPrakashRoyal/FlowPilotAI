export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
  role?: string;
}

export interface WorkflowNodeData {
  id: string;
  type: string;
  label: string;
  position: { x: number; y: number };
  config: Record<string, any>;
}

export interface WorkflowEdgeData {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface WorkflowGraph {
  nodes: WorkflowNodeData[];
  edges: WorkflowEdgeData[];
  viewport?: { x: number; y: number; zoom: number };
}

export interface Workflow {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  current_version_id?: string;
  graph?: WorkflowGraph;
  created_at: string;
  updated_at: string;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version_number: number;
  graph_data: WorkflowGraph;
  is_published: boolean;
  changelog?: string;
  created_at: string;
}

export interface ExecutionNode {
  id: string;
  node_id: string;
  node_type: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'SKIPPED';
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  retry_count: number;
}

export interface ExecutionEvent {
  id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface AgentRun {
  id: string;
  task_id?: string;
  agent_role: string;
  status: string;
  token_count: number;
  latency_ms: number;
  retry_count?: number;
  provider?: string;
  model?: string;
  tools_called: (string | Record<string, any>)[];
  task_input: Record<string, any>;
  task_output: Record<string, any>;
  handoff_data: Record<string, any>;
  validation_findings?: string[];
  approval_status?: string;
  error_message?: string;
  created_at: string;
}

export interface Execution {
  id: string;
  workspace_id: string;
  workflow_id: string;
  workflow_version_id: string;
  status: 'PENDING' | 'QUEUED' | 'RUNNING' | 'WAITING_APPROVAL' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  trigger_type: string;
  context_data: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  token_usage: Record<string, any>;
  nodes?: ExecutionNode[];
  events?: ExecutionEvent[];
}

export interface AIConfig {
  workspace_id: string;
  default_provider: string;
  default_model: string;
  request_limit: number;
  daily_token_limit: number;
  sensitive_fields: string[];
}

export interface AIProvider {
  id: string;
  configured: boolean;
  models: string[];
}

export interface Approval {
  id: string;
  workspace_id: string;
  execution_id: string;
  execution_node_id: string;
  action_type: string;
  title: string;
  proposal_data: Record<string, any>;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EDITED';
  decided_by?: string;
  decision_notes?: string;
  decided_at?: string;
  created_at: string;
}

export interface Integration {
  id: string;
  workspace_id: string;
  provider: 'GMAIL' | 'GITHUB' | 'SLACK';
  is_connected: boolean;
  account_email?: string;
  status_message?: string;
  scopes?: string[];
  created_at: string;
  updated_at: string;
}

export interface IntegrationConfig {
  google_oauth_configured: boolean;
  google_client_id_configured: boolean;
  google_redirect_uri: string;
  scopes: string[];
  setup_instructions: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  badge?: string;
  nodes: WorkflowNodeData[];
  edges: WorkflowEdgeData[];
}

export interface AnalyticsOverview {
  total_workflows: number;
  active_workflows: number;
  total_executions?: number;
  successful_executions: number;
  failed_executions: number;
  success_rate_percent?: number;
  failure_rate_percent?: number;
  pending_approvals: number;
  avg_duration_ms: number;
  total_tokens_consumed: number;
  estimated_cost_usd: number;
  connected_integrations_count?: number;
  connected_integrations?: { id: string; provider: string; account_email?: string; connected_at?: string }[];
  recent_agent_runs?: { id: string; task_id?: string; agent_role: string; status: string; token_count: number; latency_ms: number; provider?: string; model?: string; started_at: string }[];
  recent_audit_logs?: { id: string; action: string; resource_type: string; resource_id?: string; details: Record<string, any>; created_at: string }[];
  execution_trends: { date: string; executions: number; successes: number; failures: number }[];
  recent_activity: { id: string; workflow_name: string; status: string; started_at: string; duration_ms: number }[];
}
