import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import AgentsPage from './pages/AgentsPage';
import ToolsPage from './pages/ToolsPage';
import MonitorPage from './pages/MonitorPage';
import SettingsPage from './pages/SettingsPage';
import TenantsPage from './pages/TenantsPage';
import WorkflowDesignerPage from './pages/WorkflowDesignerPage';
import WorkflowRunnerPage from './pages/WorkflowRunnerPage';
import PublishedAppPage from './pages/PublishedAppPage';

/** 带侧边栏的管理后台布局包装 */
function AdminLayout() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        {/* 公开应用页面 - 独立布局，无侧边栏 */}
        <Route path="/app/:slug" element={<PublishedAppPage />} />

        {/* 管理后台页面 - 带侧边栏布局 */}
        <Route element={<AdminLayout />}>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:conversationId" element={<ChatPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/tenants" element={<TenantsPage />} />
          <Route path="/workflows" element={<WorkflowDesignerPage />} />
          <Route path="/workflows/:workflowId/edit" element={<WorkflowDesignerPage />} />
          <Route path="/workflows/:workflowId/run" element={<WorkflowRunnerPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
