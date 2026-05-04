import React, { useEffect, useState, useCallback } from 'react';
import { Puck } from '@measured/puck';
import '@measured/puck/puck.css';
import { workflowAPI } from '../services/api';
import puckConfig from '../components/puck/AgentComponents';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Trash2,
  Play,
  Save,
  Loader2,
  Workflow,
  Edit3,
  X,
  Globe,
  Lock,
  Link2,
  Check,
  ExternalLink,
} from 'lucide-react';

// ─── Create Modal ─────────────────────────────────────────────────────────────
function CreateModal({ onClose, onCreate }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onCreate({ name: name.trim(), description: description.trim() });
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">新建工作流</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">工作流名称 *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：客服对话助手"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">描述（可选）</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="简要描述这个工作流的用途..."
              rows={3}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!name.trim() || saving}
              className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Workflow List Panel ──────────────────────────────────────────────────────
// ─── Publish Confirm Modal ────────────────────────────────────────────────────
function PublishModal({ workflow, onClose, onPublish }) {
  const [publishing, setPublishing] = useState(false);
  const isPublished = workflow?.is_public;

  const handlePublish = async () => {
    setPublishing(true);
    try {
      await onPublish(!isPublished);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setPublishing(false);
    }
  };

  const appUrl = `${window.location.origin}/app/${workflow?.slug}`;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">
            {isPublished ? '取消发布' : '发布应用'}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          {isPublished ? (
            <>
              <div className="flex items-center gap-3 p-4 bg-emerald-900/20 border border-emerald-800 rounded-lg">
                <Globe size={20} className="text-emerald-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-emerald-300">应用已发布</p>
                  <p className="text-xs text-slate-400 mt-0.5">其他用户可以通过链接访问此应用</p>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">应用访问链接</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={appUrl}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 font-mono"
                  />
                  <CopyButton text={appUrl} />
                </div>
              </div>
              <p className="text-sm text-slate-400">
                取消发布后，其他用户将无法通过链接访问此应用。
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 p-4 bg-indigo-900/20 border border-indigo-800 rounded-lg">
                <Globe size={20} className="text-indigo-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-indigo-300">发布为公开应用</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    发布后，其他用户可以通过链接访问此应用，首页将展示你设计的界面
                  </p>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">发布后的访问链接</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={appUrl}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 font-mono"
                  />
                  <CopyButton text={appUrl} />
                </div>
              </div>
            </>
          )}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
            >
              取消
            </button>
            <button
              onClick={handlePublish}
              disabled={publishing}
              className={`flex-1 px-4 py-2 text-white rounded-lg text-sm transition-colors flex items-center justify-center gap-2 ${
                isPublished
                  ? 'bg-red-600 hover:bg-red-500 disabled:opacity-50'
                  : 'bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50'
              }`}
            >
              {publishing ? (
                <Loader2 size={14} className="animate-spin" />
              ) : isPublished ? (
                <Lock size={14} />
              ) : (
                <Globe size={14} />
              )}
              {isPublished ? '取消发布' : '确认发布'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Copy Button ──────────────────────────────────────────────────────────────
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs transition-colors flex-shrink-0"
    >
      {copied ? <Check size={12} className="text-emerald-400" /> : <Link2 size={12} />}
      {copied ? '已复制' : '复制'}
    </button>
  );
}

// ─── Workflow List Panel ──────────────────────────────────────────────────────
function WorkflowList({ workflows, activeId, onSelect, onCreate, onDelete, loading }) {
  return (
    <div className="w-64 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Workflow size={16} className="text-indigo-400" />
          <span className="font-semibold text-white text-sm">工作流</span>
        </div>
        <button
          onClick={onCreate}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg transition-colors"
        >
          <Plus size={12} />
          新建
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin text-slate-500" />
          </div>
        ) : workflows.length === 0 ? (
          <div className="text-center py-8 px-4">
            <Workflow size={28} className="text-slate-700 mx-auto mb-2" />
            <p className="text-slate-500 text-xs">暂无工作流</p>
            <p className="text-slate-600 text-xs mt-1">点击「新建」创建</p>
          </div>
        ) : (
          workflows.map((wf) => (
            <div
              key={wf.id}
              onClick={() => onSelect(wf)}
              className={`group flex items-center gap-2 px-3 py-2.5 cursor-pointer transition-colors ${
                activeId === wf.id
                  ? 'bg-indigo-600/20 border-r-2 border-indigo-500'
                  : 'hover:bg-slate-800'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className={`text-sm font-medium truncate ${activeId === wf.id ? 'text-indigo-300' : 'text-slate-200'}`}>
                    {wf.name}
                  </p>
                  {wf.is_public && (
                    <Globe size={10} className="text-emerald-400 flex-shrink-0" />
                  )}
                </div>
                {wf.description && (
                  <p className="text-xs text-slate-500 truncate mt-0.5">{wf.description}</p>
                )}
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(wf.id); }}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-all rounded"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────
function EmptyState({ onCreate }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Workflow size={32} className="text-slate-600" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">选择或创建工作流</h2>
        <p className="text-slate-400 text-sm mb-6 max-w-xs">
          使用 Puck 拖拽编辑器设计你的 AI 对话界面，然后一键运行
        </p>
        <button
          onClick={onCreate}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors mx-auto"
        >
          <Plus size={16} />
          新建工作流
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function WorkflowDesignerPage() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState([]);
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [puckData, setPuckData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showPublish, setShowPublish] = useState(false);
  const [error, setError] = useState('');

  const loadWorkflows = useCallback(async () => {
    try {
      setLoading(true);
      const data = await workflowAPI.list();
      setWorkflows(data);
    } catch (err) {
      setError('加载工作流失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  const handleSelect = (wf) => {
    setActiveWorkflow(wf);
    setPuckData(wf.puck_data || { content: [], root: {} });
  };

  const handleCreate = async (formData) => {
    const wf = await workflowAPI.create({
      ...formData,
      puck_data: { content: [], root: {} },
    });
    setWorkflows((prev) => [wf, ...prev]);
    setActiveWorkflow(wf);
    setPuckData(wf.puck_data || { content: [], root: {} });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('确认删除此工作流？')) return;
    await workflowAPI.delete(id);
    setWorkflows((prev) => prev.filter((w) => w.id !== id));
    if (activeWorkflow?.id === id) {
      setActiveWorkflow(null);
      setPuckData(null);
    }
  };

  const handleSave = async (data) => {
    if (!activeWorkflow) return;
    setSaving(true);
    try {
      const updated = await workflowAPI.update(activeWorkflow.id, {
        puck_data: data,
      });
      setActiveWorkflow(updated);
      setWorkflows((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
    } catch (err) {
      setError('保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async (isPublic) => {
    if (!activeWorkflow) return;
    try {
      const updated = await workflowAPI.publish(activeWorkflow.id, isPublic);
      setActiveWorkflow(updated);
      setWorkflows((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
    } catch (err) {
      setError('发布操作失败');
      throw err;
    }
  };

  return (
    <div className="flex h-full overflow-hidden bg-slate-950">
      {/* Left: workflow list */}
      <WorkflowList
        workflows={workflows}
        activeId={activeWorkflow?.id}
        onSelect={handleSelect}
        onCreate={() => setShowCreate(true)}
        onDelete={handleDelete}
        loading={loading}
      />

      {/* Right: Puck editor or empty state */}
      {activeWorkflow && puckData ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 flex-shrink-0">
            <div className="flex items-center gap-2">
              <Edit3 size={14} className="text-indigo-400" />
              <span className="text-sm font-medium text-white">{activeWorkflow.name}</span>
              {activeWorkflow.is_public && (
                <span className="flex items-center gap-1 px-2 py-0.5 bg-emerald-900/40 border border-emerald-800 text-emerald-400 text-xs rounded-full">
                  <Globe size={10} />
                  已发布
                </span>
              )}
              {saving && <Loader2 size={12} className="animate-spin text-slate-400" />}
            </div>
            <div className="flex items-center gap-2">
              {error && (
                <span className="text-xs text-red-400 flex items-center gap-1">
                  <span>{error}</span>
                </span>
              )}
              {activeWorkflow.is_public && (
                <a
                  href={`/app/${activeWorkflow.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs rounded-lg transition-colors"
                >
                  <ExternalLink size={12} />
                  访问应用
                </a>
              )}
              <button
                onClick={() => setShowPublish(true)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  activeWorkflow.is_public
                    ? 'bg-emerald-600/20 border border-emerald-700 text-emerald-400 hover:bg-emerald-600/30'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                }`}
              >
                <Globe size={12} />
                {activeWorkflow.is_public ? '发布管理' : '发布应用'}
              </button>
              <button
                onClick={() => navigate(`/workflows/${activeWorkflow.id}/run`)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded-lg transition-colors"
              >
                <Play size={12} />
                运行测试
              </button>
            </div>
          </div>

          {/* Puck Editor */}
          <div className="flex-1 overflow-hidden">
            <Puck
              config={puckConfig}
              data={puckData}
              onPublish={handleSave}
              overrides={{
                headerActions: ({ children }) => (
                  <>
                    {children}
                    <button
                      onClick={() => setShowPublish(true)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ml-2 ${
                        activeWorkflow.is_public
                          ? 'bg-emerald-600/20 border border-emerald-700 text-emerald-400 hover:bg-emerald-600/30'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                      }`}
                    >
                      <Globe size={12} />
                      {activeWorkflow.is_public ? '已发布' : '发布'}
                    </button>
                    <button
                      onClick={() => navigate(`/workflows/${activeWorkflow.id}/run`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded-lg transition-colors ml-2"
                    >
                      <Play size={12} />
                      运行测试
                    </button>
                  </>
                ),
              }}
            />
          </div>
        </div>
      ) : (
        <EmptyState onCreate={() => setShowCreate(true)} />
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onCreate={handleCreate}
        />
      )}

      {/* Publish Modal */}
      {showPublish && activeWorkflow && (
        <PublishModal
          workflow={activeWorkflow}
          onClose={() => setShowPublish(false)}
          onPublish={handlePublish}
        />
      )}
    </div>
  );
}
