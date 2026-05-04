import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Settings,
  Save,
  RotateCcw,
  Cpu,
  Bot,
  Wrench,
  Brain,
  Eye,
  Shield,
  CheckCircle,
  XCircle,
  Loader2,
  Plus,
  Trash2,
  TestTube,
  X,
  ToggleLeft,
  ToggleRight,
  Search,
  ExternalLink,
  Info,
  ChevronDown,
  Key,
  Globe,
  Box,
  Zap,
} from 'lucide-react';
import { useSettingsStore } from '../store';

const TABS = [
  { id: 'llm', label: 'LLM 配置', icon: Cpu },
  { id: 'agent', label: 'Agent 默认值', icon: Bot },
  { id: 'tools', label: '工具配置', icon: Wrench },
  { id: 'memory', label: '记忆系统', icon: Brain },
  { id: 'observability', label: '可观测性', icon: Eye },
  { id: 'security', label: '安全设置', icon: Shield },
];

export default function SettingsPage() {
  const {
    settings,
    providers,
    isLoading,
    isSaving,
    error,
    testResult,
    loadSettings,
    updateSection,
    resetSettings,
    testLLMConnection,
    clearError,
    clearTestResult,
  } = useSettingsStore();

  const [activeTab, setActiveTab] = useState('llm');
  const [localSettings, setLocalSettings] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    if (settings) {
      setLocalSettings(JSON.parse(JSON.stringify(settings)));
      setHasChanges(false);
    }
  }, [settings]);

  const updateLocal = useCallback((section, value) => {
    setLocalSettings((prev) => ({
      ...prev,
      [section]: value,
    }));
    setHasChanges(true);
  }, []);

  const handleSave = async () => {
    if (!localSettings) return;
    const sectionMap = {
      llm: 'llm',
      agent: 'agent_defaults',
      tools: 'tools',
      memory: 'memory',
      observability: 'observability',
      security: 'security',
    };
    const section = sectionMap[activeTab];
    if (section && localSettings[section] !== undefined) {
      const success = await updateSection(section, { [section]: localSettings[section] });
      if (success) setHasChanges(false);
    }
  };

  const handleReset = async () => {
    if (window.confirm('确定要重置所有配置为默认值吗？此操作不可撤销。')) {
      await resetSettings();
    }
  };

  if (isLoading || !localSettings) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={32} className="animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="max-w-5xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Settings size={24} className="text-indigo-400" />
              系统设置
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              配置 LLM 提供商、Agent 行为、工具、记忆系统等所有系统参数
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleReset} className="btn-ghost flex items-center gap-2 text-slate-400">
              <RotateCcw size={14} />
              重置默认
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              保存配置
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
            <XCircle size={16} />
            <span className="flex-1">{error}</span>
            <button onClick={clearError}><X size={14} /></button>
          </div>
        )}

        {/* Unsaved changes indicator */}
        {hasChanges && (
          <div className="mb-4 px-4 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-400 text-sm flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            有未保存的更改
          </div>
        )}

        <div className="flex gap-6">
          {/* Tab navigation */}
          <div className="w-48 flex-shrink-0">
            <nav className="space-y-1 sticky top-6">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === id
                      ? 'bg-indigo-500/10 text-indigo-400'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon size={16} />
                  {label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab content */}
          <div className="flex-1 min-w-0">
            {activeTab === 'llm' && (
              <LLMSettings
                llmConfig={localSettings.llm || {}}
                providers={providers || {}}
                onChange={(v) => updateLocal('llm', v)}
                onTest={testLLMConnection}
                testResult={testResult}
                clearTestResult={clearTestResult}
              />
            )}
            {activeTab === 'agent' && (
              <AgentSettings
                config={localSettings.agent_defaults || {}}
                providers={providers || {}}
                onChange={(v) => updateLocal('agent_defaults', v)}
              />
            )}
            {activeTab === 'tools' && (
              <ToolSettings
                tools={localSettings.tools || []}
                onChange={(v) => updateLocal('tools', v)}
              />
            )}
            {activeTab === 'memory' && (
              <MemorySettings
                config={localSettings.memory || {}}
                onChange={(v) => updateLocal('memory', v)}
              />
            )}
            {activeTab === 'observability' && (
              <ObservabilitySettings
                config={localSettings.observability || {}}
                onChange={(v) => updateLocal('observability', v)}
              />
            )}
            {activeTab === 'security' && (
              <SecuritySettings
                config={localSettings.security || {}}
                onChange={(v) => updateLocal('security', v)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== LLM Settings (重构版) ====================
function LLMSettings({ llmConfig, providers, onChange, onTest, testResult, clearTestResult }) {
  const [testing, setTesting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showProviderList, setShowProviderList] = useState(false);

  // 当前选中的提供商元数据
  const currentProviderMeta = useMemo(() => {
    return providers[llmConfig.provider] || null;
  }, [providers, llmConfig.provider]);

  // 按搜索词过滤提供商列表
  const filteredProviders = useMemo(() => {
    const entries = Object.entries(providers);
    if (!searchTerm) return entries;
    const term = searchTerm.toLowerCase();
    return entries.filter(
      ([id, meta]) =>
        id.toLowerCase().includes(term) ||
        meta.label.toLowerCase().includes(term) ||
        (meta.description && meta.description.toLowerCase().includes(term))
    );
  }, [providers, searchTerm]);

  const update = (field, value) => {
    onChange({ ...llmConfig, [field]: value });
  };

  const handleProviderChange = (providerId) => {
    const meta = providers[providerId];
    if (meta) {
      onChange({
        ...llmConfig,
        provider: providerId,
        base_url: meta.default_base_url || '',
        model: meta.default_model || '',
        // 保留 api_key 不变，除非切换到不需要 key 的提供商
        api_key: meta.requires_api_key ? (llmConfig.api_key || '') : '',
      });
    }
    setShowProviderList(false);
    setSearchTerm('');
  };

  const handleTest = async () => {
    setTesting(true);
    clearTestResult();
    await onTest(
      llmConfig.provider,
      llmConfig.api_key,
      llmConfig.base_url,
      llmConfig.model
    );
    setTesting(false);
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Cpu}
        title="LLM 提供商配置"
        description="配置 AI 模型的 API 提供商、地址、密钥和模型"
      />

      {/* 4 个核心配置项在同一个卡片 */}
      <div className="card">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-indigo-500/20 rounded-lg flex items-center justify-center">
            <Zap size={20} className="text-indigo-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-white font-semibold">LLM 连接配置</h3>
            <p className="text-xs text-slate-500">配置 API 提供商、地址、密钥和模型</p>
          </div>
        </div>

        <div className="space-y-5">
          {/* 1. API 提供商 */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
              <Cpu size={12} />
              API 提供商
              <span className="text-red-400 text-[10px]">* 必填</span>
            </label>
            <div className="relative">
              <button
                onClick={() => setShowProviderList(!showProviderList)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/80 border border-slate-700/50 rounded-lg hover:border-indigo-500/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-indigo-500/10 rounded-md flex items-center justify-center">
                    <Cpu size={16} className="text-indigo-400" />
                  </div>
                  <div className="text-left">
                    <div className="text-white font-medium text-sm">
                      {currentProviderMeta?.label || llmConfig.provider || '选择提供商'}
                    </div>
                    <div className="text-xs text-slate-500">
                      {currentProviderMeta?.description || '点击选择 API 提供商'}
                    </div>
                  </div>
                </div>
                <ChevronDown
                  size={16}
                  className={`text-slate-400 transition-transform ${showProviderList ? 'rotate-180' : ''}`}
                />
              </button>

              {/* 提供商下拉列表 */}
              {showProviderList && (
                <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-slate-700/50 rounded-lg shadow-2xl max-h-80 overflow-hidden">
                  {/* 搜索框 */}
                  <div className="p-3 border-b border-slate-700/50">
                    <div className="relative">
                      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                      <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-md text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
                        placeholder="搜索提供商..."
                        autoFocus
                      />
                    </div>
                  </div>

                  {/* 提供商列表 */}
                  <div className="overflow-y-auto max-h-60 scrollbar-thin">
                    {filteredProviders.map(([id, meta]) => (
                      <button
                        key={id}
                        onClick={() => handleProviderChange(id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-700/50 transition-colors text-left ${
                          llmConfig.provider === id ? 'bg-indigo-500/10 border-l-2 border-indigo-500' : ''
                        }`}
                      >
                        <div className="w-7 h-7 bg-slate-700/50 rounded-md flex items-center justify-center flex-shrink-0">
                          <Cpu size={14} className={llmConfig.provider === id ? 'text-indigo-400' : 'text-slate-400'} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className={`text-sm font-medium truncate ${
                            llmConfig.provider === id ? 'text-indigo-400' : 'text-white'
                          }`}>
                            {meta.label}
                          </div>
                          <div className="text-xs text-slate-500 truncate">{meta.description}</div>
                        </div>
                        {llmConfig.provider === id && (
                          <CheckCircle size={14} className="text-indigo-400 flex-shrink-0" />
                        )}
                      </button>
                    ))}
                    {filteredProviders.length === 0 && (
                      <div className="px-4 py-6 text-center text-slate-500 text-sm">
                        未找到匹配的提供商
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 点击外部关闭 */}
            {showProviderList && (
              <div
                className="fixed inset-0 z-40"
                onClick={() => {
                  setShowProviderList(false);
                  setSearchTerm('');
                }}
              />
            )}
          </div>

          {/* 2. Base URL */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
              <Globe size={12} />
              Base URL
              {currentProviderMeta?.requires_base_url && (
                <span className="text-red-400 text-[10px]">* 必填</span>
              )}
              {!currentProviderMeta?.requires_base_url && (
                <span className="text-slate-600 text-[10px]">可选（留空使用默认）</span>
              )}
            </label>
            <div className="relative">
              <input
                value={llmConfig.base_url || ''}
                onChange={(e) => update('base_url', e.target.value)}
                className="input text-sm font-mono pr-10"
                placeholder={currentProviderMeta?.default_base_url || '输入 API Base URL'}
              />
              {currentProviderMeta?.default_base_url && !llmConfig.base_url && (
                <button
                  onClick={() => update('base_url', currentProviderMeta.default_base_url)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-indigo-400 hover:text-indigo-300"
                  title="使用默认地址"
                >
                  <ExternalLink size={14} />
                </button>
              )}
            </div>
            {currentProviderMeta?.default_base_url && (
              <p className="text-[11px] text-slate-600 mt-1">
                默认: {currentProviderMeta.default_base_url}
              </p>
            )}
          </div>

          {/* 3. API 密钥 */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
              <Key size={12} />
              API 密钥
              {currentProviderMeta?.requires_api_key ? (
                <span className="text-red-400 text-[10px]">* 必填</span>
              ) : (
                <span className="text-slate-600 text-[10px]">不需要</span>
              )}
            </label>
            {currentProviderMeta?.requires_api_key !== false ? (
              <input
                type="password"
                value={llmConfig.api_key || ''}
                onChange={(e) => update('api_key', e.target.value)}
                className="input text-sm font-mono"
                placeholder={`输入 ${currentProviderMeta?.label || ''} API Key`}
              />
            ) : (
              <div className="px-4 py-3 bg-slate-800/50 border border-slate-700/30 rounded-lg text-sm text-slate-500 flex items-center gap-2">
                <Info size={14} />
                此提供商不需要 API 密钥
              </div>
            )}
          </div>

          {/* 4. 模型 */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
              <Box size={12} />
              模型
              <span className="text-red-400 text-[10px]">* 必填</span>
            </label>
            {currentProviderMeta?.models && currentProviderMeta.models.length > 0 ? (
              <div className="space-y-2">
                <select
                  value={llmConfig.model || ''}
                  onChange={(e) => update('model', e.target.value)}
                  className="select text-sm"
                >
                  <option value="">-- 选择模型 --</option>
                  {currentProviderMeta.models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-600">或手动输入:</span>
                  <input
                    value={llmConfig.model || ''}
                    onChange={(e) => update('model', e.target.value)}
                    className="input text-xs flex-1"
                    placeholder="自定义模型名称"
                  />
                </div>
              </div>
            ) : (
              <input
                value={llmConfig.model || ''}
                onChange={(e) => update('model', e.target.value)}
                className="input text-sm"
                placeholder="输入模型名称"
              />
            )}
          </div>
        </div>
      </div>

      {/* 测试连接 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
              <TestTube size={20} className="text-amber-400" />
            </div>
            <div>
              <h3 className="text-white font-semibold">测试连接</h3>
              <p className="text-xs text-slate-500">验证当前配置是否能正常连接到 LLM 服务</p>
            </div>
          </div>
          <button
            onClick={handleTest}
            disabled={testing || !llmConfig.provider}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {testing ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <TestTube size={14} />
            )}
            测试连接
          </button>
        </div>

        {testResult && !testing && (
          <div className={`mt-4 px-4 py-3 rounded-lg flex items-start gap-2 text-sm ${
            testResult.status === 'success'
              ? 'bg-green-500/10 border border-green-500/20 text-green-400'
              : 'bg-red-500/10 border border-red-500/20 text-red-400'
          }`}>
            {testResult.status === 'success' ? (
              <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
            ) : (
              <XCircle size={16} className="mt-0.5 flex-shrink-0" />
            )}
            <div>
              <p className="font-medium">{testResult.message}</p>
              {testResult.response && (
                <p className="text-xs mt-1 opacity-70">响应: {testResult.response}</p>
              )}
              {testResult.model && (
                <p className="text-xs mt-0.5 opacity-70">模型: {testResult.model}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 当前配置摘要 */}
      <div className="card bg-slate-800/30">
        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">当前配置摘要</h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">提供商:</span>
            <span className="text-xs text-white font-medium">{currentProviderMeta?.label || llmConfig.provider || '-'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">模型:</span>
            <span className="text-xs text-white font-medium font-mono">{llmConfig.model || '-'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Base URL:</span>
            <span className="text-xs text-white font-medium font-mono truncate">{llmConfig.base_url || currentProviderMeta?.default_base_url || '-'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">密钥:</span>
            <span className="text-xs text-white font-medium">
              {llmConfig.api_key ? '已配置 ✓' : (currentProviderMeta?.requires_api_key ? '未配置 ✗' : '不需要')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== Agent Settings ====================
function AgentSettings({ config, providers, onChange }) {
  const update = (field, value) => onChange({ ...config, [field]: value });

  // 从 providers 构建提供商选项
  const providerOptions = useMemo(() => {
    return Object.entries(providers || {}).map(([id, meta]) => ({
      value: id,
      label: meta.label,
    }));
  }, [providers]);

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Bot}
        title="Agent 默认配置"
        description="设置新建 Agent 时的默认参数"
      />

      <div className="card space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">默认 LLM 提供商</label>
            <select
              value={config.default_provider || 'openai'}
              onChange={(e) => update('default_provider', e.target.value)}
              className="select"
            >
              {providerOptions.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">默认模型</label>
            <input
              value={config.default_model || 'gpt-4o'}
              onChange={(e) => update('default_model', e.target.value)}
              className="input"
              placeholder="gpt-4o"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">最大迭代次数</label>
            <input
              type="number"
              value={config.max_iterations || 10}
              onChange={(e) => update('max_iterations', parseInt(e.target.value, 10))}
              className="input"
              min={1}
              max={100}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              默认温度: {config.default_temperature || 0.7}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={config.default_temperature || 0.7}
              onChange={(e) => update('default_temperature', parseFloat(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">最大 Token</label>
          <input
            type="number"
            value={config.max_tokens || 4096}
            onChange={(e) => update('max_tokens', parseInt(e.target.value, 10))}
            className="input w-40"
            min={1}
            max={128000}
          />
        </div>

        <div className="border-t border-slate-700/50 pt-4 space-y-3">
          <ToggleField
            label="启用反思机制"
            description="Agent 在执行过程中定期反思和调整策略"
            checked={config.enable_reflection !== false}
            onChange={(v) => update('enable_reflection', v)}
          />
          {config.enable_reflection !== false && (
            <div className="pl-8">
              <label className="block text-xs font-medium text-slate-400 mb-1">
                反思间隔（每 N 步反思一次）
              </label>
              <input
                type="number"
                value={config.reflection_interval || 3}
                onChange={(e) => update('reflection_interval', parseInt(e.target.value, 10))}
                className="input w-32"
                min={1}
                max={20}
              />
            </div>
          )}
          <ToggleField
            label="启用任务规划"
            description="Agent 在执行前先进行任务分解和规划"
            checked={config.enable_planning !== false}
            onChange={(v) => update('enable_planning', v)}
          />
        </div>
      </div>
    </div>
  );
}

// ==================== Tool Settings ====================
function ToolSettings({ tools, onChange }) {
  const updateTool = (index, field, value) => {
    const updated = [...tools];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addTool = () => {
    onChange([
      ...tools,
      { name: '', enabled: true, requires_approval: false, timeout: 30, config: {} },
    ]);
  };

  const removeTool = (index) => {
    onChange(tools.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Wrench}
        title="工具配置"
        description="管理已注册工具的启用状态、审批要求和超时设置"
      />

      <div className="space-y-3">
        {tools.map((tool, idx) => (
          <div key={idx} className="card py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => updateTool(idx, 'enabled', !tool.enabled)}
                className="flex-shrink-0"
              >
                {tool.enabled ? (
                  <ToggleRight size={24} className="text-indigo-400" />
                ) : (
                  <ToggleLeft size={24} className="text-slate-600" />
                )}
              </button>

              <div className="flex-1 grid grid-cols-4 gap-4 items-center">
                <div>
                  <input
                    value={tool.name}
                    onChange={(e) => updateTool(idx, 'name', e.target.value)}
                    className="input text-xs"
                    placeholder="工具名称"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={tool.requires_approval || false}
                    onChange={(e) => updateTool(idx, 'requires_approval', e.target.checked)}
                    className="rounded border-slate-600 bg-slate-800 text-indigo-500"
                  />
                  <span className="text-xs text-slate-400">需要审批</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={tool.timeout || 30}
                      onChange={(e) => updateTool(idx, 'timeout', parseInt(e.target.value, 10))}
                      className="input text-xs w-20"
                      min={1}
                      max={300}
                    />
                    <span className="text-xs text-slate-500">秒</span>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => removeTool(idx)}
                    className="btn-icon hover:text-red-400"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button onClick={addTool} className="btn-secondary flex items-center gap-2">
        <Plus size={14} />
        添加工具
      </button>
    </div>
  );
}

// ==================== Memory Settings ====================
function MemorySettings({ config, onChange }) {
  const update = (field, value) => onChange({ ...config, [field]: value });

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Brain}
        title="记忆系统配置"
        description="配置短期记忆、长期记忆和工作记忆的参数"
      />

      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-white">短期记忆</h3>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            最大 Token 数: {config.short_term_max_tokens || 4000}
          </label>
          <input
            type="range"
            min="500"
            max="128000"
            step="500"
            value={config.short_term_max_tokens || 4000}
            onChange={(e) => update('short_term_max_tokens', parseInt(e.target.value, 10))}
            className="w-full accent-indigo-500"
          />
          <div className="flex justify-between text-xs text-slate-600 mt-1">
            <span>500</span>
            <span>128,000</span>
          </div>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">长期记忆 (向量存储)</h3>
          <button onClick={() => update('long_term_enabled', !config.long_term_enabled)}>
            {config.long_term_enabled !== false ? (
              <ToggleRight size={24} className="text-indigo-400" />
            ) : (
              <ToggleLeft size={24} className="text-slate-600" />
            )}
          </button>
        </div>

        {config.long_term_enabled !== false && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">集合名称</label>
              <input
                value={config.long_term_collection || 'xagent_memory'}
                onChange={(e) => update('long_term_collection', e.target.value)}
                className="input text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">检索数量 (Top-K)</label>
              <input
                type="number"
                value={config.long_term_top_k || 5}
                onChange={(e) => update('long_term_top_k', parseInt(e.target.value, 10))}
                className="input text-xs"
                min={1}
                max={50}
              />
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <ToggleField
          label="工作记忆"
          description="启用任务状态跟踪、计划管理和反思记录"
          checked={config.working_memory_enabled !== false}
          onChange={(v) => update('working_memory_enabled', v)}
        />
      </div>
    </div>
  );
}

// ==================== Observability Settings ====================
function ObservabilitySettings({ config, onChange }) {
  const update = (field, value) => onChange({ ...config, [field]: value });

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Eye}
        title="可观测性配置"
        description="配置日志级别、追踪和监控指标"
      />

      <div className="card space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">日志级别</label>
          <select
            value={config.log_level || 'INFO'}
            onChange={(e) => update('log_level', e.target.value)}
            className="select"
          >
            <option value="DEBUG">DEBUG - 详细调试信息</option>
            <option value="INFO">INFO - 一般运行信息</option>
            <option value="WARNING">WARNING - 警告信息</option>
            <option value="ERROR">ERROR - 仅错误信息</option>
          </select>
        </div>

        <div className="border-t border-slate-700/50 pt-4 space-y-3">
          <ToggleField
            label="执行追踪"
            description="记录 Agent 执行的详细追踪信息 (Trace/Span)"
            checked={config.enable_tracing !== false}
            onChange={(v) => update('enable_tracing', v)}
          />
          <ToggleField
            label="Prometheus 指标"
            description="暴露 Prometheus 格式的监控指标"
            checked={config.enable_metrics !== false}
            onChange={(v) => update('enable_metrics', v)}
          />
        </div>

        {config.enable_tracing !== false && (
          <div className="pt-2">
            <label className="block text-xs font-medium text-slate-400 mb-1">
              追踪数据保留时间（小时）
            </label>
            <input
              type="number"
              value={config.trace_retention_hours || 24}
              onChange={(e) => update('trace_retention_hours', parseInt(e.target.value, 10))}
              className="input w-32"
              min={1}
              max={720}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== Security Settings ====================
function SecuritySettings({ config, onChange }) {
  const update = (field, value) => onChange({ ...config, [field]: value });

  const updateCorsOrigin = (index, value) => {
    const updated = [...(config.cors_origins || ['*'])];
    updated[index] = value;
    update('cors_origins', updated);
  };

  const addCorsOrigin = () => {
    update('cors_origins', [...(config.cors_origins || ['*']), '']);
  };

  const removeCorsOrigin = (index) => {
    update('cors_origins', (config.cors_origins || []).filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Shield}
        title="安全设置"
        description="配置 CORS、认证和速率限制"
      />

      <div className="card space-y-4">
        <ToggleField
          label="启用认证"
          description="要求 API 请求携带有效的认证令牌"
          checked={config.enable_auth || false}
          onChange={(v) => update('enable_auth', v)}
        />

        <div className="border-t border-slate-700/50 pt-4">
          <label className="block text-xs font-medium text-slate-400 mb-1">
            API 速率限制（每分钟请求数）
          </label>
          <input
            type="number"
            value={config.api_rate_limit || 100}
            onChange={(e) => update('api_rate_limit', parseInt(e.target.value, 10))}
            className="input w-40"
            min={1}
            max={10000}
          />
        </div>

        <div className="border-t border-slate-700/50 pt-4">
          <label className="block text-xs font-medium text-slate-400 mb-2">CORS 允许的来源</label>
          <div className="space-y-2">
            {(config.cors_origins || ['*']).map((origin, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  value={origin}
                  onChange={(e) => updateCorsOrigin(idx, e.target.value)}
                  className="input text-xs flex-1"
                  placeholder="https://example.com 或 *"
                />
                <button
                  onClick={() => removeCorsOrigin(idx)}
                  className="btn-icon hover:text-red-400"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
          <button onClick={addCorsOrigin} className="btn-ghost text-xs mt-2 flex items-center gap-1">
            <Plus size={12} />
            添加来源
          </button>
        </div>
      </div>
    </div>
  );
}

// ==================== Shared Components ====================

function SectionHeader({ icon: Icon, title, description }) {
  return (
    <div className="flex items-start gap-3 mb-2">
      <div className="w-10 h-10 bg-indigo-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
        <Icon size={20} className="text-indigo-400" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
    </div>
  );
}

function ToggleField({ label, description, checked, onChange }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-white font-medium">{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <button onClick={() => onChange(!checked)}>
        {checked ? (
          <ToggleRight size={28} className="text-indigo-400" />
        ) : (
          <ToggleLeft size={28} className="text-slate-600" />
        )}
      </button>
    </div>
  );
}
