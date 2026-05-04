import React, { useState } from 'react';
import { NavLink, useLocation, Outlet } from 'react-router-dom';
import {
  MessageSquare,
  Bot,
  Wrench,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Building2,
  GitBranch,
} from 'lucide-react';

const navItems = [
  { path: '/chat', label: '对话', icon: MessageSquare },
  { path: '/agents', label: 'Agent 管理', icon: Bot },
  { path: '/tools', label: '工具管理', icon: Wrench },
  { path: '/workflows', label: '工作流设计器', icon: GitBranch },
  { path: '/monitor', label: '系统监控', icon: Activity },
  { path: '/tenants', label: '租户管理', icon: Building2 },
  { path: '/settings', label: '系统设置', icon: Settings },
];

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-slate-900 border-r border-slate-800 transition-all duration-300 ${
          collapsed ? 'w-16' : 'w-60'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-slate-800">
          <div className="flex items-center justify-center w-8 h-8 bg-indigo-600 rounded-lg flex-shrink-0">
            <Zap size={18} className="text-white" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold text-white tracking-tight">
              xAgent
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `sidebar-link ${
                  isActive || location.pathname.startsWith(path) ? 'active' : ''
                } ${collapsed ? 'justify-center px-0' : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon size={20} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Collapse toggle */}
        <div className="p-2 border-t border-slate-800">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="btn-ghost w-full flex items-center justify-center gap-2"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            {!collapsed && <span className="text-xs text-slate-500">收起侧栏</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">{children || <Outlet />}</main>
    </div>
  );
}
