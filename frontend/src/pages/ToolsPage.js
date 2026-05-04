import React, { useEffect, useState, useMemo } from 'react';
import {
  Wrench, Plus, Edit3, Trash2, Search,
  CheckCircle, XCircle, X, Save, RefreshCw,
  ToggleLeft, ToggleRight, FileText,
  Globe, Terminal, Code, Bot, Server,
  ChevronDown, ChevronRight, Eye, EyeOff, Zap,
} from 'lucide-react';
import { useToolStore } from '../store';

/* ── 常量 ─────────────────────────────────────────── */
const TYPE_ICONS = { mcp: Server, api: Globe, agent: Bot, script: Terminal, sandbox: Code };
const TYPE_COLORS = {
  mcp: 'text-purple-400 bg-purple-500/20',
  api: 'text-blue-400 bg-blue-500/20',
  agent: 'text-amber-400 bg-amber-500/20',
  script: 'text-green-400 bg-green-500/20',
  sandbox: 'text-cyan-400 bg-cyan-500/20',
  skills: 'text-pink-400 bg-pink-500/20',
};
const HEALTH = {
  healthy:   { color: 'text-green-400', bg: 'bg-green-500/20', label: '健康' },
  unhealthy: { color: 'text-red-400',   bg: 'bg-red-500/20',   label: '异常' },
  unknown:   { color: 'text-slate-400', bg: 'bg-slate-500/20', label: '未知' },
};

/* ══════════════════════════════════════════════════════
   主页面
   ══════════════════════════════════════════════════════ */
export default function ToolsPage() {
  const {
    tools, toolTypes, isLoading, error,
    loadTools, loadToolTypes, createTool, updateTool, deleteTool,
    testConnection, toggleTool, batchTest, clearError,
  } = useToolStore();

  const [showForm, setShowForm]       = useState(false);
  const [editingTool, setEditingTool] = useState(null);
  const [filterType, setFilterType]   = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [testingId, setTestingId]     = useState(null);
  const [batchTesting, setBatchTesting] = useState(false);
  const [expandedId, setExpandedId]   = useState(null);

  useEffect(() => { loadTools(); loadToolTypes(); }, [loadTools, loadToolTypes]);

  /* 过滤 */
  const filteredTools = useMemo(() => {
    let list = tools || [];
    if (filterType !== 'all') list = list.filter((t) => t.type === filterType);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((t) =>
        t.name.toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q)
      );
    }
    return list;
  }, [tools, filterType, searchQuery]);

  /* 类型计数 */
  const typeCounts = useMemo(() => {
    const c = { all: (tools || []).length };
    (tools || []).forEach((t) => { c[t.type] = (c[t.type] || 0) + 1; });
    return c;
  }, [tools]);

  /* 事件处理 */
  const handleCreate = () => { setEditingTool(null); setShowForm(true); };
  const handleEdit   = (tool) => { setEditingTool(tool); setShowForm(true); };
  const handleDelete = async (id) => {
    if (window.confirm('确定要删除此工具吗？')) await deleteTool(id);
  };
  const handleToggle = (id) => toggleTool(id);
  const handleTest   = async (id) => {
    setTestingId(id);
    try { await testConnection(id); } finally { setTestingId(null); }
  };
  const handleBatchTest = async () => {
    setBatchTesting(true);
    try { await batchTest(); } finally { setBatchTesting(false); }
  };
  const handleFormSubmit = async (data) => {
    try {
      if (editingTool) await updateTool(editingTool.id, data);
      else await createTool(data);
      setShowForm(false);
      setEditingTool(null);
    } catch (err) { console.error('Tool form error:', err); }
  };

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="max-w-6xl mx-auto p-6">

        {/* ── 顶栏 ── */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">工具管理</h1>
            <p className="text-slate-400 text-sm mt-1">统一管理 MCP、API、Agent、脚本和沙箱工具</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleBatchTest} disabled={batchTesting} className="btn-secondary flex items-center gap-2">
              <RefreshCw size={16} className={batchTesting ? 'animate-spin' : ''} />
              {batchTesting ? '测试中...' : '批量测试'}
            </button>
            <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
              <Plus size={16} /> 添加工具
            </button>
          </div>
        </div>

        {/* ── 错误 ── */}
        {error && (
          <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
            <XCircle size={16} />
            <span className="flex-1">{error}</span>
            <button onClick={clearError}><X size={14} /></button>
          </div>
        )}

        {/* ── 筛选栏 ── */}
        <div className="flex items-center gap-4 mb-6 flex-wrap">
          <div className="relative flex-1 max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" placeholder="搜索工具名称或描述..." />
          </div>
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            <FilterTab label={`全部 (${typeCounts.all || 0})`} active={filterType === 'all'} onClick={() => setFilterType('all')} />
            {Object.entries(toolTypes).map(([key, info]) => (
              <FilterTab key={key} label={`${info.label} (${typeCounts[key] || 0})`} active={filterType === key} onClick={() => setFilterType(key)} />
            ))}
          </div>
        </div>

        {/* ── 工具列表 ── */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500">加载中...</div>
        ) : filteredTools.length === 0 ? (
          <div className="text-center py-16">
            <Wrench size={48} className="mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400 mb-4">{searchQuery || filterType !== 'all' ? '没有匹配的工具' : '还没有添加任何工具'}</p>
            {!searchQuery && filterType === 'all' && (
              <button onClick={handleCreate} className="btn-primary">添加第一个工具</button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTools.map((tool) => (
              <ToolCard
                key={tool.id}
                tool={tool}
                toolTypes={toolTypes}
                expanded={expandedId === tool.id}
                testing={testingId === tool.id}
                onToggleExpand={() => setExpandedId(expandedId === tool.id ? null : tool.id)}
                onEdit={() => handleEdit(tool)}
                onDelete={() => handleDelete(tool.id)}
                onToggle={() => handleToggle(tool.id)}
                onTest={() => handleTest(tool.id)}
              />
            ))}
          </div>
        )}

        {/* ── 表单弹窗 ── */}
        {showForm && (
          <ToolFormModal
            tool={editingTool}
            toolTypes={toolTypes}
            onSubmit={handleFormSubmit}
            onClose={() => { setShowForm(false); setEditingTool(null); }}
          />
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   FilterTab
   ══════════════════════════════════════════════════════ */
function FilterTab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
        active ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
      }`}
    >
      {label}
    </button>
  );
}

/* ══════════════════════════════════════════════════════
   ToolCard — 工具卡片
   ══════════════════════════════════════════════════════ */
function ToolCard({ tool, toolTypes, expanded, testing, onToggleExpand, onEdit, onDelete, onToggle, onTest }) {
  const Icon = TYPE_ICONS[tool.type] || Wrench;
  const colorCls = TYPE_COLORS[tool.type] || 'text-slate-400 bg-slate-500/20';
  const health = HEALTH[tool.health_status] || HEALTH.unknown;
  const typeLabel = toolTypes[tool.type]?.label || tool.type;

  return (
    <div className="card">
      <div className="flex items-start gap-4">
        {/* 图标 */}
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${colorCls}`}>
          <Icon size={24} />
        </div>

        {/* 信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold text-white">{tool.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${colorCls}`}>{typeLabel}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${health.bg} ${health.color}`}>{health.label}</span>
            {!tool.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-slate-600/40 text-slate-500">已禁用</span>}
          </div>
          <p className="text-sm text-slate-400 mb-2">{tool.description || '暂无描述'}</p>

          {/* 标签 */}
          <div className="flex flex-wrap gap-2 text-xs">
            {tool.health_message && (
              <span className="text-slate-500" title={tool.health_message}>
                {tool.health_message.length > 60 ? tool.health_message.slice(0, 60) + '...' : tool.health_message}
              </span>
            )}
          </div>

          {/* 展开详情 */}
          {expanded && (
            <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3">
              {/* 配置信息 */}
              {tool.config && Object.keys(tool.config).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">配置信息</h4>
                  <pre className="text-xs bg-slate-900/50 rounded-lg p-3 text-slate-400 overflow-x-auto max-h-40 overflow-y-auto">
                    {JSON.stringify(tool.config, null, 2)}
                  </pre>
                </div>
              )}
              {/* 配置文件 */}
              {tool.config_file && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                    <FileText size={14} /> 配置文件
                  </h4>
                  <pre className="text-xs bg-slate-900/50 rounded-lg p-3 text-slate-400 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {tool.config_file}
                  </pre>
                </div>
              )}
              {/* 说明文件 */}
              {tool.readme && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                    <FileText size={14} /> 说明文件
                  </h4>
                  <pre className="text-xs bg-slate-900/50 rounded-lg p-3 text-slate-400 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {tool.readme}
                  </pre>
                </div>
              )}
              {/* 输入/输出 Schema */}
              {tool.input_schema && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">输入 Schema</h4>
                  <pre className="text-xs bg-slate-900/50 rounded-lg p-3 text-slate-400 overflow-x-auto max-h-32 overflow-y-auto">
                    {JSON.stringify(tool.input_schema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <button onClick={onTest} disabled={testing} className="btn-icon" title="测试连通性">
            {testing ? <RefreshCw size={18} className="animate-spin text-blue-400" /> : <Zap size={18} />}
          </button>
          <button onClick={onToggle} className="btn-icon" title={tool.is_active ? '禁用' : '启用'}>
            {tool.is_active ? <ToggleRight size={18} className="text-green-400" /> : <ToggleLeft size={18} className="text-slate-500" />}
          </button>
          <button onClick={onToggleExpand} className="btn-icon" title="详情">
            {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </button>
          <button onClick={onEdit} className="btn-icon" title="编辑">
            <Edit3 size={18} />
          </button>
          <button onClick={onDelete} className="btn-icon hover:text-red-400" title="删除">
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ToolFormModal — 创建/编辑工具弹窗
   ══════════════════════════════════════════════════════ */
function ToolFormModal({ tool, toolTypes, onSubmit, onClose }) {
  const isEdit = !!tool;
  const [activeTab, setActiveTab] = useState('basic');

  const [form, setForm] = useState({
    name:        tool?.name || '',
    type:        tool?.type || Object.keys(toolTypes)[0] || 'mcp',
    description: tool?.description || '',
    config:      tool?.config || {},
    config_file: tool?.config_file || '',
    readme:      tool?.readme || '',
    input_schema:  tool?.input_schema ? JSON.stringify(tool.input_schema, null, 2) : '',
    output_schema: tool?.output_schema ? JSON.stringify(tool.output_schema, null, 2) : '',
  });

  const handleChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const handleConfigFieldChange = (fieldKey, value) => {
    setForm((prev) => {
      const newConfig = { ...prev.config };
      // 支持嵌套 key，如 "auth.type"
      const parts = fieldKey.split('.');
      if (parts.length === 2) {
        newConfig[parts[0]] = { ...(newConfig[parts[0]] || {}), [parts[1]]: value };
      } else {
        newConfig[fieldKey] = value;
      }
      return { ...prev, config: newConfig };
    });
  };

  const getConfigValue = (fieldKey) => {
    const parts = fieldKey.split('.');
    if (parts.length === 2) return (form.config[parts[0]] || {})[parts[1]] || '';
    return form.config[fieldKey] || '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      name: form.name,
      type: form.type,
      description: form.description,
      config: form.config,
      config_file: form.config_file || null,
      readme: form.readme || null,
    };
    if (form.input_schema.trim()) {
      try { payload.input_schema = JSON.parse(form.input_schema); } catch (_) { /* ignore */ }
    }
    if (form.output_schema.trim()) {
      try { payload.output_schema = JSON.parse(form.output_schema); } catch (_) { /* ignore */ }
    }
    onSubmit(payload);
  };

  const currentTypeFields = toolTypes[form.type]?.config_fields || [];

  const tabs = [
    { key: 'basic',  label: '基本信息' },
    { key: 'config', label: '连接配置' },
    { key: 'files',  label: '配置文件 & 说明' },
    { key: 'schema', label: 'Schema' },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-white">{isEdit ? '编辑工具' : '添加工具'}</h2>
          <button onClick={onClose} className="btn-icon"><X size={18} /></button>
        </div>

        {/* Tab 栏 */}
        <div className="flex border-b border-slate-700 px-6 flex-shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">

          {/* ── 基本信息 Tab ── */}
          {activeTab === 'basic' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">名称 *</label>
                <input value={form.name} onChange={(e) => handleChange('name', e.target.value)} className="input" placeholder="工具名称" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">类型 *</label>
                <select value={form.type} onChange={(e) => handleChange('type', e.target.value)} className="select" disabled={isEdit}>
                  {Object.entries(toolTypes).map(([key, info]) => (
                    <option key={key} value={key}>{info.label} - {info.description}</option>
                  ))}
                </select>
                {isEdit && <p className="text-xs text-slate-500 mt-1">工具类型创建后不可更改</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">描述</label>
                <textarea value={form.description} onChange={(e) => handleChange('description', e.target.value)} className="textarea" rows={3} placeholder="工具的功能描述..." />
              </div>
            </>
          )}

          {/* ── 连接配置 Tab ── */}
          {activeTab === 'config' && (
            <>
              <p className="text-sm text-slate-400 mb-2">
                根据工具类型 <span className="text-indigo-400 font-medium">{toolTypes[form.type]?.label || form.type}</span> 配置连接参数
              </p>
              {currentTypeFields.length === 0 ? (
                <p className="text-slate-500 text-sm py-4">该类型暂无配置字段</p>
              ) : (
                currentTypeFields.map((field) => (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      {field.label} {field.required && <span className="text-red-400">*</span>}
                    </label>
                    <ConfigFieldInput
                      field={field}
                      value={getConfigValue(field.key)}
                      onChange={(val) => handleConfigFieldChange(field.key, val)}
                    />
                  </div>
                ))
              )}
            </>
          )}

          {/* ── 配置文件 & 说明 Tab ── */}
          {activeTab === 'files' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1 flex items-center gap-2">
                  <FileText size={14} /> 配置文件 (YAML/JSON)
                </label>
                <p className="text-xs text-slate-500 mb-2">通过此配置文件可以将工具正常运行起来</p>
                <textarea
                  value={form.config_file}
                  onChange={(e) => handleChange('config_file', e.target.value)}
                  className="textarea font-mono text-xs"
                  rows={10}
                  placeholder={'# 工具配置文件\n# 支持 YAML 或 JSON 格式\nserver:\n  host: localhost\n  port: 8080'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1 flex items-center gap-2">
                  <FileText size={14} /> 说明文件 (Markdown)
                </label>
                <p className="text-xs text-slate-500 mb-2">工具的使用说明和文档</p>
                <textarea
                  value={form.readme}
                  onChange={(e) => handleChange('readme', e.target.value)}
                  className="textarea font-mono text-xs"
                  rows={10}
                  placeholder={'# 工具名称\n\n## 功能说明\n\n描述工具的主要功能...\n\n## 使用方法\n\n1. 步骤一\n2. 步骤二'}
                />
              </div>
            </>
          )}

          {/* ── Schema Tab ── */}
          {activeTab === 'schema' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">输入 Schema (JSON)</label>
                <textarea
                  value={form.input_schema}
                  onChange={(e) => handleChange('input_schema', e.target.value)}
                  className="textarea font-mono text-xs"
                  rows={8}
                  placeholder={'{\n  "type": "object",\n  "properties": {\n    "query": { "type": "string", "description": "查询内容" }\n  },\n  "required": ["query"]\n}'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">输出 Schema (JSON)</label>
                <textarea
                  value={form.output_schema}
                  onChange={(e) => handleChange('output_schema', e.target.value)}
                  className="textarea font-mono text-xs"
                  rows={8}
                  placeholder={'{\n  "type": "object",\n  "properties": {\n    "result": { "type": "string" }\n  }\n}'}
                />
              </div>
            </>
          )}

          {/* 提交按钮 */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
            <button type="button" onClick={onClose} className="btn-secondary">取消</button>
            <button type="submit" className="btn-primary flex items-center gap-2">
              <Save size={16} /> {isEdit ? '保存修改' : '创建工具'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ConfigFieldInput — 根据字段类型渲染不同输入控件
   ══════════════════════════════════════════════════════ */
function ConfigFieldInput({ field, value, onChange }) {
  const [showPassword, setShowPassword] = useState(false);

  switch (field.type) {
    case 'select':
      return (
        <select value={value || field.default || ''} onChange={(e) => onChange(e.target.value)} className="select">
          {(field.options || []).map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );

    case 'number':
      return (
        <input
          type="number"
          value={value || field.default || ''}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
          className="input"
          placeholder={field.placeholder}
        />
      );

    case 'password':
      return (
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="input pr-10"
            placeholder={field.placeholder}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      );

    case 'json':
      return (
        <textarea
          value={typeof value === 'string' ? value : JSON.stringify(value || {}, null, 2)}
          onChange={(e) => {
            try { onChange(JSON.parse(e.target.value)); } catch (_) { onChange(e.target.value); }
          }}
          className="textarea font-mono text-xs"
          rows={4}
          placeholder={field.placeholder || '{}'}
        />
      );

    case 'code':
      return (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="textarea font-mono text-xs"
          rows={6}
          placeholder={field.placeholder}
        />
      );

    case 'tags':
      return (
        <input
          value={Array.isArray(value) ? value.join(', ') : value || ''}
          onChange={(e) => onChange(e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
          className="input"
          placeholder="逗号分隔，如: json, math, os"
        />
      );

    default: // text
      return (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="input"
          placeholder={field.placeholder}
          required={field.required}
        />
      );
  }
}
