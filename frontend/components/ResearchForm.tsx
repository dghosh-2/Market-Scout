'use client'

import { useState } from 'react'

interface ResearchFormProps {
  onSubmit: (query: string) => void
  isLoading: boolean
}

export default function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSubmit(query.trim())
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
        Stock Ticker and Request
      </label>
      <textarea
        id="query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="AAPL - comprehensive analysis focusing on growth potential"
        rows={3}
        className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        disabled={isLoading}
        required
      />
      <p className="mt-2 text-xs text-gray-400 mb-4">
        Enter ticker (TSLA, MSFT) and optionally describe what you want to know
      </p>
      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        className="w-full py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Generating...' : 'Generate Report'}
      </button>
    </form>
  )
}
