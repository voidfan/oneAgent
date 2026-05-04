import React, { useEffect, useState } from 'react';
import {
  Bot,
  Plus,
  Edit3,
  Trash2,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  X,
  Save,
} from 'lucide-react';
import { useAgentStore } from '../store';

export default function AgentsPage() {
  const {
    agents,
    executions,
    isLoading,
    error,
    loadAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    loadExecutions,
    clearError,
  } = useAgentStore();

  const [showForm, setShowForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [expandedAgent, setExpandedAgent] = useState(null);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  const handleCreate = () => {
    setEditingAgent(null);
    setShowForm(true);
  };

  const handleEdit = (agent) => {
    setEditingAgent(agent);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('确定要删除此 Agent 吗？')) {
      await deleteAgent(id);
    }
  };

  const handleToggleExpand = async (agentId) => {
    if (expandedAgent === agentId) {
      setExpandedAgent(null);
    } else {
      setExpandedAgent(agentId);
      await loadExecutions(agentId);
    }
  };

  const handleFormSubmit = async (data) => {
    try {
      if (editingAgent) {
        await updateAgent(editingAgent.id, data);
      } else {
        await createAgent(data);
      }
      setShowForm(false);
      setEditingAgent(null);
    } catch (err) {
      // error is already set in store by createAgent/updateAgent
      console.error('Agent form submit error:', err);
    }
  };

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="max-w-5xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Agent 管理</h1>
            <p className="text-slate-400 text-sm mt-1">
              创建和管理 AI Agent，配置其能力和行为
            </p>
          </div>
          <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
            <Plus size={16} />
            创建 Agent
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
            <XCircle size={16} />
            <span className="flex-1">{error}</span>
            <button onClick={clearError}><X size={14} /></button>
          </div>
        )}

        {/* Agent list */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500">加载中...</div>
        ) : agents.length === 0 ? (
          <div className="text-center py-16">
            <Bot size={48} className="mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400 mb-4">还没有创建任何 Agent</p>
            <button onClick={handleCreate} className="btn-primary">
              创建第一个 Agent
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {agents.map((agent) => (
              <div key={agent.id} className="card">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Bot size={24} className="text-indigo-400" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-semibold text-white">
                        {agent.name}
                      </h3>
                      <StatusBadge status={agent.status || 'idle'} />
                    </div>
                    <p className="text-sm text-slate-400 mb-3">
                      {agent.description || '暂无描述'}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-3">
                      {agent.llm_provider && (
                        <span className="badge-info">
                          LLM: {agent.llm_provider}
                        </span>
                      )}
                      {agent.tools_config && Object.keys(agent.tools_config).length > 0 && (
                        <span className="badge-neutral">
                          工具: {Object.keys(agent.tools_config).length} 个
                        </span>
                      )}
                      {agent.max_steps && (
                        <span className="badge-neutral">
                          最大步数: {agent.max_steps}
                        </span>
                      )}
                    </div>

                    {/* Expanded executions */}
                    {expandedAgent === agent.id && (
                      <div className="mt-4 pt-4 border-t border-slate-700/50">
                        <h4 className="text-sm font-medium text-slate-300 mb-3">
                          执行历史
                        </h4>
                        {executions.length === 0 ? (
                          <p className="text-sm text-slate-500">暂无执行记录</p>
                        ) : (
                          <div className="space-y-2">
                            {executions.slice(0, 5).map((exec) => (
                              <div
                                key={exec.id}
                                className="flex items-center gap-3 px-3 py-2 bg-slate-800/50 rounded-lg text-sm"
                              >
                                <ExecutionStatusIcon status={exec.status} />
                                <span className="flex-1 text-slate-300 truncate">
                                  {exec.input_text || exec.id}
                                </span>
                                <span className="text-slate-500 text-xs">
                                  {exec.total_steps || 0} 步
                                </span>
                                <span className="text-slate-500 text-xs">
                                  {formatTime(exec.created_at)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleToggleExpand(agent.id)}
                      className="btn-icon"
                      title="执行历史"
                    >
                      {expandedAgent === agent.id ? (
                        <ChevronUp size={18} />
                      ) : (
                        <ChevronDown size={18} />
                      )}
                    </button>
                    <button
                      onClick={() => handleEdit(agent)}
                      className="btn-icon"
                      title="编辑"
                    >
                      <Edit3 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="btn-icon hover:text-red-400"
                      title="删除"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create/Edit Form Modal */}
        {showForm && (
          <AgentFormModal
            agent={editingAgent}
            onSubmit={handleFormSubmit}
            onClose={() => {
              setShowForm(false);
              setEditingAgent(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    idle: 'badge-neutral',
    running: 'badge-info',
    completed: 'badge-success',
    failed: 'badge-error',
  };
  const labels = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  };
  return (
    <span className={styles[status] || 'badge-neutral'}>
      {labels[status] || status}
    </span>
  );
}

function ExecutionStatusIcon({ status }) {
  switch (status) {
    case 'completed':
      return <CheckCircle size={14} className="text-green-400" />;
    case 'failed':
      return <XCircle size={14} className="text-red-400" />;
    case 'running':
      return <Play size={14} className="text-blue-400" />;
    default:
      return <Clock size={14} className="text-slate-400" />;
  }
}

function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function AgentFormModal({ agent, onSubmit, onClose }) {
  const [form, setForm] = useState({
    name: agent?.name || '',
    description: agent?.description || '',
    system_prompt: agent?.system_prompt || '',
    llm_provider: agent?.llm_provider || 'openai',
    llm_model: agent?.llm_model || 'gpt-4',
    max_steps: agent?.max_steps || 10,
    temperature: agent?.temperature || 0.7,
    tools: agent?.tools_config ? Object.keys(agent.tools_config).join(', ') : '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const toolsList = form.tools
      ? form.tools.split(',').map((t) => t.trim()).filter(Boolean)
      : [];
    const toolsConfig = {};
    toolsList.forEach((t) => { toolsConfig[t] = { enabled: true }; });
    onSubmit({
      name: form.name,
      description: form.description,
      system_prompt: form.system_prompt,
      llm_provider: form.llm_provider,
      llm_model: form.llm_model,
      max_steps: parseInt(form.max_steps, 10),
      temperature: parseFloat(form.temperature),
      tools_config: toolsConfig,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">
            {agent ? '编辑 Agent' : '创建 Agent'}
          </h2>
          <button onClick={onClose} className="btn-icon">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">名称 *</label>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              className="input"
              placeholder="例如: 代码助手"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">描述</label>
            <input
              name="description"
              value={form.description}
              onChange={handleChange}
              className="input"
              placeholder="Agent 的功能描述"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">系统提示词</label>
            <textarea
              name="system_prompt"
              value={form.system_prompt}
              onChange={handleChange}
              className="textarea"
              rows={4}
              placeholder="定义 Agent 的角色和行为..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">LLM 提供商</label>
              <select
                name="llm_provider"
                value={form.llm_provider}
                onChange={handleChange}
                className="select"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="local">本地模型</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">模型</label>
              <input
                name="llm_model"
                value={form.llm_model}
                onChange={handleChange}
                className="input"
                placeholder="gpt-4"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">最大步数</label>
              <input
                name="max_steps"
                type="number"
                value={form.max_steps}
                onChange={handleChange}
                className="input"
                min={1}
                max={200}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">温度</label>
              <input
                name="temperature"
                type="number"
                value={form.temperature}
                onChange={handleChange}
                className="input"
                min={0}
                max={2}
                step={0.1}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">工具（逗号分隔）</label>
            <input
              name="tools"
              value={form.tools}
              onChange={handleChange}
              className="input"
              placeholder="web_search, calculator, code_executor"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              取消
            </button>
            <button type="submit" className="btn-primary flex items-center gap-2">
              <Save size={16} />
              {agent ? '保存修改' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
