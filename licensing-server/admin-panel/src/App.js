import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  LicenseOutlined,
  KeyOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Licenses from './pages/Licenses';
import OpenAIKeys from './pages/OpenAIKeys';
import ScripMaster from './pages/ScripMaster';
import './App.css';

const { Header, Content, Sider } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/licenses',
      icon: <LicenseOutlined />,
      label: 'Licenses',
    },
    {
      key: '/openai-keys',
      icon: <KeyOutlined />,
      label: 'OpenAI Keys',
    },
    {
      key: '/scrip-master',
      icon: <FileTextOutlined />,
      label: 'Scrip Master',
    },
  ];

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
          <div
            style={{
              height: 32,
              margin: 16,
              textAlign: 'center',
              fontSize: collapsed ? 20 : 18,
              fontWeight: 'bold',
              color: 'white',
            }}
          >
            {collapsed ? '🧞' : '🧞 TradeYoda'}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            defaultSelectedKeys={[window.location.pathname]}
            items={menuItems}
            onClick={({ key }) => {
              window.location.pathname = key;
            }}
          />
        </Sider>
        <Layout>
          <Header
            style={{
              padding: '0 24px',
              background: colorBgContainer,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <h2 style={{ margin: 0 }}>Licensing Admin Panel</h2>
            <div style={{ color: '#666', fontSize: 14 }}>
              API: {process.env.REACT_APP_API_URL || 'http://localhost:8100'}
            </div>
          </Header>
          <Content style={{ margin: '24px 16px', padding: 24, background: colorBgContainer }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/licenses" element={<Licenses />} />
              <Route path="/openai-keys" element={<OpenAIKeys />} />
              <Route path="/scrip-master" element={<ScripMaster />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
