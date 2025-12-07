'use client';

import Link from 'next/link';
import NavBar from '@/components/NavBar';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-semibold text-gray-900 mb-6">
            AI-Powered Stock Research
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            Generate comprehensive research reports on any publicly traded company. 
            Get financial analysis, risk assessment, and market insights in seconds.
          </p>
          <Link
            href="/research"
            className="inline-block px-8 py-4 bg-gray-900 text-white rounded-lg text-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Start Research
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          {[
            {
              title: 'Smart Resolution',
              desc: 'Enter company names in plain English. Our AI resolves "that electric car company" to TSLA automatically.'
            },
            {
              title: 'Comprehensive Analysis',
              desc: 'Financial metrics, risk factors, news sentiment, and actionable recommendations in one report.'
            },
            {
              title: 'Custom Focus',
              desc: 'Add specific requests like "focus on dividends" or "analyze growth potential" for tailored insights.'
            },
          ].map((feature) => (
            <div key={feature.title} className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.desc}</p>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Enter Query', desc: 'Type a company name, ticker, or description' },
              { step: '2', title: 'AI Analysis', desc: 'Our agents gather and analyze data' },
              { step: '3', title: 'Review Data', desc: 'See charts and key metrics in real-time' },
              { step: '4', title: 'Download', desc: 'Get your professional PDF report' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-10 h-10 bg-gray-900 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-lg font-medium">
                  {item.step}
                </div>
                <h4 className="font-medium text-gray-900 mb-1">{item.title}</h4>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-gray-500">
          For informational purposes only. Not investment advice.
        </div>
      </footer>
    </div>
  );
}
