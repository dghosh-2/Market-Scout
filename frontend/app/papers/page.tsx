'use client';

import { useState, useEffect } from 'react';
import NavBar from '../../components/NavBar';
import Link from 'next/link';
import { getApiBase, getBackendOrigin } from '../../lib/env';

interface Report {
  id: string;
  company: string;
  version: number;
  created_at: string;
  report_path: string;
}

interface CompanyGroup {
  company: string;
  report_count: number;
  reports: Report[];
}

export default function PapersPage() {
  const [groups, setGroups] = useState<CompanyGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const API_BASE = getApiBase();
  const BACKEND_BASE = getBackendOrigin();

  useEffect(() => {
    void fetchPapers();
  }, []);

  const fetchPapers = async () => {
    try {
      const res = await fetch(`${API_BASE}/papers`);
      if (!res.ok) throw new Error('Failed to fetch papers');
      const data = await res.json();
      setGroups(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load papers');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const extractTicker = (company: string) => {
    const match = company.match(/\(([^)]+)\)/);
    return match ? match[1] : company.slice(0, 4).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <NavBar />

      <main className="max-w-4xl mx-auto px-6 py-14">
        <p className="text-[10px] tracking-[0.35em] uppercase text-white/45 mb-3">Archive</p>
        <h1 className="text-2xl font-extralight tracking-[0.12em] uppercase mb-4">Papers</h1>
        <p className="text-sm text-white/40 font-light mb-10">Prior runs, by issuer.</p>

        {loading && <p className="text-white/40 text-sm font-light py-16">Loading…</p>}

        {error && (
          <div className="border border-white/15 px-4 py-3 text-sm text-white/70 mb-6 rounded-sm">{error}</div>
        )}

        {!loading && !error && groups.length === 0 && (
          <div className="border border-white/10 rounded-sm py-16 text-center">
            <p className="text-white/45 text-sm mb-6">Nothing yet.</p>
            <Link
              href="/research"
              className="text-[10px] uppercase tracking-[0.25em] text-white border border-white/25 px-5 py-2 rounded-sm inline-block hover:bg-white/5"
            >
              Run research
            </Link>
          </div>
        )}

        {!loading && groups.length > 0 && (
          <div className="space-y-4">
            {groups.map((group) => (
              <div key={group.company} className="border border-white/10 rounded-sm overflow-hidden">
                <div className="px-5 py-4 flex items-center justify-between gap-4 border-b border-white/10">
                  <div>
                    <h2 className="text-sm font-light tracking-wide">{group.company}</h2>
                    <p className="text-[10px] uppercase tracking-widest text-white/35 mt-1">
                      {group.report_count} report{group.report_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <Link
                    href={`/papers/${encodeURIComponent(extractTicker(group.company))}`}
                    className="text-[10px] uppercase tracking-widest text-white/50 hover:text-white shrink-0"
                  >
                    Open
                  </Link>
                </div>
                <div className="divide-y divide-white/5">
                  {group.reports.slice(0, 4).map((report) => (
                    <div key={report.id} className="px-5 py-3 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs text-white/80">Version {report.version}</p>
                        <p className="text-[10px] text-white/35 mt-0.5">{formatDate(report.created_at)}</p>
                      </div>
                      <a
                        href={`${BACKEND_BASE}${report.report_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] uppercase tracking-widest px-3 py-1.5 border border-white/20 rounded-sm hover:bg-white/5"
                      >
                        PDF
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
