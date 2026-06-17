import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin, Alert, Progress } from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PauseCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { fetchKpi, KpiData } from '../api/client'

const TEAM_COLOURS = [
  '#1677ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96',
]
const PRIORITY_COLOURS: Record<string, string> = {
  P1: '#f5222d', P2: '#fa8c16', P3: '#1677ff', P4: '#52c41a',
}

const DashboardPage: React.FC = () => {
  const [kpi, setKpi] = useState<KpiData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchKpi()
      .then(setKpi)
      .catch(() => setError('Could not load KPI data. Is the API running?'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  if (error || !kpi) return <Alert type="error" message={error ?? 'Unknown error'} />

  return (
    <div>
      {/* ── KPI Stat Cards ─────────────────────────────────────────────── */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Tickets Processed"
              value={kpi.total_tickets}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Auto-Routed"
              value={kpi.auto_route_pct}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress
              percent={kpi.auto_route_pct}
              showInfo={false}
              strokeColor="#52c41a"
              size="small"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Flagged for Review"
              value={kpi.flagged}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Held (Low Confidence)"
              value={kpi.held}
              prefix={<PauseCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* ── Secondary Stats ─────────────────────────────────────────────── */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Average AI Confidence"
              value={(kpi.avg_confidence * 100).toFixed(1)}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Model Accuracy"
              value={kpi.model_accuracy != null ? (kpi.model_accuracy * 100).toFixed(1) : '—'}
              suffix={kpi.model_accuracy != null ? '%' : ''}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Human Corrections" value={kpi.total_feedback} />
          </Card>
        </Col>
      </Row>

      {/* ── Charts ──────────────────────────────────────────────────────── */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="Ticket Volume by Team">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={kpi.team_distribution} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="team" angle={-30} textAnchor="end" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" name="Tickets">
                  {kpi.team_distribution.map((_, i) => (
                    <Cell key={i} fill={TEAM_COLOURS[i % TEAM_COLOURS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Priority Distribution">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={kpi.priority_distribution}
                  dataKey="count"
                  nameKey="priority"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ priority, percent }) => `${priority} ${(percent * 100).toFixed(0)}%`}
                >
                  {kpi.priority_distribution.map((entry, i) => (
                    <Cell key={i} fill={PRIORITY_COLOURS[entry.priority] ?? '#8884d8'} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
