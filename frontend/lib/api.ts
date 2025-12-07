import axios from 'axios'

// Create axios instance with base URL
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface ResearchRequest {
  query: string
}

export interface ResearchResponse {
  success: boolean
  message: string
  report_id?: number
  report_path?: string
  company?: string
}

export interface FeedbackRequest {
  report_id: number
  feedback: string
}

export interface Report {
  id: number
  query_id: number
  company: string
  report_path: string
  created_at: string
  version: number
}

export interface ReportWithQuery extends Report {
  query: {
    id: number
    date: string
    time: string
    request: string
    company: string
    timestamp: string
  }
}

export interface CompanyReportsResponse {
  company: string
  reports: Report[]
  total_reports: number
}

// API functions
export const researchApi = {
  // Create new research report
  createResearch: async (query: string): Promise<ResearchResponse> => {
    const response = await api.post('/research', { query })
    return response.data
  },

  // Get research status
  getResearchStatus: async (reportId: number) => {
    const response = await api.get(`/research/status/${reportId}`)
    return response.data
  },
}

export const papersApi = {
  // Get all papers
  getAllPapers: async (): Promise<ReportWithQuery[]> => {
    const response = await api.get('/papers')
    return response.data
  },

  // Get companies with papers
  getCompanies: async (): Promise<{ companies: string[] }> => {
    const response = await api.get('/papers/companies')
    return response.data
  },

  // Get papers by company
  getCompanyPapers: async (company: string): Promise<CompanyReportsResponse> => {
    const response = await api.get(`/papers/company/${encodeURIComponent(company)}`)
    return response.data
  },

  // Get single paper
  getPaper: async (reportId: number): Promise<ReportWithQuery> => {
    const response = await api.get(`/papers/${reportId}`)
    return response.data
  },

  // Download paper (returns blob URL)
  downloadPaper: async (reportId: number): Promise<string> => {
    const response = await api.get(`/papers/download/${reportId}`, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    return URL.createObjectURL(blob)
  },

  // Delete paper
  deletePaper: async (reportId: number): Promise<void> => {
    await api.delete(`/papers/${reportId}`)
  },
}

export const feedbackApi = {
  // Submit feedback and regenerate report
  submitFeedback: async (reportId: number, feedback: string): Promise<ResearchResponse> => {
    const response = await api.post('/feedback', { report_id: reportId, feedback })
    return response.data
  },

  // Get feedback history
  getFeedbackHistory: async (reportId: number) => {
    const response = await api.get(`/feedback/history/${reportId}`)
    return response.data
  },
}

export default api

