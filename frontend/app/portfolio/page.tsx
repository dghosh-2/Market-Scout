'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import NavBar from '../../components/NavBar';
import { getApiBase } from '../../lib/env';

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

  const [queueBusy, setQueueBusy] = useState(false);
  const [queueStatus, setQueueStatus] = useState('');

  const API_BASE = getApiBase();

  useEffect(() => {
    void fetchPortfolio();
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
          company_name: newCompanyName || newTicker.toUpperCase(),
        }),
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
        body: JSON.stringify({ shares: parseFloat(editShares) }),
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
        method: 'DELETE',
      });

      if (!res.ok) throw new Error('Failed to delete holding');

      await fetchPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete holding');
    }
  };

  const researchAll = async () => {
    if (!holdings.length || queueBusy) return;
    setQueueBusy(true);
    setError('');
    const delayMs = 13000;
    try {
      for (let i = 0; i < holdings.length; i++) {
        const h = holdings[i];
        setQueueStatus(`Research ${h.ticker} (${i + 1}/${holdings.length})…`);
        const res = await fetch(`${API_BASE}/research`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: h.ticker }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.detail || data.message || `Failed on ${h.ticker}`);
        }
        if (i < holdings.length - 1) {
          await new Promise((r) => setTimeout(r, delayMs));
        }
      }
      setQueueStatus('Done.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Queue stopped');
      setQueueStatus('');
    } finally {
      setQueueBusy(false);
    }
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);

  const formatNumber = (value: number) =>
    new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value);

  return (
    <div className="min-h-screen bg-black text-white">
      <NavBar />

      <main className="max-w-5xl mx-auto px-6 py-14">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 mb-12">
          <div>
            <p className="text-[10px] tracking-[0.35em] uppercase text-white/45 mb-3">Holdings</p>
            <h1 className="text-2xl md:text-3xl font-extralight tracking-[0.12em] uppercase">Portfolio</h1>
            <p className="mt-3 text-sm text-white/40 font-light max-w-md">
              Weights feed into research reports as portfolio fit.
            </p>
          </div>
          {holdings.length > 0 && (
            <button
              type="button"
              onClick={() => void researchAll()}
              disabled={queueBusy}
              className="text-[10px] uppercase tracking-[0.2em] px-5 py-3 border border-white/25 rounded-sm hover:bg-white/5 disabled:opacity-30 shrink-0"
            >
              {queueBusy ? 'Running…' : 'Research all'}
            </button>
          )}
        </div>

        {queueStatus && (
          <p className="text-xs text-white/50 font-light mb-6 border border-white/10 px-4 py-3 rounded-sm">
            {queueStatus}
          </p>
        )}

        {error && (
          <div className="mb-6 text-sm text-white/70 border border-white/20 px-4 py-3 rounded-sm">{error}</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {[
            { label: 'Total value', value: isLoading ? '—' : formatCurrency(totalValue) },
            { label: 'Positions', value: isLoading ? '—' : String(holdings.length) },
            {
              label: 'Sectors',
              value: isLoading
                ? '—'
                : String(new Set(holdings.map((h) => h.sector || 'Unknown')).size),
            },
          ].map((s) => (
            <div key={s.label} className="border border-white/10 px-5 py-4 rounded-sm">
              <p className="text-[10px] uppercase tracking-[0.2em] text-white/35 mb-2">{s.label}</p>
              <p className="text-lg font-light">{s.value}</p>
            </div>
          ))}
        </div>

        <div className="border border-white/10 p-5 rounded-sm mb-10">
          <p className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-4">Add</p>
          <form onSubmit={handleAdd} className="flex flex-col md:flex-row flex-wrap gap-3">
            <input
              type="text"
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              placeholder="Ticker"
              className="flex-1 min-w-[100px] bg-white/[0.03] border border-white/10 px-3 py-2 text-sm outline-none font-light placeholder:text-white/25"
            />
            <input
              type="text"
              value={newCompanyName}
              onChange={(e) => setNewCompanyName(e.target.value)}
              placeholder="Name (optional)"
              className="flex-1 min-w-[140px] bg-white/[0.03] border border-white/10 px-3 py-2 text-sm outline-none font-light placeholder:text-white/25"
            />
            <input
              type="number"
              value={newShares}
              onChange={(e) => setNewShares(e.target.value)}
              placeholder="Shares"
              step="0.01"
              min="0"
              className="w-full md:w-28 bg-white/[0.03] border border-white/10 px-3 py-2 text-sm outline-none font-light placeholder:text-white/25"
            />
            <button
              type="submit"
              disabled={isAdding || !newTicker.trim() || !newShares}
              className="px-5 py-2 text-[10px] uppercase tracking-widest bg-white text-black rounded-sm hover:bg-white/90 disabled:opacity-30"
            >
              {isAdding ? '…' : 'Add'}
            </button>
          </form>
        </div>

        {isLoading ? (
          <p className="text-white/40 text-sm font-light py-12 text-center">Loading…</p>
        ) : holdings.length === 0 ? (
          <p className="text-white/40 text-sm font-light py-12 text-center border border-white/10 rounded-sm">
            No positions yet.
          </p>
        ) : (
          <div className="overflow-x-auto border border-white/10 rounded-sm">
            <table className="w-full text-sm font-light">
              <thead>
                <tr className="border-b border-white/10 text-[10px] uppercase tracking-[0.15em] text-white/40">
                  <th className="text-left px-4 py-3 font-normal">Ticker</th>
                  <th className="text-left px-4 py-3 font-normal">Name</th>
                  <th className="text-right px-4 py-3 font-normal">Shares</th>
                  <th className="text-right px-4 py-3 font-normal">Price</th>
                  <th className="text-right px-4 py-3 font-normal">Value</th>
                  <th className="text-right px-4 py-3 font-normal">Wt</th>
                  <th className="text-right px-4 py-3 font-normal"> </th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => (
                  <tr key={holding.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="px-4 py-3">
                      <span className="text-[11px] tracking-wider">{holding.ticker}</span>
                    </td>
                    <td className="px-4 py-3 text-white/60">{holding.company_name}</td>
                    <td className="px-4 py-3 text-right">
                      {editingTicker === holding.ticker ? (
                        <input
                          type="number"
                          value={editShares}
                          onChange={(e) => setEditShares(e.target.value)}
                          className="w-20 bg-white/[0.05] border border-white/15 px-2 py-1 text-right outline-none"
                          step="0.01"
                          autoFocus
                        />
                      ) : (
                        formatNumber(holding.shares)
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-white/50">
                      {holding.current_price != null ? formatCurrency(holding.current_price) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {holding.value != null ? formatCurrency(holding.value) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-white/50">
                      {holding.weight != null ? `${holding.weight.toFixed(1)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <Link
                        href={`/research?ticker=${encodeURIComponent(holding.ticker)}`}
                        className="text-[10px] uppercase tracking-wider text-white/50 hover:text-white mr-3"
                      >
                        Research
                      </Link>
                      {editingTicker === holding.ticker ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleUpdate(holding.ticker)}
                            className="text-[10px] uppercase text-white/70 mr-2"
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingTicker(null);
                              setEditShares('');
                            }}
                            className="text-[10px] uppercase text-white/35"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingTicker(holding.ticker);
                              setEditShares(holding.shares.toString());
                            }}
                            className="text-[10px] uppercase text-white/35 mr-2"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleDelete(holding.ticker)}
                            className="text-[10px] uppercase text-white/35"
                          >
                            Remove
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
