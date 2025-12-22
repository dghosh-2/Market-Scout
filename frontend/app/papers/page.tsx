'use client';

import { useState, useEffect } from 'react';
import NavBar from '../../components/NavBar';
import Link from 'next/link';

const API_BASE = 'http://localhost:8000/api';

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

  useEffect(() => {
    fetchPapers();
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
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const extractTicker = (company: string) => {
    const match = company.match(/\(([^)]+)\)/);
    return match ? match[1] : company.slice(0, 4).toUpperCase();
  };

  const getLogoUrl = (company: string) => {
    const ticker = extractTicker(company);
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
    const domain = domains[ticker] || `${ticker.toLowerCase()}.com`;
    return `https://logo.clearbit.com/${domain}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">My Papers</h1>
          <p className="text-gray-600">View and download your research reports</p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!loading && !error && groups.length === 0 && (
          <div className="text-center py-20">
            <p className="text-gray-500 mb-4">No research reports yet</p>
            <Link
              href="/research"
              className="inline-block px-6 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
            >
              Generate Your First Report
            </Link>
          </div>
        )}

        {!loading && groups.length > 0 && (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group.company} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="p-5 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <img
                      src={getLogoUrl(group.company)}
                      alt={group.company}
                      className="w-12 h-12 rounded-lg object-contain bg-white border border-gray-100"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">{group.company}</h2>
                      <p className="text-sm text-gray-500">{group.report_count} report{group.report_count !== 1 ? 's' : ''}</p>
                    </div>
                  </div>
                  <Link
                    href={`/papers/${encodeURIComponent(extractTicker(group.company))}`}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View All
                  </Link>
                </div>
                
                <div className="divide-y divide-gray-100">
                  {group.reports.slice(0, 3).map((report) => (
                    <div key={report.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Version {report.version}</p>
                        <p className="text-xs text-gray-500">{formatDate(report.created_at)}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Link
                          href={`/papers/${encodeURIComponent(extractTicker(group.company))}?report=${report.id}`}
                          className="text-sm text-gray-600 hover:text-gray-900"
                        >
                          Details
                        </Link>
                        <a
                          href={`http://localhost:8000${report.report_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                        >
                          Download
                        </a>
                      </div>
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
