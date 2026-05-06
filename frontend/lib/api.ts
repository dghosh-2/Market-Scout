import axios from 'axios';
import { getApiBase } from './env';

const api = axios.create({
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  config.baseURL = getApiBase();
  return config;
});

export interface ResearchRequest {
  query: string;
  omit_sections?: string[];
  add_sections?: string[];
}

export interface ResearchResponse {
  success: boolean;
  message: string;
  report_id?: string;
  report_path?: string;
  company?: string;
}

export interface FeedbackRequest {
  report_id: string;
  feedback: string;
}

export interface Report {
  id: string;
  query_id?: string;
  company: string;
  ticker?: string;
  report_path: string;
  created_at: string;
  version: number;
}

export const researchApi = {
  createResearch: async (body: ResearchRequest): Promise<ResearchResponse> => {
    const response = await api.post('/research', body);
    return response.data;
  },

  getResearchStatus: async (reportId: string) => {
    const response = await api.get(`/research/status/${reportId}`);
    return response.data;
  },
};

export const papersApi = {
  getAllPapers: async () => {
    const response = await api.get('/papers');
    return response.data;
  },

  getCompanyPapers: async (companyOrTicker: string) => {
    const response = await api.get(`/papers/${encodeURIComponent(companyOrTicker)}`);
    return response.data;
  },

  getPaper: async (reportId: string) => {
    const response = await api.get(`/papers/report/${reportId}`);
    return response.data;
  },
};

export const feedbackApi = {
  submitFeedback: async (reportId: string, feedback: string) => {
    const response = await api.post('/feedback', { report_id: reportId, feedback });
    return response.data;
  },
};

export interface Holding {
  id: string;
  ticker: string;
  shares: number;
  company_name: string;
  current_price?: number;
  value?: number;
  weight?: number;
  sector?: string;
  created_at: string;
}

export interface PortfolioSummary {
  holdings: Holding[];
  total_value: number;
  total_holdings: number;
}

export const portfolioApi = {
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get('/portfolio/summary');
    return response.data;
  },

  addHolding: async (ticker: string, shares: number, companyName?: string) => {
    const response = await api.post('/portfolio', {
      ticker,
      shares,
      company_name: companyName,
    });
    return response.data;
  },

  updateHolding: async (ticker: string, shares: number) => {
    const response = await api.put(`/portfolio/${ticker}`, { shares });
    return response.data;
  },

  deleteHolding: async (ticker: string) => {
    const response = await api.delete(`/portfolio/${ticker}`);
    return response.data;
  },
};

export default api;
