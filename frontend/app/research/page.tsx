'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import NavBar from '../../components/NavBar';
import { getApiBase, getBackendOrigin } from '../../lib/env';
import { feedbackApi, papersApi } from '../../lib/api';

interface PricePoint {
  date: string;
  close: number;
}

interface CompanyInfo {
  name: string;
  ticker: string;
  sector: string;
  industry: string;
  market_cap: number;
}

interface ReportRow {
  id: string;
  version: number;
  created_at: string;
  report_path: string;
  company?: string;
  ticker?: string;
}

type StreamPayload = {
  step: string;
  message: string;
  ticker?: string;
  company_name?: string;
  report_id?: string;
  report_path?: string;
  company?: string;
  company_info?: Record<string, unknown>;
  price_data?: { prices?: PricePoint[] };
};

function ResearchPageInner() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamMessage, setStreamMessage] = useState('');
  const [error, setError] = useState('');
  const [reportPath, setReportPath] = useState('');
  const [reportId, setReportId] = useState<string | null>(null);
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [priceData, setPriceData] = useState<PricePoint[]>([]);
  const [versions, setVersions] = useState<ReportRow[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [viewAnalysis, setViewAnalysis] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState('');
  const [feedbackBusy, setFeedbackBusy] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const esRef = useRef<EventSource | null>(null);

  const API_BASE = getApiBase();
  const BACKEND_BASE = getBackendOrigin();

  useEffect(() => {
    const t = searchParams.get('ticker');
    if (t) setQuery(t.toUpperCase());
  }, [searchParams]);

  const loadVersions = useCallback(async (ticker: string, preferredId?: string | null) => {
    try {
      const data = await papersApi.getCompanyPapers(ticker);
      const list = (data.reports || []) as ReportRow[];
      setVersions(list);
      if (preferredId && list.some((r) => r.id === preferredId)) {
        setSelectedVersionId(preferredId);
      } else if (list.length) {
        setSelectedVersionId(list[0].id);
      }
    } catch {
      setVersions([]);
    }
  }, []);

  const loadReportDetail = useCallback(async (id: string) => {
    try {
      const data = await papersApi.getPaper(id);
      const raw = data.data?.analysis;
      if (typeof raw === 'string' && raw.trim()) {
        try {
          const parsed = JSON.parse(raw) as Record<string, string>;
          setViewAnalysis(parsed);
        } catch {
          setViewAnalysis({});
        }
      } else {
        setViewAnalysis({});
      }
    } catch {
      setViewAnalysis({});
    }
  }, []);

  useEffect(() => {
    if (selectedVersionId) {
      loadReportDetail(selectedVersionId);
    }
  }, [selectedVersionId, loadReportDetail]);

  useEffect(() => {
    if (!selectedVersionId || !versions.length) return;
    const v = versions.find((x) => x.id === selectedVersionId);
    if (v?.report_path) setReportPath(v.report_path);
  }, [selectedVersionId, versions]);

  useEffect(() => {
    if (priceData.length > 0 && canvasRef.current) {
      drawChart();
    }
  }, [priceData]);

  const drawChart = () => {
    const canvas = canvasRef.current;
    if (!canvas || priceData.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 16, bottom: 28, left: 44 };

    ctx.clearRect(0, 0, width, height);

    const prices = priceData.map((p) => p.close);
    const minPrice = Math.min(...prices) * 0.98;
    const maxPrice = Math.max(...prices) * 1.02;
    const priceRange = maxPrice - minPrice || 1;

    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const isPositive = endPrice >= startPrice;
    const lineColor = isPositive ? '#ffffff' : '#a3a3a3';
    const muted = 'rgba(255,255,255,0.12)';

    ctx.strokeStyle = muted;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (height - padding.top - padding.bottom) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const price = maxPrice - (priceRange * i) / 4;
      ctx.fillStyle = 'rgba(255,255,255,0.45)';
      ctx.font = '10px ui-sans-serif, system-ui, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`$${price.toFixed(0)}`, padding.left - 6, y + 3);
    }

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const xStep = chartWidth / (priceData.length - 1 || 1);

    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, isPositive ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');

    ctx.beginPath();
    ctx.moveTo(padding.left, height - padding.bottom);
    priceData.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight * (1 - (point.close - minPrice) / priceRange);
      ctx.lineTo(x, y);
    });
    ctx.lineTo(padding.left + (priceData.length - 1) * xStep, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1.5;
    priceData.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight * (1 - (point.close - minPrice) / priceRange);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.font = '10px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'center';
    const labelIndices = [0, Math.floor(priceData.length / 2), priceData.length - 1];
    labelIndices.forEach((i) => {
      if (priceData[i]) {
        const x = padding.left + i * xStep;
        const date = new Date(priceData[i].date);
        ctx.fillText(
          date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
          x,
          height - 8
        );
      }
    });
  };

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(0)}`;
  };

  const closeStream = () => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    closeStream();
    setIsLoading(true);
    setError('');
    setReportPath('');
    setReportId(null);
    setStreamMessage('');
    setVersions([]);
    setSelectedVersionId(null);
    setViewAnalysis({});
    setCompanyInfo(null);
    setPriceData([]);

    const streamUrl = `${API_BASE}/research/stream/${encodeURIComponent(query)}`;
    const es = new EventSource(streamUrl);
    esRef.current = es;

    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data) as StreamPayload;
        setStreamMessage(data.message || '');
        if (data.step === 'resolved' && data.ticker && data.company_name) {
          setCompanyInfo({
            name: data.company_name,
            ticker: data.ticker,
            sector: '',
            industry: '',
            market_cap: 0,
          });
        }
        if (data.step === 'complete') {
          if (data.report_path) setReportPath(data.report_path);
          if (data.report_id) setReportId(data.report_id);
          if (data.ticker && data.company_name) {
            const ci = data.company_info as Record<string, unknown> | undefined;
            setCompanyInfo({
              name: data.company_name,
              ticker: data.ticker,
              sector: (ci?.sector as string) || '',
              industry: (ci?.industry as string) || '',
              market_cap: Number(ci?.market_cap) || 0,
            });
            const prices = data.price_data?.prices;
            if (prices?.length) setPriceData(prices);
          }
          if (data.ticker) {
            void loadVersions(data.ticker, data.report_id || null);
            if (data.report_id) void loadReportDetail(data.report_id);
          }
          closeStream();
          setIsLoading(false);
        }
        if (data.step === 'error') {
          setError(data.message || 'Research failed');
          closeStream();
          setIsLoading(false);
        }
      } catch {
        /* ignore parse */
      }
    };

    es.onerror = () => {
      setError('Connection lost. Try again.');
      closeStream();
      setIsLoading(false);
    };
  };

  const handleFeedback = async () => {
    const id = selectedVersionId || reportId;
    if (!id || !feedback.trim()) return;
    setFeedbackBusy(true);
    setError('');
    try {
      const res = await feedbackApi.submitFeedback(id, feedback);
      if (!res.success) throw new Error(res.message || 'Feedback failed');
      setFeedback('');
      const t = companyInfo?.ticker;
      if (t) {
        await loadVersions(t, res.new_report_id || null);
        if (res.new_report_id) {
          setReportPath(res.new_report_path || '');
          setReportId(res.new_report_id);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Feedback failed');
    } finally {
      setFeedbackBusy(false);
    }
  };

  const getLogoUrl = (ticker: string) => {
    const domains: Record<string, string> = {
      AAPL: 'apple.com',
      MSFT: 'microsoft.com',
      GOOGL: 'google.com',
      AMZN: 'amazon.com',
      META: 'meta.com',
      TSLA: 'tesla.com',
      NVDA: 'nvidia.com',
      TSM: 'tsmc.com',
    };
    const domain = domains[ticker] || `${ticker.toLowerCase()}.com`;
    return `https://logo.clearbit.com/${domain}`;
  };

  const sectionOrder: { key: string; label: string }[] = [
    { key: 'recommendation', label: 'Recommendation' },
    { key: 'company_overview', label: 'Company' },
    { key: 'financial_analysis', label: 'Financials' },
    { key: 'risk_assessment', label: 'Risks' },
    { key: 'news_analysis', label: 'News' },
    { key: 'user_topics', label: 'Topics' },
    { key: 'custom_section', label: 'Focus' },
    { key: 'portfolio_fit', label: 'Portfolio fit' },
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      <NavBar />

      <main className="max-w-3xl mx-auto px-6 py-16 md:py-24">
        <header className="mb-14">
          <p className="text-[10px] tracking-[0.35em] uppercase text-white/50 mb-4">Research</p>
          <h1 className="text-3xl md:text-4xl font-extralight tracking-[0.08em] uppercase">
            Market Scout
          </h1>
          <p className="mt-4 text-sm text-white/45 font-light max-w-md leading-relaxed">
            Plain-English company lookup, live progress, PDF export.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="mb-12">
          <div className="flex flex-col sm:flex-row gap-3 border border-white/15 rounded-sm p-1 bg-white/[0.02]">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ticker or company name"
              className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none font-light"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-6 py-3 text-xs font-medium uppercase tracking-widest bg-white text-black rounded-sm hover:bg-white/90 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Running' : 'Run'}
            </button>
          </div>
        </form>

        {error && (
          <div className="mb-8 text-sm text-white/70 border border-white/20 px-4 py-3 rounded-sm">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="mb-10 py-8 border-t border-b border-white/10">
            <p className="text-xs tracking-[0.2em] uppercase text-white/40 mb-2">Status</p>
            <p className="text-sm font-light text-white/80">{streamMessage || 'Starting…'}</p>
          </div>
        )}

        {companyInfo && (
          <div className="mb-12 border border-white/10 p-6 rounded-sm">
            <div className="flex items-start gap-5">
              <img
                src={getLogoUrl(companyInfo.ticker)}
                alt=""
                className="w-14 h-14 object-contain opacity-90"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-baseline gap-3">
                  <h2 className="text-lg font-light tracking-wide">{companyInfo.name}</h2>
                  <span className="text-[10px] tracking-widest uppercase text-white/50">
                    {companyInfo.ticker}
                  </span>
                </div>
                {(companyInfo.sector || companyInfo.industry) && (
                  <p className="text-xs text-white/40 mt-2 font-light">
                    {companyInfo.sector}
                    {companyInfo.industry ? ` · ${companyInfo.industry}` : ''}
                  </p>
                )}
                {companyInfo.market_cap > 0 && (
                  <p className="text-xs text-white/35 mt-1">
                    Mkt cap {formatMarketCap(companyInfo.market_cap)}
                  </p>
                )}
              </div>
            </div>

            {priceData.length > 0 && (
              <div className="mt-8 pt-8 border-t border-white/10">
                <p className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-4">
                  1Y price
                </p>
                <canvas ref={canvasRef} className="w-full" style={{ height: 160 }} />
              </div>
            )}
          </div>
        )}

        {versions.length > 0 && (
          <div className="mb-10">
            <p className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-3">
              Versions
            </p>
            <div className="flex flex-wrap gap-2">
              {versions.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => setSelectedVersionId(v.id)}
                  className={`px-3 py-1.5 text-[10px] uppercase tracking-wider rounded-sm border transition-colors ${
                    selectedVersionId === v.id
                      ? 'bg-white text-black border-white'
                      : 'border-white/25 text-white/60 hover:border-white/50'
                  }`}
                >
                  v{v.version}
                </button>
              ))}
            </div>
          </div>
        )}

        {Object.keys(viewAnalysis).length > 0 && (
          <div className="space-y-10 mb-12">
            {sectionOrder.map(({ key, label }) => {
              const text = viewAnalysis[key];
              if (!text?.trim()) return null;
              return (
                <section key={key}>
                  <h3 className="text-[10px] uppercase tracking-[0.3em] text-white/35 mb-3">
                    {label}
                  </h3>
                  <div className="text-sm text-white/70 font-light leading-relaxed whitespace-pre-wrap">
                    {text}
                  </div>
                </section>
              );
            })}
          </div>
        )}

        {reportPath && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border border-white/15 p-5 rounded-sm mb-12">
            <p className="text-xs text-white/50 font-light">PDF ready</p>
            <a
              href={`${BACKEND_BASE}${reportPath}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-black bg-white px-5 py-3 rounded-sm hover:bg-white/90"
            >
              Download
              <span aria-hidden>↗</span>
            </a>
          </div>
        )}

        {(selectedVersionId || reportId) && (
          <div className="border border-white/10 p-5 rounded-sm">
            <p className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-3">
              Regenerate
            </p>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="What should change in the next version?"
              rows={3}
              className="w-full bg-white/[0.03] border border-white/10 px-3 py-2 text-sm text-white placeholder:text-white/25 outline-none font-light mb-3"
            />
            <button
              type="button"
              onClick={() => void handleFeedback()}
              disabled={feedbackBusy || !feedback.trim()}
              className="text-xs uppercase tracking-widest px-4 py-2 border border-white/30 rounded-sm hover:bg-white/5 disabled:opacity-30"
            >
              {feedbackBusy ? 'Working…' : 'Submit feedback'}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black text-white flex items-center justify-center text-sm font-light">
          Loading…
        </div>
      }
    >
      <ResearchPageInner />
    </Suspense>
  );
}
