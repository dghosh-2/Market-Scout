'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { feedbackApi } from '@/lib/api'

interface FeedbackFormProps {
  reportId: number
  onSuccess: (data: any) => void
}

export default function FeedbackForm({ reportId, onSuccess }: FeedbackFormProps) {
  const [feedback, setFeedback] = useState('')
  const [error, setError] = useState<string | null>(null)

  const feedbackMutation = useMutation({
    mutationFn: (feedback: string) => feedbackApi.submitFeedback(reportId, feedback),
    onSuccess: (data) => {
      if (data.success) {
        setFeedback('')
        setError(null)
        onSuccess(data)
      } else {
        setError(data.message)
      }
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to process feedback')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (feedback.trim()) {
      setError(null)
      feedbackMutation.mutate(feedback.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="More detail on competitive landscape and recent partnerships"
        rows={2}
        className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none mb-3"
        disabled={feedbackMutation.isPending}
        required
      />
      <button
        type="submit"
        disabled={feedbackMutation.isPending || !feedback.trim()}
        className="w-full py-2.5 bg-gray-100 text-gray-900 text-sm font-medium rounded-lg hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {feedbackMutation.isPending ? 'Regenerating...' : 'Submit Feedback'}
      </button>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </form>
  )
}
