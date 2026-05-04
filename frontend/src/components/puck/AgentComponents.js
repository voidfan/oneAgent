import React from 'react';
import { Bot, User, Wrench, ChevronDown, ChevronUp, Send } from 'lucide-react';

// ─── AgentHeader ────────────────────────────────────────────────────────────
export const AgentHeaderConfig = {
  fields: {
    title: { type: 'text', label: 'Agent 名称' },
    subtitle: { type: 'text', label: '副标题' },
    avatarColor: { type: 'text', label: '头像颜色 (CSS)' },
  },
  defaultProps: {
    title: 'AI Assistant',
    subtitle: '智能对话助手，随时为您服务',
    avatarColor: '#6366f1',
  },
  render: ({ title, subtitle, avatarColor }) => (
    <div className="flex items-center gap-4 p-6 border-b border-slate-700 bg-slate-800">
      <div
        className="flex items-center justify-center w-12 h-12 rounded-full text-white font-bold text-lg flex-shrink-0"
        style={{ backgroundColor: avatarColor }}
      >
        <Bot size={24} />
      </div>
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  ),
};

// ─── WelcomeMessage ──────────────────────────────────────────────────────────
export const WelcomeMessageConfig = {
  fields: {
    heading: { type: 'text', label: '欢迎标题' },
    body: { type: 'textarea', label: '欢迎内容' },
  },
  defaultProps: {
    heading: '👋 你好！有什么可以帮助你的？',
    body: '我是一个 AI 助手，可以回答问题、分析数据、编写代码等。请随时告诉我你需要什么帮助。',
  },
  render: ({ heading, body }) => (
    <div className="mx-auto max-w-2xl px-6 py-8 text-center">
      <h2 className="text-2xl font-semibold text-white mb-3">{heading}</h2>
      <p className="text-slate-400 leading-relaxed">{body}</p>
    </div>
  ),
};

// ─── SuggestionChips ─────────────────────────────────────────────────────────
export const SuggestionChipsConfig = {
  fields: {
    chips: {
      type: 'array',
      label: '建议问题',
      arrayFields: {
        text: { type: 'text', label: '问题文本' },
      },
    },
  },
  defaultProps: {
    chips: [
      { text: '帮我写一段 Python 代码' },
      { text: '解释一下机器学习的基本概念' },
      { text: '如何优化 SQL 查询性能？' },
      { text: '给我讲一个有趣的故事' },
    ],
  },
  render: ({ chips, onChipClick }) => (
    <div className="flex flex-wrap gap-2 px-6 pb-4 justify-center">
      {(chips || []).map((chip, i) => (
        <button
          key={i}
          onClick={() => onChipClick && onChipClick(chip.text)}
          className="px-4 py-2 rounded-full bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white text-sm transition-colors border border-slate-600 hover:border-slate-500"
        >
          {chip.text}
        </button>
      ))}
    </div>
  ),
};

// ─── MessageBubble ───────────────────────────────────────────────────────────
export const MessageBubbleConfig = {
  fields: {
    userBubbleColor: { type: 'text', label: '用户气泡颜色' },
    aiBubbleColor: { type: 'text', label: 'AI 气泡颜色' },
    showAvatar: { type: 'radio', label: '显示头像', options: [{ label: '是', value: 'true' }, { label: '否', value: 'false' }] },
    roundedStyle: {
      type: 'select',
      label: '圆角风格',
      options: [
        { label: '圆润', value: 'rounded-2xl' },
        { label: '方正', value: 'rounded-md' },
        { label: '全圆', value: 'rounded-full' },
      ],
    },
  },
  defaultProps: {
    userBubbleColor: '#6366f1',
    aiBubbleColor: '#1e293b',
    showAvatar: 'true',
    roundedStyle: 'rounded-2xl',
  },
  render: ({ userBubbleColor, aiBubbleColor, showAvatar, roundedStyle }) => {
    const showAv = showAvatar !== 'false';
    return (
      <div className="px-4 py-2 space-y-4">
        {/* Preview: user message */}
        <div className="flex items-end gap-2 justify-end">
          <div
            className={`max-w-xs px-4 py-2 text-white text-sm ${roundedStyle} rounded-br-sm`}
            style={{ backgroundColor: userBubbleColor }}
          >
            这是用户发送的消息示例
          </div>
          {showAv && (
            <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0">
              <User size={16} className="text-slate-300" />
            </div>
          )}
        </div>
        {/* Preview: AI message */}
        <div className="flex items-end gap-2">
          {showAv && (
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
              <Bot size={16} className="text-white" />
            </div>
          )}
          <div
            className={`max-w-xs px-4 py-2 text-slate-200 text-sm ${roundedStyle} rounded-bl-sm border border-slate-700`}
            style={{ backgroundColor: aiBubbleColor }}
          >
            这是 AI 回复的消息示例，支持 Markdown 格式。
          </div>
        </div>
      </div>
    );
  },
};

// ─── ToolCallCard ────────────────────────────────────────────────────────────
export const ToolCallCardConfig = {
  fields: {
    accentColor: { type: 'text', label: '强调色' },
    defaultExpanded: {
      type: 'radio',
      label: '默认展开',
      options: [{ label: '是', value: 'true' }, { label: '否', value: 'false' }],
    },
  },
  defaultProps: {
    accentColor: '#f59e0b',
    defaultExpanded: 'false',
  },
  render: ({ accentColor, defaultExpanded }) => {
    const [expanded, setExpanded] = React.useState(defaultExpanded === 'true');
    return (
      <div className="mx-4 my-2 rounded-lg border border-slate-700 bg-slate-800 overflow-hidden">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-slate-700 transition-colors"
        >
          <Wrench size={14} style={{ color: accentColor }} />
          <span className="text-sm font-medium text-slate-300 flex-1">web_search</span>
          <span className="text-xs text-slate-500 mr-2">工具调用</span>
          {expanded ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
        </button>
        {expanded && (
          <div className="px-4 pb-3 border-t border-slate-700">
            <div className="mt-2">
              <p className="text-xs text-slate-500 mb-1">输入参数</p>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {JSON.stringify({ query: 'xAgent workflow designer' }, null, 2)}
              </pre>
            </div>
            <div className="mt-2">
              <p className="text-xs text-slate-500 mb-1">返回结果</p>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {'找到 10 条相关结果...'}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  },
};

// ─── ChatInputBar ────────────────────────────────────────────────────────────
export const ChatInputBarConfig = {
  fields: {
    placeholder: { type: 'text', label: '占位文本' },
    buttonColor: { type: 'text', label: '发送按钮颜色' },
    showAttach: {
      type: 'radio',
      label: '显示附件按钮',
      options: [{ label: '是', value: 'true' }, { label: '否', value: 'false' }],
    },
  },
  defaultProps: {
    placeholder: '输入消息，按 Enter 发送...',
    buttonColor: '#6366f1',
    showAttach: 'false',
  },
  render: ({ placeholder, buttonColor, onSend }) => (
    <div className="p-4 border-t border-slate-700 bg-slate-800">
      <div className="flex items-end gap-2 bg-slate-900 rounded-xl border border-slate-700 px-4 py-2">
        <textarea
          rows={1}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 resize-none outline-none text-sm py-1"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (onSend) onSend(e.target.value);
              e.target.value = '';
            }
          }}
        />
        <button
          className="flex items-center justify-center w-8 h-8 rounded-lg text-white flex-shrink-0 transition-opacity hover:opacity-80"
          style={{ backgroundColor: buttonColor }}
          onClick={(e) => {
            const ta = e.currentTarget.previousSibling;
            if (onSend && ta.value.trim()) { onSend(ta.value.trim()); ta.value = ''; }
          }}
        >
          <Send size={14} />
        </button>
      </div>
      <p className="text-xs text-slate-600 mt-1 text-center">Shift+Enter 换行，Enter 发送</p>
    </div>
  ),
};

// ─── Divider ─────────────────────────────────────────────────────────────────
export const DividerConfig = {
  fields: {
    label: { type: 'text', label: '分隔文字（可选）' },
    color: { type: 'text', label: '线条颜色' },
  },
  defaultProps: {
    label: '',
    color: '#334155',
  },
  render: ({ label, color }) => (
    <div className="flex items-center gap-3 px-6 py-2">
      <div className="flex-1 h-px" style={{ backgroundColor: color }} />
      {label && <span className="text-xs text-slate-500 flex-shrink-0">{label}</span>}
      {label && <div className="flex-1 h-px" style={{ backgroundColor: color }} />}
    </div>
  ),
};

// ─── Puck Config Export ───────────────────────────────────────────────────────
export const puckConfig = {
  components: {
    AgentHeader: AgentHeaderConfig,
    WelcomeMessage: WelcomeMessageConfig,
    SuggestionChips: SuggestionChipsConfig,
    MessageBubble: MessageBubbleConfig,
    ToolCallCard: ToolCallCardConfig,
    ChatInputBar: ChatInputBarConfig,
    Divider: DividerConfig,
  },
};

export default puckConfig;
