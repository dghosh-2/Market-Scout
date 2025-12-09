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
        percent: totalValue > 0 ? (value / totalValue * 100) : 0
      }))
      .sort((a, b) => b.value - a.value);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Portfolio</h1>
          <p className="text-gray-600">Track your holdings and see how new investments would fit</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="text-sm text-gray-500 mb-1">Total Value</p>
            <p className="text-3xl font-semibold text-gray-900">
              {isLoading ? '...' : formatCurrency(totalValue)}
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="text-sm text-gray-500 mb-1">Holdings</p>
            <p className="text-3xl font-semibold text-gray-900">
              {isLoading ? '...' : holdings.length}
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="text-sm text-gray-500 mb-1">Sectors</p>
            <p className="text-3xl font-semibold text-gray-900">
              {isLoading ? '...' : getSectorBreakdown().length}
            </p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Holding</h2>
          <form onSubmit={handleAdd} className="flex flex-wrap gap-4">
            <input
              type="text"
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              placeholder="Ticker (e.g., AAPL)"
              className="flex-1 min-w-[120px] px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
            />
            <input
              type="text"
              value={newCompanyName}
              onChange={(e) => setNewCompanyName(e.target.value)}
              placeholder="Company name (optional)"
              className="flex-1 min-w-[180px] px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
            />
            <input
              type="number"
              value={newShares}
              onChange={(e) => setNewShares(e.target.value)}
              placeholder="Shares"
              step="0.01"
              min="0"
              className="w-32 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
            />
            <button
              type="submit"
              disabled={isAdding || !newTicker.trim() || !newShares}
              className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isAdding ? 'Adding...' : 'Add'}
            </button>
          </form>
        </div>

        {isLoading ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500">Loading portfolio...</p>
          </div>
        ) : holdings.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500 mb-2">No holdings yet</p>
            <p className="text-sm text-gray-400">Add your first holding above to get started</p>
          </div>
        ) : (
          <>
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden mb-8">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Ticker</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Company</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Shares</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Price</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Weight</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => (
                    <tr key={holding.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">{holding.ticker}</td>
                      <td className="px-6 py-4 text-gray-600">{holding.company_name}</td>
                      <td className="px-6 py-4 text-right">
                        {editingTicker === holding.ticker ? (
                          <input
                            type="number"
                            value={editShares}
                            onChange={(e) => setEditShares(e.target.value)}
                            className="w-24 px-2 py-1 border border-gray-200 rounded text-right"
                            step="0.01"
                            autoFocus
                          />
                        ) : (
                          formatNumber(holding.shares)
                        )}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {holding.current_price ? formatCurrency(holding.current_price) : '-'}
                      </td>
                      <td className="px-6 py-4 text-right font-medium text-gray-900">
                        {holding.value ? formatCurrency(holding.value) : '-'}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {holding.weight ? `${holding.weight.toFixed(1)}%` : '-'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {editingTicker === holding.ticker ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleUpdate(holding.ticker)}
                              className="text-sm text-blue-600 hover:text-blue-800"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => {
                                setEditingTicker(null);
                                setEditShares('');
                              }}
                              className="text-sm text-gray-500 hover:text-gray-700"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="flex justify-end gap-3">
                            <button
                              onClick={() => {
                                setEditingTicker(holding.ticker);
                                setEditShares(holding.shares.toString());
                              }}
                              className="text-sm text-gray-500 hover:text-gray-700"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(holding.ticker)}
                              className="text-sm text-red-500 hover:text-red-700"
                            >
                              Remove
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {getSectorBreakdown().length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Sector Breakdown</h2>
                <div className="space-y-3">
                  {getSectorBreakdown().map((sector) => (
                    <div key={sector.name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700">{sector.name}</span>
                        <span className="text-gray-500">{sector.percent.toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${sector.percent}%` }}
                        />
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

