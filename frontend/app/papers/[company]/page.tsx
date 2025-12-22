'use client';

import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import NavBar from '../../../components/NavBar';
import Link from 'next/link';

const API_BASE = 'http://localhost:8000/api';

interface Report {
  id: string;
  company: string;
  version: number;
  created_at: string;
  report_path: string;
}

export default function CompanyPapersPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const company = decodeURIComponent(params.company as string);
  const selectedReportId = searchParams.get('report');

  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  useEffect(() => {
    fetchReports();
  }, [company]);

  const fetchReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/papers/${encodeURIComponent(company)}`);
      if (!res.ok) throw new Error('Failed to fetch reports');
      const data = await res.json();
      setReports(data.reports || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleFeedback = async (reportId: string) => {
    if (!feedback.trim()) return;

    setSubmitting(true);
    setFeedbackSuccess('');

    try {
      const res = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId, feedback })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Failed to submit feedback');
      }

      setFeedbackSuccess('New report generated successfully!');
      setFeedback('');
      fetchReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  const getLogoUrl = () => {
    const domains: Record<string, string> = {
      'AAPL': 'apple.com',
      'MSFT': 'microsoft.com',
      'GOOGL': 'google.com',
      'AMZN': 'amazon.com',
      'META': 'meta.com',
      'TSLA': 'tesla.com',
      'NVDA': 'nvidia.com',
      'TSM': 'tsmc.com',
    };
    const domain = domains[company] || `${company.toLowerCase()}.com`;
    return `https://logo.clearbit.com/${domain}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-6">
          <Link href="/papers" className="text-sm text-blue-600 hover:text-blue-800">
            Back to All Papers
          </Link>
        </div>

        <div className="flex items-center gap-4 mb-10">
          <img
            src={getLogoUrl()}
            alt={company}
            className="w-16 h-16 rounded-lg object-contain bg-white border border-gray-200"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          <div>
            <h1 className="text-3xl font-semibold text-gray-900">{company}</h1>
            <p className="text-gray-600">{reports.length} research report{reports.length !== 1 ? 's' : ''}</p>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {feedbackSuccess && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-700">{feedbackSuccess}</p>
          </div>
        )}

        {!loading && reports.length > 0 && (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className={`bg-white border rounded-lg overflow-hidden ${
                  selectedReportId === report.id ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-200'
                }`}
              >
                <div className="p-5 flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Version {report.version}</h3>
                    <p className="text-sm text-gray-500">{formatDate(report.created_at)}</p>
                  </div>
                  <a
                    href={`http://localhost:8000${report.report_path}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-2.5 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
                  >
                    Download PDF
                  </a>
                </div>

                <div className="px-5 pb-5 border-t border-gray-100 pt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Request Updated Report</p>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={selectedReportId === report.id ? feedback : ''}
                      onChange={(e) => {
                        if (selectedReportId === report.id || !selectedReportId) {
                          setFeedback(e.target.value);
                        }
                      }}
                      onFocus={() => {
                        window.history.replaceState({}, '', `?report=${report.id}`);
                      }}
                      placeholder="e.g., Include more detail on dividends, focus on recent acquisitions..."
                      className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                    <button
                      onClick={() => handleFeedback(report.id)}
                      disabled={submitting || !feedback.trim()}
                      className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {submitting ? 'Generating...' : 'Generate New'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
