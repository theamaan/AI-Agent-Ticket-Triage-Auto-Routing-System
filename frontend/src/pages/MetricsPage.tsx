import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Alert, Spin, Progress, Typography } from 'antd'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { fetchKpi, KpiData } from '../api/client'

const { Title, Text, Paragraph } = Typography

const MetricsPage: React.FC = () => {
  const [kpi, setKpi] = useState<KpiData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchKpi()
      .then(setKpi)
      .catch(() => setError('Could not load metrics. Is the API running?'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  if (error || !kpi) return <Alert type="error" message={error ?? 'Unknown error'} />

  const accuracyPct = kpi.model_accuracy != null ? Math.round(kpi.model_accuracy * 100) : null
  const f1Pct = kpi.model_f1_macro != null ? Math.round(kpi.model_f1_macro * 100) : null

  const kpiTargets = [
    { label: 'Model Accuracy', achieved: accuracyPct ?? 0, target: 85 },
    { label: 'Auto-Route Rate', achieved: kpi.auto_route_pct, target: 70 },
    { label: 'Avg Confidence', achieved: Math.round(kpi.avg_confidence * 100), target: 80 },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        Model Performance & KPI Report
      </Title>

      {/* ── Model Accuracy Cards ─────────────────────────────────────────── */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card title="Model Version">
            <Text>{kpi.model_version}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card title="Accuracy">
            {accuracyPct != null ? (
              <>
                <Statistic value={accuracyPct} suffix="%" valueStyle={{ color: accuracyPct >= 80 ? '#52c41a' : '#fa8c16' }} />
                <Progress
                  percent={accuracyPct}
                  strokeColor={accuracyPct >= 80 ? '#52c41a' : '#fa8c16'}
                  size="small"
                  style={{ marginTop: 8 }}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>KRA Target: ≥85%</Text>
              </>
            ) : (
              <Text type="secondary">Train the model first: python src/ml/trainer.py</Text>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card title="F1 Score (Macro)">
            {f1Pct != null ? (
              <>
                <Statistic value={f1Pct} suffix="%" valueStyle={{ color: f1Pct >= 75 ? '#52c41a' : '#fa8c16' }} />
                <Progress percent={f1Pct} strokeColor={f1Pct >= 75 ? '#52c41a' : '#fa8c16'} size="small" style={{ marginTop: 8 }} />
              </>
            ) : (
              <Text type="secondary">—</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* ── KPI vs Target Bar Chart ──────────────────────────────────────── */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="KPI vs Target">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={kpiTargets} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="label" width={120} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="achieved" name="Achieved" radius={[0,4,4,0]}>
                  {kpiTargets.map((entry, i) => (
                    <Cell key={i} fill={entry.achieved >= entry.target ? '#52c41a' : '#fa8c16'} />
                  ))}
                </Bar>
                <Bar dataKey="target" name="Target" fill="#d9d9d9" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="KRA Achievements Summary">
            <Paragraph>
              <Text strong>✓ Data Generation:</Text> 350 synthetic labeled tickets across 7 teams.
            </Paragraph>
            <Paragraph>
              <Text strong>✓ Classifier Model:</Text> TF-IDF + Logistic Regression — target 70–80% accuracy.
            </Paragraph>
            <Paragraph>
              <Text strong>✓ Multi-Agent Pipeline:</Text> Classifier → Priority → Routing → Confidence agents.
            </Paragraph>
            <Paragraph>
              <Text strong>✓ Auto-Routing:</Text> Excel batch processing with confidence thresholds (0.85/0.65).
            </Paragraph>
            <Paragraph>
              <Text strong>✓ Email Notification:</Text> Gmail SMTP real cloud action on auto-route.
            </Paragraph>
            <Paragraph>
              <Text strong>✓ Feedback Loop:</Text> Human corrections stored; retraining triggered at threshold.
            </Paragraph>
          </Card>
        </Col>
      </Row>

      {/* ── Routing Outcome Bar ──────────────────────────────────────────── */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="Routing Outcome Breakdown">
            <Row gutter={16}>
              {[
                { label: 'Auto-Routed', count: kpi.auto_routed, total: kpi.total_tickets, colour: '#52c41a' },
                { label: 'Flagged', count: kpi.flagged, total: kpi.total_tickets, colour: '#fa8c16' },
                { label: 'Held', count: kpi.held, total: kpi.total_tickets, colour: '#f5222d' },
              ].map(item => (
                <Col key={item.label} xs={24} sm={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Statistic title={item.label} value={item.count} />
                    <Progress
                      type="circle"
                      percent={item.total > 0 ? Math.round((item.count / item.total) * 100) : 0}
                      strokeColor={item.colour}
                      size={80}
                      style={{ marginTop: 8 }}
                    />
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default MetricsPage
