import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  Send,
  Plus,
  Trash2,
  MessageSquare,
  Loader2,
  Bot,
  User,
  AlertCircle,
  X,
} from 'lucide-react';
import { useChatStore } from '../store';

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    isLoading,
    error,
    loadConversations,
    selectConversation,
    newConversation,
    sendMessage,
    deleteConversation,
    clearError,
  } = useChatStore();

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load conversation if ID in URL
  useEffect(() => {
    if (conversationId) {
      selectConversation(conversationId);
    }
  }, [conversationId, selectConversation]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, [currentConversation]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming || isLoading) return;
    setInput('');
    await sendMessage(trimmed);
  }, [input, isStreaming, isLoading, sendMessage]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    newConversation();
    navigate('/chat');
  };

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation();
    await deleteConversation(id);
  };

  const handleSelectConversation = (id) => {
    navigate(`/chat/${id}`);
  };

  return (
    <div className="flex h-full">
      {/* Conversation list sidebar */}
      <div className="w-72 bg-slate-900/50 border-r border-slate-800 flex flex-col">
        <div className="p-3 border-b border-slate-800">
          <button onClick={handleNewChat} className="btn-primary w-full flex items-center justify-center gap-2">
            <Plus size={16} />
            新对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin py-2">
          {conversations.length === 0 ? (
            <div className="text-center text-slate-500 text-sm py-8">
              暂无对话记录
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => handleSelectConversation(conv.id)}
                className={`group flex items-center gap-3 mx-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                  currentConversation?.id === conv.id
                    ? 'bg-indigo-500/10 text-indigo-300'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <MessageSquare size={16} className="flex-shrink-0" />
                <span className="flex-1 text-sm truncate">
                  {conv.title || '新对话'}
                </span>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6">
          {messages.length === 0 ? (
            <EmptyState onSuggestionClick={setInput} />
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg, idx) => (
                <MessageBubble key={msg.id || idx} message={msg} />
              ))}
              {isStreaming && (
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <Loader2 size={14} className="animate-spin" />
                  <span>AI 正在思考...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-4 mb-2 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm animate-fade-in">
            <AlertCircle size={16} />
            <span className="flex-1">{error}</span>
            <button onClick={clearError}>
              <X size={14} />
            </button>
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-slate-800 p-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
                  rows={1}
                  className="textarea min-h-[44px] max-h-[200px] pr-12"
                  style={{
                    height: 'auto',
                    height: Math.min(
                      200,
                      Math.max(44, input.split('\n').length * 24 + 20)
                    ),
                  }}
                  disabled={isStreaming}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isStreaming || isLoading}
                className="btn-primary flex items-center justify-center w-11 h-11 p-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStreaming ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>
            <p className="text-xs text-slate-600 mt-2 text-center">
              xAgent AI 助手 · 基于大语言模型驱动
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Empty state component
function EmptyState({ onSuggestionClick }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
      <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6">
        <Bot size={32} className="text-indigo-400" />
      </div>
      <h2 className="text-xl font-semibold text-slate-200 mb-2">
        欢迎使用 xAgent
      </h2>
      <p className="text-slate-500 max-w-md mb-8">
        我是一个智能 AI 助手，具备工具调用、任务规划、记忆管理等能力。
        请输入您的问题或任务，我将尽力帮助您。
      </p>
      <div className="grid grid-cols-2 gap-3 max-w-lg">
        {[
          '帮我分析一段代码的性能问题',
          '搜索最新的 AI 技术趋势',
          '制定一个项目开发计划',
          '解释 ReAct 推理框架的原理',
        ].map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSuggestionClick(suggestion)}
            className="text-left px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-lg
                       text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800
                       transition-colors duration-200"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

// Message bubble component
function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-indigo-500/20 rounded-lg flex items-center justify-center">
          <Bot size={16} className="text-indigo-400" />
        </div>
      )}

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-slate-800/80 text-slate-200'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="markdown-content text-sm">
            <ReactMarkdown>{message.content || ''}</ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center">
          <User size={16} className="text-slate-300" />
        </div>
      )}
    </div>
  );
}
