import React, { useState } from 'react'
import { Card, Upload, Button, Steps, Alert, Typography, Space, Result } from 'antd'
import { InboxOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import type { RcFile } from 'antd/es/upload'
import { uploadExcel } from '../api/client'

const { Dragger } = Upload
const { Text } = Typography

type StepStatus = 'wait' | 'process' | 'finish' | 'error'

interface StepState {
  current: number
  status: StepStatus
}

const STEPS = [
  { title: 'Upload', description: 'Select .xlsx file' },
  { title: 'Processing', description: 'AI agents running' },
  { title: 'Complete', description: 'Download results' },
]

const UploadPage: React.FC = () => {
  const [stepState, setStepState] = useState<StepState>({ current: 0, status: 'process' })
  const [resultBlob, setResultBlob] = useState<Blob | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reset = () => {
    setStepState({ current: 0, status: 'process' })
    setResultBlob(null)
    setError(null)
  }

  const handleUpload = async (file: RcFile) => {
    setError(null)
    setResultBlob(null)
    setStepState({ current: 1, status: 'process' })

    try {
      const blob = await uploadExcel(file as File)
      setResultBlob(blob)
      setStepState({ current: 2, status: 'finish' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Check API connection.'
      setError(msg)
      setStepState({ current: 1, status: 'error' })
    }
    return false // prevent antd default upload
  }

  const downloadResult = () => {
    if (!resultBlob) return
    const url = URL.createObjectURL(resultBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'triage_results.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Steps current={stepState.current} status={stepState.status} items={STEPS} />
      </Card>

      {error && (
        <Alert type="error" showIcon closable message={error} onClose={() => setError(null)} />
      )}

      {stepState.current === 0 || stepState.status === 'error' ? (
        <Card title="Upload Ticket File">
          <Dragger
            accept=".xlsx"
            beforeUpload={handleUpload}
            showUploadList={false}
            multiple={false}
            style={{ padding: '24px 0' }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: 48, color: '#1677ff' }} />
            </p>
            <p className="ant-upload-text">
              Click or drag an Excel file (.xlsx) here to upload
            </p>
            <p className="ant-upload-hint">
              Required columns: <Text code>Summary</Text> and <Text code>Description</Text>.
              Optional: Ticket_ID, Date, Reporter, Category, Priority, Status.
            </p>
          </Dragger>
        </Card>
      ) : stepState.current === 1 ? (
        <Card>
          <Result
            status="info"
            icon={<ReloadOutlined spin style={{ fontSize: 48, color: '#1677ff' }} />}
            title="Processing tickets…"
            subTitle="AI agents are classifying, prioritising, and routing your tickets. This may take a moment."
          />
        </Card>
      ) : (
        <Card>
          <Result
            status="success"
            title="Triage Complete!"
            subTitle="Your tickets have been processed. Download the enriched Excel file below."
            extra={[
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                size="large"
                onClick={downloadResult}
                key="download"
              >
                Download triage_results.xlsx
              </Button>,
              <Button onClick={reset} key="again">
                Process Another File
              </Button>,
            ]}
          />
        </Card>
      )}

      <Card title="Expected Input Format" size="small">
        <Text type="secondary">
          Your Excel file should include at minimum <Text code>Summary</Text> and <Text code>Description</Text> columns.
          The system will add: <Text code>AI_Category</Text>, <Text code>AI_Priority</Text>, <Text code>Assigned_Team_AI</Text>,{' '}
          <Text code>Assigned_To</Text>, <Text code>Final_Confidence</Text>, <Text code>Routing_Status</Text>, <Text code>Email_Sent</Text>.
        </Text>
      </Card>
    </Space>
  )
}

export default UploadPage
