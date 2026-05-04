import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Render } from '@measured/puck';
import '@measured/puck/puck.css';
import { workflowAPI } from '../services/api';
import puckConfig from '../components/puck/AgentComponents';
import {
  Send,
  Loader2,
  Bot,
  User,
  Wrench,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react';

// ─── Tool Call Block ─────────────────────────────────────────────────────────
function ToolCallBlock({ name, input, output }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mx-4 my-2 rounded-lg border border-slate-700 bg-slate-800 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-slate-700 transition-colors"
      >
        <Wrench size={14} className="text-amber-400" />
        <span className="text-sm font-medium text-slate-300 flex-1">{name}</span>
        <span className="text-xs text-slate-500 mr-2">工具调用</span>
        {open ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
      </button>
      {open && (
        <div className="px-4 pb-3 border-t border-slate-700">
          {input && (
            <div className="mt-2">
              <p className="text-xs text-slate-500 mb-1">输入</p>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {typeof input === 'string' ? input : JSON.stringify(input, null, 2)}
              </pre>
            </div>
          )}
          {output && (
            <div className="mt-2">
              <p className="text-xs text-slate-500 mb-1">输出</p>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {typeof output === 'string' ? output : JSON.stringify(output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Message Item ────────────────────────────────────────────────────────────
function MessageItem({ msg }) {
  const isUser = msg.role === 'user';
  if (msg.role === 'tool') {
    return <ToolCallBlock name={msg.tool_name || 'tool'} input={msg.tool_input} output={msg.content} />;
  }
  return (
    <div className={`flex items-end gap-2 px-4 py-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mb-1">
          <Bot size={14} className="text-white" />
        </div>
      )}
      <div
        className={`max-w-2xl px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-sm'
        }`}
      >
        {msg.content}
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0 mb-1">
          <User size={14} className="text-slate-300" />
        </div>
      )}
    </div>
  );
}

// ─── Published App Page (独立布局，无侧边栏) ─────────────────────────────────
export default function PublishedAppPage() {
  const { slug } = useParams();
  const [workflow, setWorkflow] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const wf = await workflowAPI.getPublic(slug);
        setWorkflow(wf);
        // 设置页面标题
        document.title = wf.name || '应用';
      } catch (e) {
        setError('应用未找到或未发布');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [slug]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = (text || input).trim();
      if (!trimmed || sending) return;
      setInput('');
      setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
      setSending(true);
      setError('');
      try {
        const res = await workflowAPI.publicChat(slug, {
          message: trimmed,
          session_id: sessionId,
        });
        if (res.session_id) setSessionId(res.session_id);
        if (res.tool_calls && res.tool_calls.length > 0) {
          res.tool_calls.forEach((tc) => {
            setMessages((prev) => [
              ...prev,
              { role: 'tool', tool_name: tc.name, tool_input: tc.input, content: tc.output || '' },
            ]);
          });
        }
        const responseContent = res.response || res.message;
        setMessages((prev) => [...prev, { role: 'assistant', content: responseContent }]);
      } catch (e) {
        setError('发送失败，请重试');
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setSending(false);
        setTimeout(() => textareaRef.current?.focus(), 100);
      }
    },
    [input, sending, slug, sessionId]
  );

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ── Loading State ──
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin text-indigo-400 mx-auto mb-4" />
          <p className="text-slate-400 text-sm">加载应用中...</p>
        </div>
      </div>
    );
  }

  // ── Error State ──
  if (error && !workflow) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-center max-w-md px-6">
          <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-red-400" />
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">无法访问应用</h1>
          <p className="text-slate-400 text-sm">{error}</p>
          <p className="text-slate-500 text-xs mt-4">请检查链接是否正确，或联系应用发布者。</p>
        </div>
      </div>
    );
  }

  const puckData = workflow?.puck_data;
  const hasPuckContent = puckData && puckData.content && puckData.content.length > 0;

  // ── Chat Input Bar ──
  const chatInputBar = (
    <div className="p-4 border-t border-slate-800 bg-slate-900 flex-shrink-0">
      <div className="max-w-3xl mx-auto flex items-end gap-2 bg-slate-800 rounded-xl border border-slate-700 px-4 py-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
          className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 resize-none outline-none text-sm py-1 max-h-32"
          style={{ overflowY: 'auto' }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || sending}
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white flex-shrink-0 transition-colors"
        >
          {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </button>
      </div>
      <p className="text-xs text-slate-600 mt-1.5 text-center">
        Powered by <span className="text-indigo-400 font-medium">{workflow?.name}</span>
      </p>
    </div>
  );

  // ── Custom UI Mode (Puck 设计的界面作为首页) ──
  if (hasPuckContent) {
    const configWithHandlers = {
      ...puckConfig,
      components: Object.fromEntries(
        Object.entries(puckConfig.components).map(([key, comp]) => [
          key,
          {
            ...comp,
            render: (props) =>
              comp.render({ ...props, onChipClick: sendMessage, onSend: sendMessage }),
          },
        ])
      ),
    };

    return (
      <div className="flex flex-col h-screen bg-slate-950">
        {/* Puck 设计的界面作为应用首页 */}
        <div className="flex-1 overflow-y-auto">
          <Render config={configWithHandlers} data={puckData} />

          {/* 对话消息区域 */}
          {messages.length > 0 && (
            <div className="max-w-3xl mx-auto py-4 space-y-1">
              <div className="flex items-center gap-2 px-4 py-2 mb-2">
                <div className="flex-1 h-px bg-slate-800" />
                <span className="text-xs text-slate-500">对话记录</span>
                <div className="flex-1 h-px bg-slate-800" />
              </div>
              {messages.map((msg, i) => (
                <MessageItem key={i} msg={msg} />
              ))}
              {sending && (
                <div className="flex items-end gap-2 px-4 py-1">
                  <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
                    <Bot size={14} className="text-white" />
                  </div>
                  <div className="px-4 py-2.5 rounded-2xl rounded-bl-sm bg-slate-800 border border-slate-700">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {error && (
          <div className="px-4 py-2 text-xs text-red-400 text-center bg-red-900/20">{error}</div>
        )}
        {chatInputBar}
      </div>
    );
  }

  // ── Default Chat Mode (无 Puck 设计内容时的默认聊天界面) ──
  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* 顶部应用信息 */}
      <div className="flex items-center gap-3 px-6 py-4 bg-slate-900 border-b border-slate-800 flex-shrink-0">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0">
          <Bot size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-white">{workflow?.name}</h1>
          {workflow?.description && <p className="text-xs text-slate-400">{workflow.description}</p>}
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto py-4 space-y-1">
        {messages.length === 0 && (
          <div className="text-center py-16 px-6">
            <div className="w-16 h-16 bg-indigo-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bot size={32} className="text-indigo-400" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-1">{workflow?.name}</h2>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              {workflow?.description || '发送消息开始对话'}
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageItem key={i} msg={msg} />
        ))}
        {sending && (
          <div className="flex items-end gap-2 px-4 py-1">
            <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
              <Bot size={14} className="text-white" />
            </div>
            <div className="px-4 py-2.5 rounded-2xl rounded-bl-sm bg-slate-800 border border-slate-700">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-400 text-center bg-red-900/20">{error}</div>
      )}
      {chatInputBar}
    </div>
  );
}
