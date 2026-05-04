import { create } from 'zustand';
import { chatAPI, agentAPI, toolAPI, systemAPI, settingsAPI, tenantAPI } from '../services/api';

// ==================== Chat Store ====================
export const useChatStore = create((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  error: null,

  // Load conversations
  loadConversations: async () => {
    try {
      const data = await chatAPI.getConversations();
      set({ conversations: data });
    } catch (err) {
      set({ error: err.message });
    }
  },

  // Select conversation
  selectConversation: async (id) => {
    try {
      const data = await chatAPI.getConversation(id);
      set({
        currentConversation: data,
        messages: data.messages || [],
      });
    } catch (err) {
      set({ error: err.message });
    }
  },

  // New conversation
  newConversation: () => {
    set({
      currentConversation: null,
      messages: [],
    });
  },

  // Send message (streaming)
  sendMessage: async (content, agentId = null) => {
    const { messages, currentConversation } = get();

    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    const assistantMessage = {
      id: `temp-assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    };

    set({
      messages: [...messages, userMessage, assistantMessage],
      isStreaming: true,
      error: null,
    });

    try {
      const requestData = {
        message: content,
        conversation_id: currentConversation?.id || null,
        agent_id: agentId,
        stream: true,
      };

      let fullContent = '';

      for await (const chunk of chatAPI.sendMessageStream(requestData)) {
        if (chunk.type === 'text' || chunk.content) {
          fullContent += chunk.content || '';
          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: fullContent }
                : m
            ),
          }));
        } else if (chunk.type === 'tool_call') {
          fullContent += `\n\n🔧 调用工具: ${chunk.tool_name}\n`;
          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: fullContent }
                : m
            ),
          }));
        } else if (chunk.type === 'thinking') {
          // Could display thinking process
        } else if (chunk.conversation_id) {
          set({ currentConversation: { id: chunk.conversation_id } });
        }
      }

      set({ isStreaming: false });
      // Reload conversations list
      get().loadConversations();
    } catch (err) {
      set((state) => ({
        isStreaming: false,
        error: err.message,
        messages: state.messages.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: `❌ 错误: ${err.message}` }
            : m
        ),
      }));
    }
  },

  // Send message (non-streaming fallback)
  sendMessageSync: async (content, agentId = null) => {
    const { messages, currentConversation } = get();

    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    set({
      messages: [...messages, userMessage],
      isLoading: true,
      error: null,
    });

    try {
      const data = await chatAPI.sendMessage({
        message: content,
        conversation_id: currentConversation?.id || null,
        agent_id: agentId,
      });

      const assistantMessage = {
        id: data.message_id || `resp-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        created_at: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
        currentConversation: { id: data.conversation_id },
      }));

      get().loadConversations();
    } catch (err) {
      set({ isLoading: false, error: err.message });
    }
  },

  // Delete conversation
  deleteConversation: async (id) => {
    try {
      await chatAPI.deleteConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        ...(state.currentConversation?.id === id
          ? { currentConversation: null, messages: [] }
          : {}),
      }));
    } catch (err) {
      set({ error: err.message });
    }
  },

  clearError: () => set({ error: null }),
}));

// ==================== Agent Store ====================
export const useAgentStore = create((set, get) => ({
  agents: [],
  currentAgent: null,
  executions: [],
  isLoading: false,
  error: null,

  loadAgents: async () => {
    set({ isLoading: true });
    try {
      const data = await agentAPI.list();
      set({ agents: data, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  getAgent: async (id) => {
    try {
      const data = await agentAPI.get(id);
      set({ currentAgent: data });
      return data;
    } catch (err) {
      set({ error: err.message });
    }
  },

  createAgent: async (agentData) => {
    try {
      const data = await agentAPI.create(agentData);
      set((state) => ({ agents: [...state.agents, data] }));
      return data;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  updateAgent: async (id, agentData) => {
    try {
      const data = await agentAPI.update(id, agentData);
      set((state) => ({
        agents: state.agents.map((a) => (a.id === id ? data : a)),
        currentAgent: state.currentAgent?.id === id ? data : state.currentAgent,
      }));
      return data;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  deleteAgent: async (id) => {
    try {
      await agentAPI.delete(id);
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== id),
        currentAgent: state.currentAgent?.id === id ? null : state.currentAgent,
      }));
    } catch (err) {
      set({ error: err.message });
    }
  },

  loadExecutions: async (agentId) => {
    try {
      const data = await agentAPI.getExecutions(agentId);
      set({ executions: data });
    } catch (err) {
      set({ error: err.message });
    }
  },

  clearError: () => set({ error: null }),
}));

// ==================== Tool Store ====================
export const useToolStore = create((set, get) => ({
  tools: [],
  toolTypes: {},
  isLoading: false,
  error: null,

  // 加载工具列表
  loadTools: async (params) => {
    set({ isLoading: true });
    try {
      const data = await toolAPI.list(params);
      set({ tools: data, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // 加载工具类型定义
  loadToolTypes: async () => {
    try {
      const data = await toolAPI.getTypes();
      set({ toolTypes: data.types || {} });
    } catch (err) {
      set({ error: err.message });
    }
  },

  // 创建工具
  createTool: async (data) => {
    try {
      const tool = await toolAPI.create(data);
      set((state) => ({ tools: [tool, ...state.tools] }));
      return tool;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 更新工具
  updateTool: async (id, data) => {
    try {
      const tool = await toolAPI.update(id, data);
      set((state) => ({
        tools: state.tools.map((t) => (t.id === id ? tool : t)),
      }));
      return tool;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 删除工具
  deleteTool: async (id) => {
    try {
      await toolAPI.delete(id);
      set((state) => ({
        tools: state.tools.filter((t) => t.id !== id),
      }));
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 执行工具
  executeTool: async (data) => {
    try {
      const result = await toolAPI.execute(data);
      return result;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 测试连通性
  testConnection: async (id) => {
    try {
      const result = await toolAPI.testConnection(id);
      // 更新工具的健康状态
      set((state) => ({
        tools: state.tools.map((t) =>
          t.id === id
            ? { ...t, health_status: result.success ? 'healthy' : 'unhealthy', health_message: result.message }
            : t
        ),
      }));
      return result;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 测试配置（不需要先创建工具）
  testConfig: async (type, config) => {
    try {
      return await toolAPI.testConfig({ type, config });
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 切换启用/禁用
  toggleTool: async (id) => {
    try {
      const tool = await toolAPI.toggle(id);
      set((state) => ({
        tools: state.tools.map((t) => (t.id === id ? tool : t)),
      }));
      return tool;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // 批量测试
  batchTest: async () => {
    try {
      const data = await toolAPI.batchTest();
      // 更新所有工具的健康状态
      const resultMap = {};
      (data.results || []).forEach((r) => { resultMap[r.tool_id] = r; });
      set((state) => ({
        tools: state.tools.map((t) => {
          const r = resultMap[t.id];
          return r ? { ...t, health_status: r.success ? 'healthy' : 'unhealthy', health_message: r.message } : t;
        }),
      }));
      return data;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));

// ==================== System Store ====================
export const useSystemStore = create((set) => ({
  health: null,
  stats: null,
  traces: [],
  isLoading: false,
  error: null,

  loadHealth: async () => {
    try {
      const data = await systemAPI.health();
      set({ health: data });
    } catch (err) {
      set({ error: err.message });
    }
  },

  loadStats: async () => {
    try {
      const data = await systemAPI.stats();
      set({ stats: data });
    } catch (err) {
      set({ error: err.message });
    }
  },

  loadTraces: async (limit = 100) => {
    try {
      const data = await systemAPI.traces(limit);
      set({ traces: data });
    } catch (err) {
      set({ error: err.message });
    }
  },

  refreshAll: async () => {
    set({ isLoading: true });
    try {
      const [health, stats, traces] = await Promise.all([
        systemAPI.health(),
        systemAPI.stats(),
        systemAPI.traces(50),
      ]);
      set({ health, stats, traces, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

// ==================== Settings Store ====================
export const useSettingsStore = create((set, get) => ({
  settings: null,
  providers: null,
  isLoading: false,
  isSaving: false,
  error: null,
  testResult: null,

  loadSettings: async () => {
    set({ isLoading: true });
    try {
      const [data, providersData] = await Promise.all([
        settingsAPI.getAll(),
        settingsAPI.getProviders(),
      ]);
      set({
        settings: data,
        providers: providersData.providers || {},
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateSection: async (section, data) => {
    set({ isSaving: true });
    try {
      await settingsAPI.updateSection(section, data);
      // Reload all settings to get updated state
      const updated = await settingsAPI.getAll();
      set({ settings: updated, isSaving: false });
      return true;
    } catch (err) {
      set({ error: err.message, isSaving: false });
      return false;
    }
  },

  resetSettings: async () => {
    set({ isSaving: true });
    try {
      await settingsAPI.reset();
      const data = await settingsAPI.getAll();
      set({ settings: data, isSaving: false });
    } catch (err) {
      set({ error: err.message, isSaving: false });
    }
  },

  testLLMConnection: async (provider, apiKey, baseUrl, model) => {
    set({ testResult: null });
    try {
      const result = await settingsAPI.testLLM(provider, apiKey, baseUrl, model);
      set({ testResult: result });
      return result;
    } catch (err) {
      const result = { status: 'error', message: err.message };
      set({ testResult: result });
      return result;
    }
  },

  getProviderModels: async (providerId) => {
    try {
      const data = await settingsAPI.getProviderModels(providerId);
      return data.models || [];
    } catch {
      return [];
    }
  },

  clearError: () => set({ error: null }),
  clearTestResult: () => set({ testResult: null }),
}));

// ==================== Tenant Store ====================
export const useTenantStore = create((set, get) => ({
  tenants: [],
  currentTenant: null,
  tenantTools: [],
  tenantMCPs: [],
  tenantSkills: [],
  tenantContexts: [],
  tenantSettings: {},
  isLoading: false,
  error: null,

  // Load all tenants
  loadTenants: async () => {
    try {
      set({ isLoading: true });
      const data = await tenantAPI.list();
      set({ tenants: data, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // Select/switch tenant
  selectTenant: async (tenantId) => {
    try {
      set({ isLoading: true });
      const tenant = await tenantAPI.get(tenantId);
      localStorage.setItem('current_tenant_id', tenantId);
      set({ currentTenant: tenant, isLoading: false });
      // Load tenant resources
      await get().loadTenantResources(tenantId);
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // Clear tenant selection
  clearTenant: () => {
    localStorage.removeItem('current_tenant_id');
    set({
      currentTenant: null,
      tenantTools: [],
      tenantMCPs: [],
      tenantSkills: [],
      tenantContexts: [],
      tenantSettings: {},
    });
  },

  // Initialize from localStorage
  initTenant: async () => {
    const savedId = localStorage.getItem('current_tenant_id');
    if (savedId) {
      await get().selectTenant(savedId);
    }
  },

  // Load all tenant resources
  loadTenantResources: async (tenantId) => {
    const tid = tenantId || get().currentTenant?.id;
    if (!tid) return;
    try {
      const [tools, mcps, skills, contexts, settings] = await Promise.all([
        tenantAPI.listTools(tid),
        tenantAPI.listMCP(tid),
        tenantAPI.listSkills(tid),
        tenantAPI.listContexts(tid),
        tenantAPI.getSettings(tid),
      ]);
      set({
        tenantTools: tools,
        tenantMCPs: mcps,
        tenantSkills: skills,
        tenantContexts: contexts,
        tenantSettings: settings,
      });
    } catch (err) {
      set({ error: err.message });
    }
  },

  // Create tenant
  createTenant: async (data) => {
    try {
      const tenant = await tenantAPI.create(data);
      set((state) => ({ tenants: [tenant, ...state.tenants] }));
      return tenant;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // Update tenant
  updateTenant: async (id, data) => {
    try {
      const updated = await tenantAPI.update(id, data);
      set((state) => ({
        tenants: state.tenants.map((t) => (t.id === id ? updated : t)),
        currentTenant: state.currentTenant?.id === id ? updated : state.currentTenant,
      }));
      return updated;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // Delete tenant
  deleteTenant: async (id) => {
    try {
      await tenantAPI.delete(id);
      set((state) => ({
        tenants: state.tenants.filter((t) => t.id !== id),
        currentTenant: state.currentTenant?.id === id ? null : state.currentTenant,
      }));
    } catch (err) {
      set({ error: err.message });
    }
  },

  // Update tenant settings
  updateTenantSettings: async (data) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    try {
      const settings = await tenantAPI.updateSettings(tid, data);
      set({ tenantSettings: settings });
      return settings;
    } catch (err) {
      set({ error: err.message });
      throw err;
    }
  },

  // ---- Tools ----
  addTenantTool: async (data) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    const tool = await tenantAPI.createTool(tid, data);
    set((state) => ({ tenantTools: [...state.tenantTools, tool] }));
    return tool;
  },

  removeTenantTool: async (toolId) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    await tenantAPI.deleteTool(tid, toolId);
    set((state) => ({ tenantTools: state.tenantTools.filter((t) => t.id !== toolId) }));
  },

  // ---- MCP ----
  addTenantMCP: async (data) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    const mcp = await tenantAPI.createMCP(tid, data);
    set((state) => ({ tenantMCPs: [...state.tenantMCPs, mcp] }));
    return mcp;
  },

  removeTenantMCP: async (mcpId) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    await tenantAPI.deleteMCP(tid, mcpId);
    set((state) => ({ tenantMCPs: state.tenantMCPs.filter((m) => m.id !== mcpId) }));
  },

  // ---- Skills ----
  addTenantSkill: async (data) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    const skill = await tenantAPI.createSkill(tid, data);
    set((state) => ({ tenantSkills: [...state.tenantSkills, skill] }));
    return skill;
  },

  removeTenantSkill: async (skillId) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    await tenantAPI.deleteSkill(tid, skillId);
    set((state) => ({ tenantSkills: state.tenantSkills.filter((s) => s.id !== skillId) }));
  },

  // ---- Contexts ----
  addTenantContext: async (data) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    const ctx = await tenantAPI.createContext(tid, data);
    set((state) => ({ tenantContexts: [...state.tenantContexts, ctx] }));
    return ctx;
  },

  removeTenantContext: async (contextId) => {
    const tid = get().currentTenant?.id;
    if (!tid) return;
    await tenantAPI.deleteContext(tid, contextId);
    set((state) => ({ tenantContexts: state.tenantContexts.filter((c) => c.id !== contextId) }));
  },

  clearError: () => set({ error: null }),
}));
