'use client';

import { useState, useEffect, useRef } from 'react';
import NavBar from '../../components/NavBar';

const API_BASE = 'http://localhost:8000/api';

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
  logo_url: string;
}

interface ProgressStep {
  id: string;
  label: string;
  completed: boolean;
}

const agentDescriptions: Record<string, string> = {
  parsing: 'Understanding your request...',
  resolving: 'Identifying the company...',
  fetching_company: 'Gathering company profile...',
  fetching_financials: 'Analyzing financial statements...',
  fetching_risks: 'Evaluating risk factors...',
  fetching_news: 'Scanning market news...',
  generating: 'AI agents synthesizing insights...',
  creating_pdf: 'Compiling your report...',
};

export default function ResearchPage() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [reportPath, setReportPath] = useState('');
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [priceData, setPriceData] = useState<PricePoint[]>([]);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const [currentStep, setCurrentStep] = useState('');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const steps = [
    { id: 'parsing', label: 'Parse' },
    { id: 'resolving', label: 'Resolve' },
    { id: 'fetching_company', label: 'Company' },
    { id: 'fetching_financials', label: 'Financials' },
    { id: 'fetching_risks', label: 'Risks' },
    { id: 'fetching_news', label: 'News' },
    { id: 'generating', label: 'Generate' },
    { id: 'creating_pdf', label: 'Export' },
  ];

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
    const padding = { top: 20, right: 20, bottom: 30, left: 50 };

    ctx.clearRect(0, 0, width, height);

    const prices = priceData.map(p => p.close);
    const minPrice = Math.min(...prices) * 0.98;
    const maxPrice = Math.max(...prices) * 1.02;
    const priceRange = maxPrice - minPrice;

    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const isPositive = endPrice >= startPrice;
    const lineColor = isPositive ? '#059669' : '#e11d48';
    const gradientStart = isPositive ? 'rgba(5, 150, 105, 0.15)' : 'rgba(225, 29, 72, 0.15)';
    const gradientEnd = isPositive ? 'rgba(5, 150, 105, 0)' : 'rgba(225, 29, 72, 0)';

    // Draw grid lines
    ctx.strokeStyle = '#f5f5f5';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (height - padding.top - padding.bottom) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const price = maxPrice - (priceRange * i / 4);
      ctx.fillStyle = '#a3a3a3';
      ctx.font = '11px DM Sans';
      ctx.textAlign = 'right';
      ctx.fillText(`$${price.toFixed(0)}`, padding.left - 8, y + 4);
    }

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const xStep = chartWidth / (priceData.length - 1);

    // Create gradient fill
    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, gradientStart);
    gradient.addColorStop(1, gradientEnd);

    // Draw filled area
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

    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    priceData.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight * (1 - (point.close - minPrice) / priceRange);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw date labels
    ctx.fillStyle = '#a3a3a3';
    ctx.font = '11px DM Sans';
    ctx.textAlign = 'center';
    const labelIndices = [0, Math.floor(priceData.length / 2), priceData.length - 1];
    labelIndices.forEach(i => {
      if (priceData[i]) {
        const x = padding.left + i * xStep;
        const date = new Date(priceData[i].date);
        ctx.fillText(date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }), x, height - 8);
      }
    });
  };

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(0)}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setReportPath('');
    setCompanyInfo(null);
    setPriceData([]);
    setProgressSteps(steps.map(s => ({ ...s, completed: false })));
    setCurrentStep('parsing');

    try {
      const updateProgress = (stepId: string) => {
        setCurrentStep(stepId);
        setProgressSteps(prev => prev.map(s => ({
          ...s,
          completed: steps.findIndex(st => st.id === s.id) < steps.findIndex(st => st.id === stepId)
        })));
      };

      updateProgress('parsing');
      await new Promise(r => setTimeout(r, 300));

      updateProgress('resolving');
      await new Promise(r => setTimeout(r, 300));

      updateProgress('fetching_company');
      
      try {
        const previewRes = await fetch(`${API_BASE}/research/preview/${encodeURIComponent(query)}`);
        if (previewRes.ok) {
          const preview = await previewRes.json();
          setCompanyInfo({
            name: preview.company_name,
            ticker: preview.ticker,
            sector: preview.company_info?.sector || '',
            industry: preview.company_info?.industry || '',
            market_cap: preview.company_info?.market_cap || 0,
            logo_url: `https://logo.clearbit.com/${preview.company_info?.website?.replace('https://', '').replace('http://', '').split('/')[0]}` || ''
          });
          if (preview.price_data?.prices) {
            setPriceData(preview.price_data.prices);
          }
        }
      } catch {
        // Continue without preview
      }

      updateProgress('fetching_financials');
      await new Promise(r => setTimeout(r, 500));

      updateProgress('fetching_risks');
      await new Promise(r => setTimeout(r, 400));

      updateProgress('fetching_news');
      await new Promise(r => setTimeout(r, 400));

      updateProgress('generating');
      
      const response = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      updateProgress('creating_pdf');
      await new Promise(r => setTimeout(r, 300));

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || data.detail || 'Research failed');
      }

      setReportPath(data.report_path);
      setProgressSteps(prev => prev.map(s => ({ ...s, completed: true })));

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const getLogoUrl = (ticker: string) => {
    const domains: Record<string, string> = {
      'AAPL': 'apple.com',
      'MSFT': 'microsoft.com',
      'GOOGL': 'google.com',
      'AMZN': 'amazon.com',
      'META': 'meta.com',
      'TSLA': 'tesla.com',
      'NVDA': 'nvidia.com',
      'TSM': 'tsmc.com',
      'JPM': 'jpmorganchase.com',
      'V': 'visa.com',
      'WMT': 'walmart.com',
      'DIS': 'disney.com',
      'NFLX': 'netflix.com',
    };
    const domain = domains[ticker] || `${ticker.toLowerCase()}.com`;
    return `https://logo.clearbit.com/${domain}`;
  };

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);
  const progress = isLoading ? ((currentStepIndex + 1) / steps.length) * 100 : 0;

  return (
    <div className="min-h-screen bg-neutral-50 gradient-mesh">
      <NavBar />
      
      <main className="max-w-5xl mx-auto px-6 py-12">
        <div className="mb-12 animate-fadeIn">
          <h1 className="text-4xl font-semibold text-neutral-900 mb-3 tracking-tight">
            Stock Research
          </h1>
          <p className="text-lg text-neutral-500">
            AI-powered analysis for smarter investment decisions
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mb-10 animate-fadeIn stagger-1">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search any company... Apple, TSLA, or 'that AI chip company'"
              className="w-full px-5 py-4 pr-32 bg-white border border-neutral-200 rounded-2xl 
                       text-neutral-900 placeholder-neutral-400 text-lg
                       focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500
                       shadow-soft transition-all duration-200"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2
                       px-6 py-2.5 bg-neutral-900 text-white rounded-xl font-medium
                       hover:bg-neutral-800 disabled:bg-neutral-300 disabled:cursor-not-allowed
                       transition-all duration-200 active:scale-[0.98]"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analyzing
                </span>
              ) : 'Research'}
            </button>
          </div>
          <p className="mt-3 text-sm text-neutral-400 pl-1">
            Add context like "focus on dividends" or "growth potential" for tailored insights
          </p>
        </form>

        {error && (
          <div className="mb-8 p-4 bg-rose-50 border border-rose-200 rounded-2xl animate-scaleIn">
            <p className="text-rose-700 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </p>
          </div>
        )}

        {isLoading && (
          <div className="mb-8 card p-8 animate-scaleIn">
            {/* AI Agent Animation */}
            <div className="flex flex-col items-center mb-8">
              <div className="relative w-24 h-24 mb-6">
                {/* Central orb */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 shadow-glow-blue animate-pulse" />
                </div>
                {/* Orbiting dots */}
                <div className="absolute inset-0 animate-orbit">
                  <div className="w-3 h-3 rounded-full bg-blue-500 shadow-glow-blue" />
                </div>
                <div className="absolute inset-0 animate-orbit-reverse">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-glow-emerald" />
                </div>
                {/* Pulse rings */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full border-2 border-blue-500/30 animate-ping" style={{ animationDuration: '2s' }} />
                </div>
              </div>
              
              <div className="text-center">
                <p className="text-lg font-medium text-neutral-900 mb-1">
                  {agentDescriptions[currentStep] || 'Processing...'}
                </p>
                <p className="text-sm text-neutral-400 font-mono">
                  {companyInfo?.ticker || query.toUpperCase().slice(0, 6)}
                </p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mb-6">
              <div className="h-1.5 bg-neutral-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transition-all duration-500 ease-out relative progress-wave"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Step indicators */}
            <div className="flex justify-between">
              {progressSteps.map((step, index) => {
                const isActive = currentStep === step.id;
                const isPast = step.completed;
                
                return (
                  <div key={step.id} className="flex flex-col items-center">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium
                      transition-all duration-300
                      ${isPast ? 'bg-emerald-500 text-white scale-100' : 
                        isActive ? 'bg-blue-500 text-white scale-110 shadow-glow-blue' : 
                        'bg-neutral-100 text-neutral-400'}
                    `}>
                      {isPast ? (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        index + 1
                      )}
                    </div>
                    <span className={`
                      mt-2 text-xs font-medium transition-colors
                      ${isActive ? 'text-blue-600' : isPast ? 'text-emerald-600' : 'text-neutral-400'}
                    `}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {companyInfo && (
          <div className="mb-8 card overflow-hidden animate-fadeIn">
            <div className="p-6 border-b border-neutral-100">
              <div className="flex items-center gap-5">
                <div className="relative">
                  <img
                    src={getLogoUrl(companyInfo.ticker)}
                    alt={companyInfo.name}
                    className="w-16 h-16 rounded-2xl object-contain bg-white border border-neutral-100 p-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-2xl font-semibold text-neutral-900">{companyInfo.name}</h2>
                    <span className="px-2.5 py-1 bg-neutral-100 text-neutral-600 text-sm font-mono rounded-lg">
                      {companyInfo.ticker}
                    </span>
                  </div>
                  <p className="text-neutral-500">
                    {companyInfo.sector} {companyInfo.industry && `· ${companyInfo.industry}`}
                  </p>
                  {companyInfo.market_cap > 0 && (
                    <p className="text-sm text-neutral-400 mt-1">
                      Market Cap: <span className="text-neutral-600 font-medium">{formatMarketCap(companyInfo.market_cap)}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>

            {priceData.length > 0 && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-neutral-500">1-Year Performance</h3>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-neutral-400">
                      ${priceData[0]?.close.toFixed(2)}
                    </span>
                    <span className={`font-medium ${
                      priceData[priceData.length - 1]?.close >= priceData[0]?.close 
                        ? 'text-emerald-600' 
                        : 'text-rose-600'
                    }`}>
                      {((priceData[priceData.length - 1]?.close - priceData[0]?.close) / priceData[0]?.close * 100).toFixed(2)}%
                    </span>
                    <span className="text-neutral-900 font-semibold">
                      ${priceData[priceData.length - 1]?.close.toFixed(2)}
                    </span>
                  </div>
                </div>
                <canvas
                  ref={canvasRef}
                  className="w-full"
                  style={{ height: '200px' }}
                />
              </div>
            )}
          </div>
        )}

        {reportPath && (
          <div className="card p-6 animate-scaleIn">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900">Report Ready</h3>
                  <p className="text-neutral-500">Your analysis is complete and ready to download</p>
                </div>
              </div>
              <a
                href={`http://localhost:8000${reportPath}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium 
                         hover:bg-blue-700 transition-all duration-200 active:scale-[0.98]
                         flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download PDF
              </a>
            </div>
          </div>
        )}

        {!isLoading && !reportPath && (
          <div className="mt-16 animate-fadeIn stagger-3">
            <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-4">Quick Start</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { query: 'Apple', desc: 'Comprehensive analysis', tag: 'Popular' },
                { query: 'TSLA - growth catalysts', desc: 'Focus on growth drivers', tag: 'Growth' },
                { query: 'Microsoft - dividend analysis', desc: 'Income-focused report', tag: 'Income' },
              ].map((example) => (
                <button
                  key={example.query}
                  onClick={() => setQuery(example.query)}
                  className="group text-left p-5 card card-hover"
                >
                  <div className="flex items-start justify-between mb-2">
                    <p className="font-medium text-neutral-900 group-hover:text-blue-600 transition-colors">
                      {example.query}
                    </p>
                    <span className="px-2 py-0.5 text-xs font-medium bg-neutral-100 text-neutral-500 rounded-md">
                      {example.tag}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-500">{example.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
