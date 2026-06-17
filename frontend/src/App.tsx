import React from 'react'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import AppLayout from './components/AppLayout'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import TicketTablePage from './pages/TicketTablePage'
import ReviewQueuePage from './pages/ReviewQueuePage'
import MetricsPage from './pages/MetricsPage'

const App: React.FC = () => (
  <ConfigProvider
    theme={{
      algorithm: theme.defaultAlgorithm,
      token: {
        colorPrimary: '#1677ff',
        borderRadius: 6,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif",
      },
    }}
  >
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/tickets" element={<TicketTablePage />} />
          <Route path="/review" element={<ReviewQueuePage />} />
          <Route path="/metrics" element={<MetricsPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  </ConfigProvider>
)

export default App
