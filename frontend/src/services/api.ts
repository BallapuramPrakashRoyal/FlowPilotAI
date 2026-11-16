import {
  User,
  Workspace,
  Workflow,
  WorkflowGraph,
  Execution,
  Approval,
  Integration,
  AnalyticsOverview,
  WorkflowVersion,
  ExecutionEvent,
  AIConfig,
  AIProvider,
  AgentRun,
  WorkflowTemplate,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;
  private currentWorkspaceId: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('flowpilot_token');
      this.currentWorkspaceId = localStorage.getItem('flowpilot_workspace_id');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('flowpilot_token', token);
    }
  }

  getToken() {
    return this.token;
  }

  clearSession() {
    this.token = null;
    this.currentWorkspaceId = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('flowpilot_token');
      localStorage.removeItem('flowpilot_workspace_id');
    }
  }

  setWorkspaceId(id: string) {
    this.currentWorkspaceId = id;
    if (typeof window !== 'undefined') {
      localStorage.setItem('flowpilot_workspace_id', id);
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryAfterUnauthorized = true,
  ): Promise<T> {
    if (this.token && !this.currentWorkspaceId && !endpoint.includes('/workspaces')) {
      try {
        const wsRes = await fetch(`${API_BASE}/api/v1/workspaces/`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        if (wsRes.ok) {
          const wsList = await wsRes.json();
          if (wsList && wsList.length > 0) {
            this.setWorkspaceId(wsList[0].id);
          }
        }
      } catch (e) {
        console.warn('Workspace discovery skipped:', e);
      }
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    if (this.currentWorkspaceId) {
      headers['X-Workspace-ID'] = this.currentWorkspaceId;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401 && retryAfterUnauthorized && !endpoint.includes('/auth/')) {
      this.token = null;
      this.currentWorkspaceId = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('flowpilot_token');
        localStorage.removeItem('flowpilot_workspace_id');
      }
      return this.request<T>(endpoint, options, false);
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }

    return res.json();
  }

  // Auth
  async login(email: string, password: string):Promise<{ access_token: string; user: User }> {
    const data = await this.request<{ access_token: string; user: User }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async register(
    email: string,
    password: string,
    fullName: string,
  ): Promise<{ access_token: string; user: User }> {
    const data = await this.request<{ access_token: string; user: User }>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async logout() {
    try {
      await this.request<{ message: string }>('/api/v1/auth/logout', { method: 'POST' }, false);
    } finally {
      this.clearSession();
    }
  }

  async getMe(): Promise<User> {
    return this.request<User>('/api/v1/auth/me');
  }

  // Workspaces
  async listWorkspaces(): Promise<Workspace[]> {
    return this.request<Workspace[]>('/api/v1/workspaces/');
  }

  // Workflows
  async listWorkflows(): Promise<Workflow[]> {
    return this.request<Workflow[]>('/api/v1/workflows/');
  }

  async getWorkflow(id: string): Promise<Workflow> {
    return this.request<Workflow>(`/api/v1/workflows/${id}`);
  }

  async createWorkflow(name: string, description?: string, graph?: WorkflowGraph): Promise<Workflow> {
    return this.request<Workflow>('/api/v1/workflows/', {
      method: 'POST',
      body: JSON.stringify({
        name,
        description,
        workspace_id: this.currentWorkspaceId || 'default',
        graph,
      }),
    });
  }

  async listTemplates(): Promise<WorkflowTemplate[]> {
    return this.request<WorkflowTemplate[]>('/api/v1/workflows/templates');
  }

  async instantiateTemplate(templateId: string): Promise<Workflow> {
    return this.request<Workflow>(`/api/v1/workflows/templates/${templateId}/instantiate`, {
      method: 'POST',
    });
  }

  async updateWorkflow(id: string, payload: Partial<Workflow> & { graph?: WorkflowGraph }): Promise<Workflow> {
    return this.request<Workflow>(`/api/v1/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async validateWorkflow(id: string): Promise<{
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    execution_order: string[];
  }> {
    return this.request(`/api/v1/workflows/${id}/validate`, { method: 'POST' });
  }

  async publishWorkflow(id: string, changelog?: string): Promise<Workflow> {
    return this.request<Workflow>(`/api/v1/workflows/${id}/publish`, {
      method: 'POST',
      body: JSON.stringify({ changelog }),
    });
  }

  async listWorkflowVersions(id: string) {
    return this.request<WorkflowVersion[]>(`/api/v1/workflows/${id}/versions`);
  }

  async generateWorkflowAI(prompt: string): Promise<{
    name: string;
    description: string;
    explanation: string;
    suggested_integrations: string[];
    graph: WorkflowGraph;
  }> {
    return this.request('/api/v1/workflows/generate', {
      method: 'POST',
      body: JSON.stringify({ workspace_id: this.currentWorkspaceId || 'default', prompt }),
    });
  }

  async executeWorkflow(id: string): Promise<Execution> {
    return this.request<Execution>(`/api/v1/workflows/${id}/execute`, {
      method: 'POST',
    });
  }

  // Executions
  async listExecutions(): Promise<Execution[]> {
    return this.request<Execution[]>('/api/v1/executions/');
  }

  async getExecution(id: string): Promise<Execution> {
    return this.request<Execution>(`/api/v1/executions/${id}`);
  }

  async listExecutionEvents(id: string): Promise<ExecutionEvent[]> {
    return this.request<ExecutionEvent[]>(`/api/v1/executions/${id}/events`);
  }

  async listAgentRuns(id: string): Promise<AgentRun[]> {
    return this.request<AgentRun[]>(`/api/v1/agents/runs/${id}`);
  }

  // AI configuration and provider metadata
  async getAIConfig(): Promise<AIConfig> {
    return this.request<AIConfig>('/api/v1/ai/config');
  }

  async updateAIConfig(payload: {
    default_provider: string;
    default_model: string;
    api_key?: string;
    request_limit?: number;
    daily_token_limit?: number;
    sensitive_fields?: string[];
  }): Promise<AIConfig> {
    return this.request<AIConfig>('/api/v1/ai/config', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async listAIProviders(): Promise<AIProvider[]> {
    return this.request<AIProvider[]>('/api/v1/ai/providers');
  }

  // Approvals
  async listApprovals(status: string = 'PENDING'): Promise<Approval[]> {
    return this.request<Approval[]>(`/api/v1/approvals/?status_filter=${status}`);
  }

  async decideApproval(id: string, decision: 'APPROVED' | 'REJECTED', notes?: string, edited?: any): Promise<Approval> {
    return this.request<Approval>(`/api/v1/approvals/${id}/decide`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        decision_notes: notes,
        edited_proposal: edited,
      }),
    });
  }

  async getIntegrationConfig(): Promise<any> {
    return this.request('/api/v1/integrations/config');
  }

  async cancelExecution(id: string): Promise<{ status: string }> {
    return this.request(`/api/v1/executions/${id}/cancel`, {
      method: 'POST',
    });
  }

  async cancelAgentRun(id: string): Promise<{ status: string }> {
    return this.request(`/api/v1/agents/runs/${id}/cancel`, {
      method: 'POST',
    });
  }

  async resumeAgentRun(id: string): Promise<any> {
    return this.request(`/api/v1/agents/runs/${id}/resume`, {
      method: 'POST',
    });
  }

  // Integrations
  async listIntegrations(): Promise<Integration[]> {
    return this.request<Integration[]>('/api/v1/integrations/');
  }

  async connectIntegration(provider: string, authCode?: string): Promise<Integration> {
    return this.request<Integration>('/api/v1/integrations/connect', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: this.currentWorkspaceId || 'default',
        provider,
        auth_code: authCode,
      }),
    });
  }

  async disconnectIntegration(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/integrations/${id}`, {
      method: 'DELETE',
    });
  }

  async getGmailPreview(): Promise<{ unread_count: number; sample_threads: any[] }> {
    return this.request('/api/v1/integrations/gmail/preview');
  }

  // Knowledge Base
  async listKnowledgeBases(): Promise<any[]> {
    return this.request<any[]>('/api/v1/knowledge-bases/');
  }

  async queryRAG(knowledgeBaseId: string, query: string): Promise<{ query: string; citations: any[] }> {
    return this.request('/api/v1/knowledge-bases/query', {
      method: 'POST',
      body: JSON.stringify({
        knowledge_base_id: knowledgeBaseId,
        query,
      }),
    });
  }

  // Analytics
  async getAnalytics(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>('/api/v1/analytics/overview');
  }
}

export const api = new ApiClient();
