import React, { useState } from 'react'
import { Layout, Menu, Typography, theme } from 'antd'
import {
  DashboardOutlined,
  UploadOutlined,
  UnorderedListOutlined,
  ExclamationCircleOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const { Sider, Header, Content, Footer } = Layout
const { Text } = Typography

const NAV_ITEMS = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/upload',    icon: <UploadOutlined />,    label: 'Upload Tickets' },
  { key: '/tickets',  icon: <UnorderedListOutlined />, label: 'All Tickets' },
  { key: '/review',   icon: <ExclamationCircleOutlined />, label: 'Review Queue' },
  { key: '/metrics',  icon: <BarChartOutlined />,   label: 'Model Metrics' },
]

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
        style={{ position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100 }}
      >
        {/* Logo / Brand */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 16px',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <DashboardOutlined style={{ color: '#1677ff', fontSize: 22 }} />
          {!collapsed && (
            <Text
              strong
              style={{ color: '#fff', marginLeft: 10, fontSize: 15, whiteSpace: 'nowrap' }}
            >
              Ticket Triage AI
            </Text>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={NAV_ITEMS}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8, border: 'none' }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: '0 24px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            display: 'flex',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 99,
          }}
        >
          <Text style={{ fontSize: 16, fontWeight: 500, color: token.colorTextHeading }}>
            {NAV_ITEMS.find(n => n.key === location.pathname)?.label ?? 'Ticket Triage AI'}
          </Text>
        </Header>

        <Content style={{ margin: '24px 24px 0', overflow: 'initial' }}>
          {children}
        </Content>

        <Footer style={{ textAlign: 'center', color: token.colorTextSecondary, fontSize: 12 }}>
          AI Ticket Triage System — Open Source Build © {new Date().getFullYear()}
        </Footer>
      </Layout>
    </Layout>
  )
}

export default AppLayout
