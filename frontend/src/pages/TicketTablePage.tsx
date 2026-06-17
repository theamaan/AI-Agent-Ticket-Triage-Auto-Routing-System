import React, { useEffect, useState } from 'react'
import { Table, Tag, Select, Space, Card, Input, Typography, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { fetchTickets, TicketRow } from '../api/client'

const { Option } = Select
const { Text } = Typography

const PRIORITY_CLASS: Record<string, string> = {
  P1: 'priority-p1', P2: 'priority-p2', P3: 'priority-p3', P4: 'priority-p4',
}

const STATUS_CLASS: Record<string, string> = {
  'Auto-Routed': 'status-auto',
  'Flagged': 'status-flagged',
  'Held': 'status-held',
}

const columns: ColumnsType<TicketRow> = [
  { title: 'Ticket ID', dataIndex: 'ticket_id', key: 'ticket_id', width: 120, fixed: 'left', sorter: true },
  {
    title: 'Summary',
    dataIndex: 'summary',
    key: 'summary',
    ellipsis: true,
    render: (text: string) => (
      <Tooltip title={text}><span>{text}</span></Tooltip>
    ),
  },
  { title: 'AI Category', dataIndex: 'ai_category', key: 'ai_category', ellipsis: true },
  {
    title: 'Priority',
    dataIndex: 'ai_priority',
    key: 'ai_priority',
    width: 90,
    render: (p: string) => <Tag className={PRIORITY_CLASS[p] ?? ''}>{p}</Tag>,
    sorter: true,
  },
  { title: 'Team', dataIndex: 'assigned_team', key: 'assigned_team', ellipsis: true },
  { title: 'Assigned To', dataIndex: 'assigned_to', key: 'assigned_to', ellipsis: true },
  {
    title: 'Confidence',
    dataIndex: 'final_confidence',
    key: 'final_confidence',
    width: 110,
    render: (c: number) => (
      <Text style={{ color: c >= 0.85 ? '#52c41a' : c >= 0.65 ? '#fa8c16' : '#f5222d' }}>
        {c != null ? `${(c * 100).toFixed(0)}%` : '—'}
      </Text>
    ),
    sorter: true,
  },
  {
    title: 'Status',
    dataIndex: 'routing_status',
    key: 'routing_status',
    width: 120,
    render: (s: string) => <span className={STATUS_CLASS[s] ?? ''}>{s}</span>,
  },
  {
    title: 'Email Sent',
    dataIndex: 'email_sent',
    key: 'email_sent',
    width: 100,
    render: (sent: boolean) => <Tag color={sent ? 'green' : 'default'}>{sent ? 'Yes' : 'No'}</Tag>,
  },
]

const TicketTablePage: React.FC = () => {
  const [data, setData] = useState<TicketRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [loading, setLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterTeam, setFilterTeam] = useState<string | undefined>()

  const load = (p: number, status?: string, team?: string) => {
    setLoading(true)
    fetchTickets(p, pageSize, status, team)
      .then(r => { setData(r.items); setTotal(r.total) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [])

  const handleFilter = (status?: string, team?: string) => {
    setPage(1)
    load(1, status, team)
  }

  return (
    <Card
      title="All Processed Tickets"
      extra={
        <Space>
          <Select
            allowClear
            placeholder="Filter by Status"
            style={{ width: 160 }}
            onChange={(v) => { setFilterStatus(v); handleFilter(v, filterTeam) }}
          >
            <Option value="Auto-Routed">Auto-Routed</Option>
            <Option value="Flagged">Flagged</Option>
            <Option value="Held">Held</Option>
          </Select>
          <Select
            allowClear
            placeholder="Filter by Team"
            style={{ width: 160 }}
            onChange={(v) => { setFilterTeam(v); handleFilter(filterStatus, v) }}
          >
            {['Testing Team','EDI Team','BizTalk Team','Database Team','Network Team','Access Team','Security Team'].map(t => (
              <Option key={t} value={t}>{t}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table<TicketRow>
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: false,
          showTotal: (t) => `${t} tickets`,
          onChange: (p) => { setPage(p); load(p, filterStatus, filterTeam) },
        }}
        size="middle"
      />
    </Card>
  )
}

export default TicketTablePage
