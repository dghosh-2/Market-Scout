'use client';

import { useState, useEffect, Suspense } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import NavBar from '../../../components/NavBar';
import Link from 'next/link';
import { getApiBase, getBackendOrigin } from '../../../lib/env';

interface Report {
  id: string;
  company: string;
  version: number;
  created_at: string;
  report_path: string;
}

function CompanyPapersInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const company = decodeURIComponent(params.company as string);
  const selectedReportId = searchParams.get('report');

  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [feedbackById, setFeedbackById] = useState<Record<string, string>>({});
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  const API_BASE = getApiBase();
  const BACKEND_BASE = getBackendOrigin();

  useEffect(() => {
    void fetchReports();
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
    });
  };

  const handleFeedback = async (reportId: string) => {
    const feedback = (feedbackById[reportId] || '').trim();
    if (!feedback) return;

    setSubmittingId(reportId);
    setFeedbackSuccess('');
    setError('');

    try {
      const res = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId, feedback }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || data.detail || 'Failed to submit feedback');
      }

      setFeedbackSuccess('New version generated.');
      setFeedbackById((prev) => ({ ...prev, [reportId]: '' }));
      await fetchReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setSubmittingId(null);
    }
  };

  const setFeedback = (reportId: string, value: string) => {
    setFeedbackById((prev) => ({ ...prev, [reportId]: value }));
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <NavBar />

      <main className="max-w-3xl mx-auto px-6 py-14">
        <Link href="/papers" className="text-[10px] uppercase tracking-widest text-white/45 hover:text-white">
          ← Papers
        </Link>

        <h1 className="mt-8 text-2xl font-extralight tracking-[0.15em] uppercase">{company}</h1>
        <p className="text-sm text-white/40 font-light mt-2">
          {reports.length} report{reports.length !== 1 ? 's' : ''}
        </p>

        {loading && <p className="text-white/40 mt-12 text-sm">Loading…</p>}

        {error && (
          <div className="mt-6 border border-white/15 px-4 py-3 text-sm text-white/70 rounded-sm">{error}</div>
        )}

        {feedbackSuccess && (
          <div className="mt-6 border border-white/20 px-4 py-3 text-sm text-white/80 rounded-sm">{feedbackSuccess}</div>
        )}

        {!loading && reports.length > 0 && (
          <div className="mt-10 space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className={`border rounded-sm overflow-hidden ${
                  selectedReportId === report.id ? 'border-white/40' : 'border-white/10'
                }`}
              >
                <div className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10">
                  <div>
                    <h3 className="text-xs uppercase tracking-widest text-white/50">Version {report.version}</h3>
                    <p className="text-[11px] text-white/35 mt-1">{formatDate(report.created_at)}</p>
                  </div>
                  <a
                    href={`${BACKEND_BASE}${report.report_path}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] uppercase tracking-widest px-4 py-2 bg-white text-black rounded-sm text-center hover:bg-white/90"
                  >
                    PDF
                  </a>
                </div>

                <div className="px-5 py-4">
                  <p className="text-[10px] uppercase tracking-widest text-white/35 mb-2">Feedback</p>
                  <div className="flex flex-col gap-2">
                    <textarea
                      value={feedbackById[report.id] || ''}
                      onChange={(e) => setFeedback(report.id, e.target.value)}
                      placeholder="What should change?"
                      rows={2}
                      className="w-full bg-white/[0.03] border border-white/10 px-3 py-2 text-sm outline-none font-light placeholder:text-white/25"
                    />
                    <button
                      type="button"
                      onClick={() => void handleFeedback(report.id)}
                      disabled={submittingId === report.id || !(feedbackById[report.id] || '').trim()}
                      className="self-start text-[10px] uppercase tracking-widest px-4 py-2 border border-white/25 rounded-sm hover:bg-white/5 disabled:opacity-30"
                    >
                      {submittingId === report.id ? '…' : 'Regenerate'}
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

export default function CompanyPapersPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black text-white flex items-center justify-center text-sm font-light">
          Loading…
        </div>
      }
    >
      <CompanyPapersInner />
    </Suspense>
  );
}
