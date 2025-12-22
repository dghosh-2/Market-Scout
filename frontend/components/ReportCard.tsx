'use client'

import { useState } from 'react'
import { formatDateTime } from '../lib/helpers'
import FeedbackForm from './FeedbackForm'

interface Report {
  id: number
  company: string
  report_path: string
  created_at: string
  version: number
}

interface ReportCardProps {
  report: Report
  onFeedbackSuccess: () => void
}

export default function ReportCard({ report, onFeedbackSuccess }: ReportCardProps) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const response = await fetch(`/api/papers/download/${report.id}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${report.id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm text-gray-500">{formatDateTime(report.created_at)}</p>
          <p className="font-medium text-gray-900">Version {report.version}</p>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleDownload}
          disabled={isDownloading}
          className="flex-1 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 disabled:bg-gray-300 transition-colors"
        >
          {isDownloading ? 'Downloading...' : 'Download'}
        </button>
        <button
          onClick={() => setShowFeedback(!showFeedback)}
          className="flex-1 py-2 bg-gray-100 text-gray-900 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
        >
          Feedback
        </button>
      </div>

      {showFeedback && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <FeedbackForm
            reportId={report.id}
            onSuccess={() => {
              setShowFeedback(false)
              onFeedbackSuccess()
            }}
          />
        </div>
      )}
    </div>
  )
}
