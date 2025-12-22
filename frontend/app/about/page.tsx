'use client';

import NavBar from '../../components/NavBar';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      
      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-semibold text-gray-900 mb-8">About StockResearch</h1>
        
        <div className="space-y-8">
          <section className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">How It Works</h2>
            <p className="text-gray-600 leading-relaxed">
              StockResearch uses AI-powered agents to gather and analyze data from multiple sources. 
              When you enter a query, our system identifies the company, fetches real-time financial 
              data, analyzes risks, gathers news, and generates a comprehensive research report.
            </p>
          </section>

          <section className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Sources</h2>
            <ul className="space-y-3 text-gray-600">
              <li><strong>Financial Data:</strong> Real-time market data, income statements, balance sheets, and cash flow analysis</li>
              <li><strong>Risk Analysis:</strong> Beta, volatility, debt ratios, and governance metrics</li>
              <li><strong>News:</strong> Recent headlines and sentiment analysis</li>
              <li><strong>AI Analysis:</strong> GPT-4o-mini for intelligent analysis and recommendations</li>
            </ul>
          </section>

          <section className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { title: 'Smart Ticker Resolution', desc: 'Enter company names in plain English' },
                { title: 'Real-Time Progress', desc: 'Watch as data is gathered and analyzed' },
                { title: 'Price Charts', desc: 'Visual 1-year price history' },
                { title: 'PDF Reports', desc: 'Professional downloadable documents' },
                { title: 'Report History', desc: 'Access all your past research' },
                { title: 'Feedback Loop', desc: 'Request updated reports with specific focus' },
              ].map((feature) => (
                <div key={feature.title} className="border border-gray-100 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Query Examples</h2>
            <div className="space-y-3">
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm text-gray-800">Apple</code>
                <p className="text-sm text-gray-500 mt-1">Standard comprehensive report</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm text-gray-800">TSLA - focus on growth catalysts</code>
                <p className="text-sm text-gray-500 mt-1">Report with specific focus area</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm text-gray-800">that semiconductor company in Taiwan</code>
                <p className="text-sm text-gray-500 mt-1">AI resolves to TSM (TSMC)</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm text-gray-800">Microsoft - dividend analysis</code>
                <p className="text-sm text-gray-500 mt-1">Income-focused analysis</p>
              </div>
            </div>
          </section>

          <section className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-yellow-900 mb-2">Disclaimer</h2>
            <p className="text-yellow-800">
              This tool is for informational purposes only and should not be considered investment advice. 
              Always conduct your own due diligence and consult with a qualified financial advisor before 
              making investment decisions. Past performance does not guarantee future results.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
