import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  Server,
  Cpu,
  Database,
  Clock,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Zap,
  MessageSquare,
  Bot,
  Wrench,
  TrendingUp,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useSystemStore } from '../store';

export default function MonitorPage() {
  const { health, stats, traces, isLoading, refreshAll } = useSystemStore();
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => refreshAll(), 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshAll]);

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">系统监控</h1>
            <p className="text-slate-400 text-sm mt-1">
              实时监控系统健康状态、性能指标和执行追踪
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-slate-600 bg-slate-800 text-indigo-500 focus:ring-indigo-500"
              />
              自动刷新
            </label>
            <button
              onClick={refreshAll}
              disabled={isLoading}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
              刷新
            </button>
          </div>
        </div>

        {/* Health status cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <HealthCard
            icon={Server}
            label="系统状态"
            value={health?.status || '未知'}
            status={health?.status === 'healthy' ? 'success' : 'warning'}
          />
          <HealthCard
            icon={Database}
            label="数据库"
            value={health?.database ? '已连接' : '未连接'}
            status={health?.database ? 'success' : 'error'}
          />
          <HealthCard
            icon={Clock}
            label="运行时间"
            value={formatUptime(health?.uptime)}
            status="info"
          />
          <HealthCard
            icon={Zap}
            label="版本"
            value={health?.version || '-'}
            status="neutral"
          />
        </div>

        {/* Stats overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={MessageSquare}
              label="总对话数"
              value={stats.total_conversations || 0}
              color="indigo"
            />
            <StatCard
              icon={Bot}
              label="Agent 数量"
              value={stats.total_agents || 0}
              color="purple"
            />
            <StatCard
              icon={Wrench}
              label="工具调用"
              value={stats.total_tool_executions || 0}
              color="cyan"
            />
            <StatCard
              icon={TrendingUp}
              label="LLM 调用"
              value={stats.total_llm_calls || 0}
              color="emerald"
            />
          </div>
        )}

        {/* Performance metrics */}
        {stats?.performance && (
          <div className="card mb-8">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Cpu size={18} className="text-indigo-400" />
              性能指标
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <MetricItem
                label="平均响应时间"
                value={`${(stats.performance.avg_response_time || 0).toFixed(0)}ms`}
                description="API 请求平均响应时间"
              />
              <MetricItem
                label="平均 LLM 延迟"
                value={`${(stats.performance.avg_llm_latency || 0).toFixed(0)}ms`}
                description="LLM 调用平均延迟"
              />
              <MetricItem
                label="Token 使用量"
                value={formatNumber(stats.performance.total_tokens || 0)}
                description="累计 Token 消耗"
              />
            </div>
          </div>
        )}

        {/* Execution traces */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity size={18} className="text-indigo-400" />
            执行追踪
          </h2>

          {traces.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              暂无追踪记录
            </div>
          ) : (
            <div className="space-y-2">
              {traces.map((trace) => (
                <TraceItem key={trace.trace_id} trace={trace} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function HealthCard({ icon: Icon, label, value, status }) {
  const statusColors = {
    success: 'text-green-400 bg-green-500/10 border-green-500/20',
    warning: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    error: 'text-red-400 bg-red-500/10 border-red-500/20',
    info: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    neutral: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
  };

  const iconColors = {
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400',
    info: 'text-blue-400',
    neutral: 'text-slate-400',
  };

  return (
    <div className={`rounded-xl border p-4 ${statusColors[status]}`}>
      <div className="flex items-center gap-3">
        <Icon size={20} className={iconColors[status]} />
        <div>
          <p className="text-xs text-slate-400">{label}</p>
          <p className="text-sm font-semibold mt-0.5">{value}</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    indigo: 'bg-indigo-500/10 text-indigo-400',
    purple: 'bg-purple-500/10 text-purple-400',
    cyan: 'bg-cyan-500/10 text-cyan-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-xs text-slate-400">{label}</p>
          <p className="text-xl font-bold text-white">{formatNumber(value)}</p>
        </div>
      </div>
    </div>
  );
}

function MetricItem({ label, value, description }) {
  return (
    <div>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{description}</p>
    </div>
  );
}

function TraceItem({ trace }) {
  const [expanded, setExpanded] = useState(false);

  const statusIcon = {
    completed: <CheckCircle size={14} className="text-green-400" />,
    failed: <XCircle size={14} className="text-red-400" />,
    running: <Activity size={14} className="text-blue-400 animate-pulse" />,
  };

  return (
    <div className="bg-slate-800/50 rounded-lg overflow-hidden">
      <div
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-800/80 transition-colors"
      >
        {expanded ? (
          <ChevronDown size={14} className="text-slate-500" />
        ) : (
          <ChevronRight size={14} className="text-slate-500" />
        )}
        {statusIcon[trace.status] || statusIcon.completed}
        <span className="text-sm text-white font-medium flex-1 truncate">
          {trace.name || trace.trace_id}
        </span>
        {trace.duration_ms != null && (
          <span className="text-xs text-slate-500">
            {trace.duration_ms.toFixed(0)}ms
          </span>
        )}
        <span className="text-xs text-slate-600">
          {formatTraceTime(trace.start_time)}
        </span>
      </div>

      {expanded && trace.spans && (
        <div className="px-4 pb-3 space-y-1">
          {trace.spans.map((span, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 pl-6 py-1.5 text-xs"
            >
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  backgroundColor:
                    span.status === 'error'
                      ? '#ef4444'
                      : span.status === 'running'
                      ? '#3b82f6'
                      : '#22c55e',
                }}
              />
              <span className="text-slate-400 flex-1 truncate">
                {span.name}
              </span>
              {span.duration_ms != null && (
                <span className="text-slate-600">
                  {span.duration_ms.toFixed(1)}ms
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatUptime(seconds) {
  if (!seconds) return '-';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 24) {
    const d = Math.floor(h / 24);
    return `${d}天 ${h % 24}小时`;
  }
  return `${h}小时 ${m}分钟`;
}

function formatNumber(num) {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return String(num);
}

function formatTraceTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}
