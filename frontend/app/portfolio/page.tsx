'use client';

import { useState, useEffect } from 'react';
import NavBar from '@/components/NavBar';

const API_BASE = 'http://localhost:8000/api';

interface Holding {
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

interface PortfolioSummary {
  holdings: Holding[];
  total_value: number;
  total_holdings: number;
}

const sectorColors: Record<string, string> = {
  'Technology': 'bg-blue-500',
  'Healthcare': 'bg-emerald-500',
  'Financial Services': 'bg-violet-500',
  'Consumer Cyclical': 'bg-amber-500',
  'Communication Services': 'bg-rose-500',
  'Consumer Defensive': 'bg-teal-500',
  'Energy': 'bg-orange-500',
  'Industrials': 'bg-slate-500',
  'Basic Materials': 'bg-lime-500',
  'Real Estate': 'bg-cyan-500',
  'Utilities': 'bg-indigo-500',
  'Unknown': 'bg-neutral-400',
};

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [newTicker, setNewTicker] = useState('');
  const [newShares, setNewShares] = useState('');
  const [newCompanyName, setNewCompanyName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  
  const [editingTicker, setEditingTicker] = useState<string | null>(null);
  const [editShares, setEditShares] = useState('');

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/portfolio/summary`);
      if (!res.ok) throw new Error('Failed to fetch portfolio');
      const data: PortfolioSummary = await res.json();
      setHoldings(data.holdings);
      setTotalValue(data.total_value);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim() || !newShares) return;
    
    setIsAdding(true);
    setError('');
    
    try {
      const res = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: newTicker.toUpperCase(),
          shares: parseFloat(newShares),
          company_name: newCompanyName || newTicker.toUpperCase()
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to add holding');
      }
      
      setNewTicker('');
      setNewShares('');
      setNewCompanyName('');
      await fetchPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add holding');
    } finally {
      setIsAdding(false);
    }
  };

  const handleUpdate = async (ticker: string) => {
    if (!editShares) return;
    
    try {
      const res = await fetch(`${API_BASE}/portfolio/${ticker}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shares: parseFloat(editShares) })
      });
      
      if (!res.ok) throw new Error('Failed to update holding');
      
      setEditingTicker(null);
      setEditShares('');
      await fetchPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update holding');
    }
  };

  const handleDelete = async (ticker: string) => {
    try {
      const res = await fetch(`${API_BASE}/portfolio/${ticker}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete holding');
      
      await fetchPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete holding');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(value);
  };

  const getSectorBreakdown = () => {
    const sectors: Record<string, number> = {};
    holdings.forEach(h => {
      const sector = h.sector || 'Unknown';
      sectors[sector] = (sectors[sector] || 0) + (h.value || 0);
    });
    return Object.entries(sectors)
      .map(([name, value]) => ({
        name,
        value,
        percent: totalValue > 0 ? (value / totalValue * 100) : 0,
        color: sectorColors[name] || 'bg-neutral-400'
      }))
      .sort((a, b) => b.value - a.value);
  };

  return (
    <div className="min-h-screen bg-neutral-50 gradient-mesh">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10 animate-fadeIn">
          <h1 className="text-4xl font-semibold text-neutral-900 mb-3 tracking-tight">Portfolio</h1>
          <p className="text-lg text-neutral-500">Track holdings and get personalized fit analysis in reports</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl animate-scaleIn">
            <p className="text-rose-700 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 animate-fadeIn stagger-1">
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm text-neutral-500">Total Value</p>
            </div>
            <p className="text-3xl font-semibold text-neutral-900">
              {isLoading ? (
                <span className="inline-block w-32 h-8 bg-neutral-100 rounded-lg animate-pulse" />
              ) : formatCurrency(totalValue)}
            </p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <p className="text-sm text-neutral-500">Holdings</p>
            </div>
            <p className="text-3xl font-semibold text-neutral-900">
              {isLoading ? (
                <span className="inline-block w-16 h-8 bg-neutral-100 rounded-lg animate-pulse" />
              ) : holdings.length}
            </p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                </svg>
              </div>
              <p className="text-sm text-neutral-500">Sectors</p>
            </div>
            <p className="text-3xl font-semibold text-neutral-900">
              {isLoading ? (
                <span className="inline-block w-16 h-8 bg-neutral-100 rounded-lg animate-pulse" />
              ) : getSectorBreakdown().length}
            </p>
          </div>
        </div>

        <div className="card p-6 mb-8 animate-fadeIn stagger-2">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Add Holding</h2>
          <form onSubmit={handleAdd} className="flex flex-wrap gap-4">
            <input
              type="text"
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              placeholder="Ticker (e.g., AAPL)"
              className="flex-1 min-w-[120px] input-modern"
            />
            <input
              type="text"
              value={newCompanyName}
              onChange={(e) => setNewCompanyName(e.target.value)}
              placeholder="Company name (optional)"
              className="flex-1 min-w-[180px] input-modern"
            />
            <input
              type="number"
              value={newShares}
              onChange={(e) => setNewShares(e.target.value)}
              placeholder="Shares"
              step="0.01"
              min="0"
              className="w-32 input-modern"
            />
            <button
              type="submit"
              disabled={isAdding || !newTicker.trim() || !newShares}
              className="btn-primary"
            >
              {isAdding ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Adding
                </span>
              ) : 'Add'}
            </button>
          </form>
        </div>

        {isLoading ? (
          <div className="card p-12 text-center animate-fadeIn">
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mb-4 animate-pulse">
                <svg className="w-6 h-6 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <p className="text-neutral-500">Loading portfolio...</p>
            </div>
          </div>
        ) : holdings.length === 0 ? (
          <div className="card p-12 text-center animate-fadeIn">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-2xl bg-neutral-100 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <p className="text-neutral-900 font-medium mb-1">No holdings yet</p>
              <p className="text-sm text-neutral-500">Add your first holding above to get started</p>
            </div>
          </div>
        ) : (
          <>
            <div className="card overflow-hidden mb-8 animate-fadeIn stagger-3">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-100 bg-neutral-50/50">
                      <th className="text-left px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Ticker</th>
                      <th className="text-left px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Company</th>
                      <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Shares</th>
                      <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Price</th>
                      <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Value</th>
                      <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Weight</th>
                      <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map((holding, i) => (
                      <tr 
                        key={holding.id} 
                        className="border-b border-neutral-50 hover:bg-neutral-50/50 transition-colors"
                        style={{ animationDelay: `${i * 50}ms` }}
                      >
                        <td className="px-6 py-4">
                          <span className="font-mono font-medium text-neutral-900 bg-neutral-100 px-2 py-1 rounded-md">
                            {holding.ticker}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-neutral-600">{holding.company_name}</td>
                        <td className="px-6 py-4 text-right">
                          {editingTicker === holding.ticker ? (
                            <input
                              type="number"
                              value={editShares}
                              onChange={(e) => setEditShares(e.target.value)}
                              className="w-24 px-3 py-1.5 border border-neutral-200 rounded-lg text-right focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                              step="0.01"
                              autoFocus
                            />
                          ) : (
                            <span className="text-neutral-900">{formatNumber(holding.shares)}</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right text-neutral-500">
                          {holding.current_price ? formatCurrency(holding.current_price) : '-'}
                        </td>
                        <td className="px-6 py-4 text-right font-medium text-neutral-900">
                          {holding.value ? formatCurrency(holding.value) : '-'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          {holding.weight ? (
                            <span className="text-neutral-600">{holding.weight.toFixed(1)}%</span>
                          ) : '-'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          {editingTicker === holding.ticker ? (
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => handleUpdate(holding.ticker)}
                                className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => {
                                  setEditingTicker(null);
                                  setEditShares('');
                                }}
                                className="px-3 py-1.5 text-sm font-medium text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 rounded-lg transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div className="flex justify-end gap-1">
                              <button
                                onClick={() => {
                                  setEditingTicker(holding.ticker);
                                  setEditShares(holding.shares.toString());
                                }}
                                className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleDelete(holding.ticker)}
                                className="p-2 text-neutral-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {getSectorBreakdown().length > 0 && (
              <div className="card p-6 animate-fadeIn stagger-4">
                <h2 className="text-lg font-semibold text-neutral-900 mb-6">Sector Allocation</h2>
                
                {/* Visual bar breakdown */}
                <div className="h-4 rounded-full overflow-hidden flex mb-6">
                  {getSectorBreakdown().map((sector) => (
                    <div
                      key={sector.name}
                      className={`${sector.color} first:rounded-l-full last:rounded-r-full transition-all duration-500`}
                      style={{ width: `${sector.percent}%` }}
                      title={`${sector.name}: ${sector.percent.toFixed(1)}%`}
                    />
                  ))}
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {getSectorBreakdown().map((sector) => (
                    <div key={sector.name} className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${sector.color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900 truncate">{sector.name}</p>
                        <p className="text-xs text-neutral-500">{sector.percent.toFixed(1)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
