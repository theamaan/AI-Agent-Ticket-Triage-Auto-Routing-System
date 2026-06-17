import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: API_BASE })

export interface KpiData {
  total_tickets: number
  auto_routed: number
  auto_route_pct: number
  flagged: number
  held: number
  total_feedback: number
  avg_confidence: number
  team_distribution: { team: string; count: number }[]
  priority_distribution: { priority: string; count: number }[]
  model_accuracy: number | null
  model_f1_macro: number | null
  model_version: string
}

export interface TicketRow {
  id: number
  ticket_id: string
  date: string
  summary: string
  description: string
  reporter: string
  original_category: string
  original_priority: string
  ai_category: string
  ai_priority: string
  assigned_team: string
  assigned_to: string
  final_confidence: number
  routing_status: string
  email_sent: boolean
  created_at: string
}

export interface TicketListResponse {
  total: number
  page: number
  page_size: number
  items: TicketRow[]
}

export const fetchKpi = (): Promise<KpiData> =>
  api.get('/metrics/kpi').then(r => r.data)

export const fetchTickets = (
  page: number,
  pageSize: number,
  routingStatus?: string,
  team?: string
): Promise<TicketListResponse> => {
  const params: Record<string, unknown> = { page, page_size: pageSize }
  if (routingStatus) params.routing_status = routingStatus
  if (team) params.team = team
  return api.get('/tickets', { params }).then(r => r.data)
}

export const submitFeedback = (body: {
  ticket_id: string
  corrected_category?: string
  corrected_priority?: string
  corrected_team?: string
  corrected_assignee?: string
  reviewer?: string
  notes?: string
}) => api.post('/feedback', body).then(r => r.data)

export const uploadExcel = (file: File): Promise<Blob> =>
  api
    .post('/tickets/process', { file }, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    })
    .then(r => r.data)
