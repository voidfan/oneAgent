import React, { useEffect, useState } from 'react';
import {
  Building2, Plus, Trash2, ChevronRight,
  Wrench, Cpu, Brain, Globe, XCircle,
  Loader2, X, Save, Users, Key
} from 'lucide-react';
import { useTenantStore } from '../store';

const TABS = [
  { id: 'overview', label: '概览', icon: Building2 },
  { id: 'llm', label: 'LLM 配置', icon: Cpu },
  { id: 'tools', label: '工具', icon: Wrench },
  { id: 'mcp', label: 'MCP', icon: Globe },
  { id: 'skills', label: 'Skills', icon: Brain },
  { id: 'contexts', label: '上下文', icon: Key },
];

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl w-full max-w-lg mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="btn-ghost p-1"><X size={18} /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

function CreateTenantModal({ onClose, onCreate }) {
  const [form, setForm] = useState({ name: '', slug: '', description: '' });
  const [saving, setSaving] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try { await onCreate(form); onClose(); } finally { setSaving(false); }
  };
  return (
    <Modal title="新建租户" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">租户名称 *</label>
          <input className="input w-full" value={form.name}
            onChange={e => setForm({...form, name: e.target.value})} required />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">标识符 (slug) *</label>
          <input className="input w-full" value={form.slug}
            onChange={e => setForm({...form, slug: e.target.value})} required placeholder="my-tenant" />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">描述</label>
          <textarea className="input w-full h-20 resize-none" value={form.description}
            onChange={e => setForm({...form, description: e.target.value})} />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-ghost">取消</button>
          <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />} 创建
          </button>
        </div>
      </form>
    </Modal>
  );
}

function TenantCard({ tenant, isActive, onSelect, onDelete }) {
  return (
    <div
      className={`card p-4 cursor-pointer transition-all hover:border-indigo-500/50 ${isActive ? 'border-indigo-500 bg-indigo-500/10' : ''}`}
      onClick={() => onSelect(tenant.id)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isActive ? 'bg-indigo-600' : 'bg-slate-700'}`}>
            <Building2 size={20} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-white">{tenant.name}</span>
              {isActive && <span className="text-xs bg-indigo-600 text-white px-2 py-0.5 rounded-full">当前</span>}
            </div>
            <span className="text-xs text-slate-500">{tenant.slug}</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <ChevronRight size={16} className="text-slate-500" />
          <button
            onClick={e => { e.stopPropagation(); onDelete(tenant.id); }}
            className="btn-ghost p-1 text-red-400 hover:text-red-300"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {tenant.description && (
        <p className="text-sm text-slate-400 mt-2">{tenant.description}</p>
      )}
    </div>
  );
}

function LLMTab({ settings, onSave }) {
  const [form, setForm] = useState(settings?.llm || {});
  const [saving, setSaving] = useState(false);
  useEffect(() => { setForm(settings?.llm || {}); }, [settings]);
  const handleSave = async () => {
    setSaving(true);
    try { await onSave({ llm: form }); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="card p-4 space-y-4">
        <h4 className="font-medium text-white">LLM 配置（覆盖全局设置）</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">提供商</label>
            <select className="input w-full" value={form.provider || ''}
              onChange={e => setForm({...form, provider: e.target.value})}>
              <option value="">使用全局配置</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="local">本地模型</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">模型</label>
            <input className="input w-full" value={form.model || ''}
              onChange={e => setForm({...form, model: e.target.value})} placeholder="gpt-4o" />
          </div>
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">API Key</label>
          <input type="password" className="input w-full" value={form.api_key || ''}
            onChange={e => setForm({...form, api_key: e.target.value})} placeholder="留空使用全局配置" />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Base URL</label>
          <input className="input w-full" value={form.base_url || ''}
            onChange={e => setForm({...form, base_url: e.target.value})} placeholder="留空使用默认" />
        </div>
        <div className="flex justify-end">
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} 保存
          </button>
        </div>
      </div>
    </div>
  );
}

function ResourceTab({ items, onAdd, onRemove, fields, title, addLabel }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const handleAdd = async () => {
    setSaving(true);
    try { await onAdd(form); setForm({}); setShowForm(false); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-400">{items.length} 个{title}</span>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={14} /> {addLabel}
        </button>
      </div>
      {showForm && (
        <div className="card p-4 space-y-3 border-indigo-500/50">
          {fields.map(f => (
            <div key={f.key}>
              <label className="block text-sm text-slate-400 mb-1">{f.label}{f.required ? ' *' : ''}</label>
              {f.type === 'textarea' ? (
                <textarea className="input w-full h-20 resize-none" value={form[f.key] || ''}
                  onChange={e => setForm({...form, [f.key]: e.target.value})} placeholder={f.placeholder} />
              ) : (
                <input type={f.type || 'text'} className="input w-full" value={form[f.key] || ''}
                  onChange={e => setForm({...form, [f.key]: e.target.value})} placeholder={f.placeholder} />
              )}
            </div>
          ))}
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowForm(false); setForm({}); }} className="btn-ghost text-sm">取消</button>
            <button onClick={handleAdd} disabled={saving} className="btn-primary text-sm flex items-center gap-1">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} 添加
            </button>
          </div>
        </div>
      )}
      <div className="space-y-2">
        {items.length === 0 && (
          <div className="text-center text-slate-500 py-8">暂无{title}</div>
        )}
        {items.map(item => (
          <div key={item.id} className="card p-3 flex items-center justify-between">
            <div>
              <span className="font-medium text-white text-sm">{item.name}</span>
              {item.description && <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>}
              {item.url && <p className="text-xs text-slate-500 mt-0.5">{item.url}</p>}
              {item.content && (
                <p className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">{item.content}</p>
              )}
            </div>
            <button onClick={() => onRemove(item.id)} className="btn-ghost p-1 text-red-400 hover:text-red-300">
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TenantsPage() {
  const {
    tenants, currentTenant, tenantTools, tenantMCPs, tenantSkills, tenantContexts, tenantSettings,
    isLoading, error,
    loadTenants, selectTenant, clearTenant, createTenant, deleteTenant,
    updateTenantSettings, addTenantTool, removeTenantTool,
    addTenantMCP, removeTenantMCP, addTenantSkill, removeTenantSkill,
    addTenantContext, removeTenantContext, clearError,
  } = useTenantStore();

  const [activeTab, setActiveTab] = useState('overview');
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => { loadTenants(); }, [loadTenants]);

  const handleDelete = async (id) => {
    if (!window.confirm('确认删除该租户？')) return;
    await deleteTenant(id);
  };

  const renderTabContent = () => {
    if (!currentTenant) return null;
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-4">
            <div className="card p-4">
              <h4 className="font-medium text-white mb-3">租户信息</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-slate-400">名称：</span><span className="text-white">{currentTenant.name}</span></div>
                <div><span className="text-slate-400">标识符：</span><span className="text-white">{currentTenant.slug}</span></div>
                <div>
                  <span className="text-slate-400">状态：</span>
                  <span className={currentTenant.is_active ? 'text-green-400' : 'text-red-400'}>
                    {currentTenant.is_active ? '活跃' : '禁用'}
                  </span>
                </div>
                <div><span className="text-slate-400">ID：</span><span className="text-slate-500 font-mono text-xs">{currentTenant.id}</span></div>
              </div>
              {currentTenant.description && (
                <p className="text-sm text-slate-400 mt-3">{currentTenant.description}</p>
              )}
            </div>
            <div className="grid grid-cols-4 gap-3">
              {[
                ['工具', tenantTools.length, Wrench],
                ['MCP', tenantMCPs.length, Globe],
                ['Skills', tenantSkills.length, Brain],
                ['上下文', tenantContexts.length, Key],
              ].map(([label, count, Icon]) => (
                <div key={label} className="card p-4 text-center">
                  <Icon size={20} className="text-indigo-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">{count}</div>
                  <div className="text-xs text-slate-400">{label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'llm':
        return <LLMTab settings={tenantSettings} onSave={updateTenantSettings} />;
      case 'tools':
        return (
          <ResourceTab
            items={tenantTools} onAdd={addTenantTool} onRemove={removeTenantTool}
            title="工具" addLabel="添加工具"
            fields={[
              { key: 'name', label: '工具名称', required: true },
              { key: 'tool_type', label: '工具类型', placeholder: 'builtin/custom' },
              { key: 'description', label: '描述', type: 'textarea' },
            ]}
          />
        );
      case 'mcp':
        return (
          <ResourceTab
            items={tenantMCPs} onAdd={addTenantMCP} onRemove={removeTenantMCP}
            title="MCP配置" addLabel="添加MCP"
            fields={[
              { key: 'name', label: '名称', required: true },
              { key: 'url', label: '服务地址', placeholder: 'http://localhost:3000' },
              { key: 'description', label: '描述', type: 'textarea' },
            ]}
          />
        );
      case 'skills':
        return (
          <ResourceTab
            items={tenantSkills} onAdd={addTenantSkill} onRemove={removeTenantSkill}
            title="Skill" addLabel="添加Skill"
            fields={[
              { key: 'name', label: '名称', required: true },
              { key: 'skill_type', label: '类型', placeholder: 'prompt/code' },
              { key: 'content', label: '内容', type: 'textarea' },
            ]}
          />
        );
      case 'contexts':
        return (
          <ResourceTab
            items={tenantContexts} onAdd={addTenantContext} onRemove={removeTenantContext}
            title="上下文" addLabel="添加上下文"
            fields={[
              { key: 'name', label: '名称', required: true },
              { key: 'context_type', label: '类型', placeholder: 'system/user' },
              { key: 'content', label: '内容', type: 'textarea' },
            ]}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: tenant list */}
      <div className="w-72 flex-shrink-0 flex flex-col border-r border-slate-800 bg-slate-900">
        <div className="flex items-center justify-between px-4 h-16 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Users size={18} className="text-indigo-400" />
            <span className="font-semibold text-white">租户管理</span>
          </div>
          <button onClick={() => setShowCreate(true)} className="btn-primary p-1.5">
            <Plus size={16} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {isLoading && !tenants.length && (
            <div className="flex justify-center py-8">
              <Loader2 size={20} className="animate-spin text-slate-500" />
            </div>
          )}
          {tenants.map(t => (
            <TenantCard
              key={t.id} tenant={t}
              isActive={currentTenant?.id === t.id}
              onSelect={selectTenant}
              onDelete={handleDelete}
            />
          ))}
          {!isLoading && tenants.length === 0 && (
            <div className="text-center text-slate-500 py-12">
              <Building2 size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">暂无租户</p>
              <button onClick={() => setShowCreate(true)} className="btn-primary mt-3 text-sm">
                创建第一个租户
              </button>
            </div>
          )}
        </div>
        {currentTenant && (
          <div className="p-3 border-t border-slate-800">
            <button onClick={clearTenant} className="btn-ghost w-full text-sm text-slate-400">
              取消选择
            </button>
          </div>
        )}
      </div>

      {/* Right: tenant detail */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!currentTenant ? (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            <div className="text-center">
              <Building2 size={48} className="mx-auto mb-4 opacity-20" />
              <p>选择左侧租户查看详情</p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-4 px-6 h-16 border-b border-slate-800 bg-slate-900">
              <Building2 size={20} className="text-indigo-400" />
              <span className="font-semibold text-white">{currentTenant.name}</span>
              <span className="text-slate-500 text-sm">/ {currentTenant.slug}</span>
            </div>
            <div className="flex border-b border-slate-800 bg-slate-900 px-4">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm border-b-2 transition-colors ${
                    activeTab === id
                      ? 'border-indigo-500 text-indigo-400'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon size={14} />{label}
                </button>
              ))}
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              {renderTabContent()}
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-900/90 text-red-200 px-4 py-3 rounded-lg flex items-center gap-3 shadow-lg">
          <XCircle size={16} />
          <span className="text-sm">{error}</span>
          <button onClick={clearError}><X size={14} /></button>
        </div>
      )}

      {showCreate && (
        <CreateTenantModal onClose={() => setShowCreate(false)} onCreate={createTenant} />
      )}
    </div>
  );
}
