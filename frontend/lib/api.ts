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

export interface Holding {
  id: string
  ticker: string
  shares: number
  company_name: string
  current_price?: number
  value?: number
  weight?: number
  sector?: string
  created_at: string
}

export interface PortfolioSummary {
  holdings: Holding[]
  total_value: number
  total_holdings: number
}

export const portfolioApi = {
  getPortfolio: async (): Promise<{ holdings: Holding[], total_holdings: number }> => {
    const response = await api.get('/portfolio')
    return response.data
  },

  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get('/portfolio/summary')
    return response.data
  },

  addHolding: async (ticker: string, shares: number, companyName?: string) => {
    const response = await api.post('/portfolio', {
      ticker,
      shares,
      company_name: companyName
    })
    return response.data
  },

  updateHolding: async (ticker: string, shares: number) => {
    const response = await api.put(`/portfolio/${ticker}`, { shares })
    return response.data
  },

  deleteHolding: async (ticker: string) => {
    const response = await api.delete(`/portfolio/${ticker}`)
    return response.data
  },
}

export default api

