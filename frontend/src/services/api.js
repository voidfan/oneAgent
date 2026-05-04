import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - inject auth token and tenant ID
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Inject current tenant ID
    const tenantId = localStorage.getItem('current_tenant_id');
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败';
    console.error('[API Error]', message);
    return Promise.reject({ message, status: error.response?.status });
  }
);

// ==================== Chat API ====================

export const chatAPI = {
  // Send message (non-streaming)
  sendMessage: (data) => api.post('/chat', data),

  // Send message (streaming)
  sendMessageStream: async function* (data) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(localStorage.getItem('auth_token')
          ? { Authorization: `Bearer ${localStorage.getItem('auth_token')}` }
          : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            yield JSON.parse(data);
          } catch {
            yield { type: 'text', content: data };
          }
        }
      }
    }
  },

  // Get conversations
  getConversations: (skip = 0, limit = 50) =>
    api.get('/chat/conversations', { params: { skip, limit } }),

  // Get conversation by ID
  getConversation: (id) => api.get(`/chat/conversations/${id}`),

  // Delete conversation
  deleteConversation: (id) => api.delete(`/chat/conversations/${id}`),
};

// ==================== Agent API ====================

export const agentAPI = {
  // List agents
  list: (skip = 0, limit = 50) =>
    api.get('/agents', { params: { skip, limit } }),

  // Get agent by ID
  get: (id) => api.get(`/agents/${id}`),

  // Create agent
  create: (data) => api.post('/agents', data),

  // Update agent
  update: (id, data) => api.put(`/agents/${id}`, data),

  // Delete agent
  delete: (id) => api.delete(`/agents/${id}`),

  // Get agent executions
  getExecutions: (id, skip = 0, limit = 20) =>
    api.get(`/agents/${id}/executions`, { params: { skip, limit } }),
};

// ==================== Tool API ====================

export const toolAPI = {
  // 获取支持的工具类型
  getTypes: () => api.get('/tools/types'),

  // CRUD
  list: (params) => api.get('/tools', { params }),
  get: (id) => api.get(`/tools/${id}`),
  create: (data) => api.post('/tools', data),
  update: (id, data) => api.put(`/tools/${id}`, data),
  delete: (id) => api.delete(`/tools/${id}`),

  // 执行工具
  execute: (data) => api.post('/tools/execute', data),

  // 连通性测试
  testConnection: (id) => api.post(`/tools/${id}/test`),
  testConfig: (data) => api.post('/tools/test-config', data),
  batchTest: () => api.post('/tools/batch-test'),

  // 切换启用/禁用
  toggle: (id) => api.patch(`/tools/${id}/toggle`),
};

// ==================== System API ====================

export const systemAPI = {
  // Health check
  health: () => api.get('/system/health'),

  // System stats
  stats: () => api.get('/system/stats'),

  // Get traces
  traces: (limit = 100) => api.get('/system/traces', { params: { limit } }),

  // Get metrics (Prometheus format)
  metrics: () => fetch(`${API_BASE}/system/metrics`).then((r) => r.text()),
};

// ==================== Settings API ====================

export const settingsAPI = {
  // Get all settings
  getAll: () => api.get('/settings'),

  // Get settings section
  getSection: (section) => api.get(`/settings/${section}`),

  // Update settings section
  updateSection: (section, data) => api.put(`/settings/${section}`, data),

  // Reset all settings
  reset: () => api.post('/settings/reset'),

  // Get all supported LLM providers with metadata
  getProviders: () => api.get('/settings/providers'),

  // Get provider info
  getProviderInfo: (providerId) => api.get(`/settings/providers/${providerId}`),

  // Get available models for provider
  getProviderModels: (providerId) => api.get(`/settings/providers/${providerId}/models`),

  // Test LLM connection
  testLLM: (provider, apiKey, baseUrl, model) =>
    api.post('/settings/test-llm', null, {
      params: { provider, api_key: apiKey, base_url: baseUrl, model },
    }),

  // Get available models for provider (legacy)
  getModels: (provider) => api.get(`/settings/llm/models/${provider}`),
};

// ==================== Tenant API ====================

export const tenantAPI = {
  // List all tenants
  list: () => api.get('/tenants'),

  // Create tenant
  create: (data) => api.post('/tenants', data),

  // Get tenant by ID
  get: (id) => api.get(`/tenants/${id}`),

  // Update tenant
  update: (id, data) => api.put(`/tenants/${id}`, data),

  // Delete tenant
  delete: (id) => api.delete(`/tenants/${id}`),

  // Get tenant settings
  getSettings: (id) => api.get(`/tenants/${id}/settings`),

  // Update tenant settings
  updateSettings: (id, data) => api.put(`/tenants/${id}/settings`, data),

  // ---- Tenant Tools ----
  listTools: (id) => api.get(`/tenants/${id}/tools`),
  createTool: (id, data) => api.post(`/tenants/${id}/tools`, data),
  deleteTool: (tenantId, toolId) => api.delete(`/tenants/${tenantId}/tools/${toolId}`),

  // ---- Tenant MCP ----
  listMCP: (id) => api.get(`/tenants/${id}/mcp`),
  createMCP: (id, data) => api.post(`/tenants/${id}/mcp`, data),
  deleteMCP: (tenantId, mcpId) => api.delete(`/tenants/${tenantId}/mcp/${mcpId}`),

  // ---- Tenant Skills ----
  listSkills: (id) => api.get(`/tenants/${id}/skills`),
  createSkill: (id, data) => api.post(`/tenants/${id}/skills`, data),
  deleteSkill: (tenantId, skillId) => api.delete(`/tenants/${tenantId}/skills/${skillId}`),

  // ---- Tenant Contexts ----
  listContexts: (id) => api.get(`/tenants/${id}/contexts`),
  createContext: (id, data) => api.post(`/tenants/${id}/contexts`, data),
  deleteContext: (tenantId, contextId) => api.delete(`/tenants/${tenantId}/contexts/${contextId}`),
};

export default api;


// ── Workflow API ──────────────────────────────────────────────────────────────
export const workflowAPI = {
  list: () => api.get('/workflows'),
  get: (id) => api.get(`/workflows/${id}`),
  getBySlug: (slug) => api.get(`/workflows/by-slug/${slug}`),
  create: (data) => api.post('/workflows', data),
  update: (id, data) => api.put(`/workflows/${id}`, data),
  delete: (id) => api.delete(`/workflows/${id}`),
  chat: (id, data) => api.post(`/workflows/${id}/chat`, data),

  // 发布/取消发布
  publish: (id, isPublic = true) => api.post(`/workflows/${id}/publish`, { is_public: isPublic }),

  // 公开应用访问（无需认证）
  getPublic: (slug) => api.get(`/workflows/public/${slug}`),
  publicChat: (slug, data) => api.post(`/workflows/public/${slug}/chat`, data),
};
