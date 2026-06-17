import React, { useEffect, useState } from 'react'
import { Table, Tag, Button, Select, Space, Card, message, Tooltip, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { fetchTickets, submitFeedback, TicketRow } from '../api/client'

const { Option } = Select
const { Text } = Typography

const TEAMS = ['Testing Team','EDI Team','BizTalk Team','Database Team','Network Team','Access Team','Security Team']
const PRIORITIES = ['P1','P2','P3','P4']

const ReviewQueuePage: React.FC = () => {
  const [data, setData] = useState<TicketRow[]>([])
  const [loading, setLoading] = useState(false)
  const [corrections, setCorrections] = useState<Record<number, { team?: string; priority?: string }>>({})
  const [submitting, setSubmitting] = useState<Record<number, boolean>>({})

  const loadFlagged = () => {
    setLoading(true)
    Promise.all([
      fetchTickets(1, 200, 'Flagged'),
      fetchTickets(1, 200, 'Held'),
    ])
      .then(([f, h]) => setData([...f.items, ...h.items]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadFlagged() }, [])

  const updateCorrection = (id: number, field: 'team' | 'priority', value: string) => {
    setCorrections(prev => ({ ...prev, [id]: { ...prev[id], [field]: value } }))
  }

  const approve = async (row: TicketRow) => {
    setSubmitting(prev => ({ ...prev, [row.id]: true }))
    try {
      await submitFeedback({
        ticket_id: row.ticket_id,
        corrected_team: corrections[row.id]?.team,
        corrected_priority: corrections[row.id]?.priority,
        reviewer: 'Manual Review',
        notes: 'Approved from Review Queue',
      })
      message.success(`Ticket ${row.ticket_id} approved.`)
      loadFlagged()
    } catch {
      message.error('Failed to submit feedback.')
    } finally {
      setSubmitting(prev => ({ ...prev, [row.id]: false }))
    }
  }

  const columns: ColumnsType<TicketRow> = [
    { title: 'Ticket ID', dataIndex: 'ticket_id', key: 'ticket_id', width: 120 },
    {
      title: 'Summary', dataIndex: 'summary', key: 'summary', ellipsis: true,
      render: (t: string) => <Tooltip title={t}><span>{t}</span></Tooltip>,
    },
    { title: 'AI Category', dataIndex: 'ai_category', key: 'ai_category', ellipsis: true },
    {
      title: 'AI Priority', dataIndex: 'ai_priority', key: 'ai_priority', width: 80,
      render: (p: string) => <Tag>{p}</Tag>,
    },
    { title: 'AI Team', dataIndex: 'assigned_team', key: 'assigned_team', ellipsis: true },
    {
      title: 'Confidence', dataIndex: 'final_confidence', key: 'final_confidence', width: 100,
      render: (c: number) => (
        <Text type="warning">{c != null ? `${(c * 100).toFixed(0)}%` : '—'}</Text>
      ),
    },
    {
      title: 'Status', dataIndex: 'routing_status', key: 'routing_status', width: 90,
      render: (s: string) => <Tag color={s === 'Flagged' ? 'orange' : 'red'}>{s}</Tag>,
    },
    {
      title: 'Override Team',
      key: 'override_team',
      width: 170,
      render: (_: unknown, row: TicketRow) => (
        <Select
          allowClear
          placeholder="Keep AI team"
          style={{ width: 150 }}
          onChange={(v) => updateCorrection(row.id, 'team', v)}
        >
          {TEAMS.map(t => <Option key={t} value={t}>{t}</Option>)}
        </Select>
      ),
    },
    {
      title: 'Override Priority',
      key: 'override_priority',
      width: 140,
      render: (_: unknown, row: TicketRow) => (
        <Select
          allowClear
          placeholder="Keep AI priority"
          style={{ width: 120 }}
          onChange={(v) => updateCorrection(row.id, 'priority', v)}
        >
          {PRIORITIES.map(p => <Option key={p} value={p}>{p}</Option>)}
        </Select>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_: unknown, row: TicketRow) => (
        <Button
          type="primary"
          size="small"
          loading={submitting[row.id]}
          onClick={() => approve(row)}
        >
          Approve
        </Button>
      ),
    },
  ]

  return (
    <Card
      title={`Review Queue (${data.length} tickets need attention)`}
      extra={<Button onClick={loadFlagged}>Refresh</Button>}
    >
      <Table<TicketRow>
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1400 }}
        pagination={{ pageSize: 20, showTotal: (t) => `${t} pending` }}
        size="middle"
        rowClassName={(row) => row.routing_status === 'Held' ? 'ant-table-row-error' : ''}
      />
    </Card>
  )
}

export default ReviewQueuePage
