'use client';

import Link from 'next/link';
import NavBar from '../components/NavBar';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-neutral-50 gradient-mesh">
      <NavBar />
      
      <main className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-20 animate-fadeIn">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-medium mb-6">
            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            AI-Powered Research
          </div>
          
          <h1 className="text-5xl md:text-6xl font-semibold text-neutral-900 mb-6 tracking-tight leading-tight">
            Investment Research,<br />
            <span className="bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent">
              Reimagined
            </span>
          </h1>
          
          <p className="text-xl text-neutral-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            Generate comprehensive research reports on any publicly traded company. 
            Financial analysis, risk assessment, and market insights in seconds.
          </p>
          
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/research"
              className="px-8 py-4 bg-neutral-900 text-white rounded-xl text-lg font-medium 
                       hover:bg-neutral-800 transition-all duration-200 active:scale-[0.98]
                       shadow-medium hover:shadow-lg"
            >
              Start Research
            </Link>
            <Link
              href="/portfolio"
              className="px-8 py-4 bg-white text-neutral-900 rounded-xl text-lg font-medium 
                       border border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50
                       transition-all duration-200 active:scale-[0.98]"
            >
              My Portfolio
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
          {[
            {
              title: 'Smart Resolution',
              desc: 'Enter company names in plain English. Our AI resolves "that electric car company" to TSLA automatically.',
              gradient: 'from-blue-500 to-blue-600',
            },
            {
              title: 'Deep Analysis',
              desc: 'Financial metrics, risk factors, news sentiment, and actionable recommendations in one comprehensive report.',
              gradient: 'from-emerald-500 to-emerald-600',
            },
            {
              title: 'Portfolio Fit',
              desc: 'See how any stock would fit into your existing portfolio with personalized diversification insights.',
              gradient: 'from-violet-500 to-violet-600',
            },
          ].map((feature, i) => (
            <div 
              key={feature.title} 
              className="card card-hover p-6 animate-fadeIn"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${feature.gradient} mb-4 flex items-center justify-center`}>
                <div className="w-5 h-5 bg-white/20 rounded-md" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">{feature.title}</h3>
              <p className="text-neutral-500 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>

        <div className="card p-8 mb-20 animate-fadeIn stagger-4">
          <h2 className="text-2xl font-semibold text-neutral-900 mb-8 text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { step: '1', title: 'Enter Query', desc: 'Type a company name, ticker, or description', color: 'blue' },
              { step: '2', title: 'AI Analysis', desc: 'Multiple agents gather and analyze data', color: 'emerald' },
              { step: '3', title: 'Review Live', desc: 'Watch charts and metrics populate in real-time', color: 'violet' },
              { step: '4', title: 'Download', desc: 'Get your professional PDF report instantly', color: 'amber' },
            ].map((item, i) => (
              <div key={item.step} className="text-center relative">
                {i < 3 && (
                  <div className="hidden md:block absolute top-5 left-[60%] w-[80%] h-px bg-gradient-to-r from-neutral-200 to-transparent" />
                )}
                <div className={`
                  w-10 h-10 rounded-xl mx-auto mb-4 flex items-center justify-center text-lg font-semibold
                  ${item.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                    item.color === 'emerald' ? 'bg-emerald-100 text-emerald-600' :
                    item.color === 'violet' ? 'bg-violet-100 text-violet-600' :
                    'bg-amber-100 text-amber-600'}
                `}>
                  {item.step}
                </div>
                <h4 className="font-semibold text-neutral-900 mb-1">{item.title}</h4>
                <p className="text-sm text-neutral-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="text-center animate-fadeIn stagger-5">
          <p className="text-sm text-neutral-400 mb-4">Trusted data sources</p>
          <div className="flex items-center justify-center gap-8 text-neutral-300">
            <span className="text-lg font-semibold">Yahoo Finance</span>
            <span className="w-1 h-1 bg-neutral-300 rounded-full" />
            <span className="text-lg font-semibold">SEC Filings</span>
            <span className="w-1 h-1 bg-neutral-300 rounded-full" />
            <span className="text-lg font-semibold">News APIs</span>
          </div>
        </div>
      </main>

      <footer className="border-t border-neutral-200/60 py-8 mt-20">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-neutral-400">
          For informational purposes only. Not investment advice.
        </div>
      </footer>
    </div>
  );
}
