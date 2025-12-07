'use client';

import { useState, useEffect, useRef } from 'react';
import NavBar from '@/components/NavBar';

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
  step: string;
  message: string;
  completed: boolean;
}

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
    { id: 'parsing', label: 'Parsing request' },
    { id: 'resolving', label: 'Finding company' },
    { id: 'fetching_company', label: 'Loading company data' },
    { id: 'fetching_financials', label: 'Analyzing financials' },
    { id: 'fetching_risks', label: 'Assessing risks' },
    { id: 'fetching_news', label: 'Gathering news' },
    { id: 'generating', label: 'Generating analysis' },
    { id: 'creating_pdf', label: 'Creating report' },
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

    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;

    ctx.clearRect(0, 0, width, height);

    const prices = priceData.map(p => p.close);
    const minPrice = Math.min(...prices) * 0.98;
    const maxPrice = Math.max(...prices) * 1.02;
    const priceRange = maxPrice - minPrice;

    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const isPositive = endPrice >= startPrice;
    const lineColor = isPositive ? '#16a34a' : '#dc2626';
    const fillColor = isPositive ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)';

    // Draw grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding + (height - 2 * padding) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();

      const price = maxPrice - (priceRange * i / 4);
      ctx.fillStyle = '#6b7280';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`$${price.toFixed(0)}`, padding - 5, y + 3);
    }

    // Draw price line
    ctx.beginPath();
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;

    const xStep = (width - 2 * padding) / (priceData.length - 1);

    priceData.forEach((point, i) => {
      const x = padding + i * xStep;
      const y = padding + (height - 2 * padding) * (1 - (point.close - minPrice) / priceRange);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Fill area under line
    ctx.lineTo(padding + (priceData.length - 1) * xStep, height - padding);
    ctx.lineTo(padding, height - padding);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();

    // Draw date labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'center';
    const labelIndices = [0, Math.floor(priceData.length / 2), priceData.length - 1];
    labelIndices.forEach(i => {
      if (priceData[i]) {
        const x = padding + i * xStep;
        const date = new Date(priceData[i].date);
        ctx.fillText(date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }), x, height - 10);
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
      // Simulate progress steps
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
      
      // Get preview data first
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
      
      // Make actual research request
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

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Stock Research</h1>
          <p className="text-gray-600">Enter a company name or ticker to generate a comprehensive research report</p>
        </div>

        <form onSubmit={handleSubmit} className="mb-10">
          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Apple, TSLA, Microsoft - focus on growth potential"
              className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900 placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-8 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Analyzing...' : 'Research'}
            </button>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Tip: Add specific requests like "focus on dividends" or "analyze growth potential"
          </p>
        </form>

        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="mb-8 bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Research Progress</h3>
            <div className="space-y-3">
              {progressSteps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    step.completed ? 'bg-green-500 text-white' :
                    currentStep === step.id ? 'bg-blue-500 text-white animate-pulse' :
                    'bg-gray-200 text-gray-500'
                  }`}>
                    {step.completed ? '✓' : index + 1}
                  </div>
                  <span className={`text-sm ${
                    step.completed ? 'text-green-700' :
                    currentStep === step.id ? 'text-blue-700 font-medium' :
                    'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                  {currentStep === step.id && (
                    <div className="ml-2 flex gap-1">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {companyInfo && (
          <div className="mb-8 bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center gap-4">
                <img
                  src={getLogoUrl(companyInfo.ticker)}
                  alt={companyInfo.name}
                  className="w-16 h-16 rounded-lg object-contain bg-white border border-gray-100"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900">{companyInfo.name}</h2>
                  <p className="text-gray-500">{companyInfo.ticker} · {companyInfo.sector} · {companyInfo.industry}</p>
                  {companyInfo.market_cap > 0 && (
                    <p className="text-sm text-gray-600 mt-1">Market Cap: {formatMarketCap(companyInfo.market_cap)}</p>
                  )}
                </div>
              </div>
            </div>

            {priceData.length > 0 && (
              <div className="p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">1-Year Price History</h3>
                <canvas
                  ref={canvasRef}
                  width={800}
                  height={300}
                  className="w-full"
                  style={{ maxHeight: '300px' }}
                />
                <div className="mt-3 flex justify-between text-sm text-gray-600">
                  <span>Start: ${priceData[0]?.close.toFixed(2)}</span>
                  <span className={priceData[priceData.length - 1]?.close >= priceData[0]?.close ? 'text-green-600' : 'text-red-600'}>
                    {((priceData[priceData.length - 1]?.close - priceData[0]?.close) / priceData[0]?.close * 100).toFixed(2)}%
                  </span>
                  <span>Current: ${priceData[priceData.length - 1]?.close.toFixed(2)}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {reportPath && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Report Ready</h3>
                <p className="text-gray-600 mt-1">Your research report has been generated successfully.</p>
              </div>
              <a
                href={`http://localhost:8000${reportPath}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Download PDF
              </a>
            </div>
          </div>
        )}

        <div className="mt-12 border-t border-gray-200 pt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Examples</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { query: 'Apple', desc: 'Standard comprehensive report' },
              { query: 'TSLA - focus on growth catalysts', desc: 'With specific focus area' },
              { query: 'Microsoft - dividend analysis', desc: 'Income-focused analysis' },
            ].map((example) => (
              <button
                key={example.query}
                onClick={() => setQuery(example.query)}
                className="text-left p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors"
              >
                <p className="font-medium text-gray-900">{example.query}</p>
                <p className="text-sm text-gray-500 mt-1">{example.desc}</p>
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
