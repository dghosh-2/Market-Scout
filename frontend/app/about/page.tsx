'use client';

import NavBar from '../../components/NavBar';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <NavBar />

      <main className="max-w-2xl mx-auto px-6 py-16">
        <p className="text-[10px] tracking-[0.35em] uppercase text-white/45 mb-4">About</p>
        <h1 className="text-2xl font-extralight tracking-[0.12em] uppercase mb-10">Market Scout</h1>

        <div className="space-y-10 text-sm text-white/55 font-light leading-relaxed">
          <section>
            <h2 className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-3">Flow</h2>
            <p>
              You describe a company in plain language. We resolve the listing, pull market data and news, run a
              structured write-up, and render a PDF. Optional portfolio context adjusts the &ldquo;fit&rdquo; section.
            </p>
          </section>

          <section>
            <h2 className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-3">Sources</h2>
            <ul className="space-y-2 list-disc pl-5 marker:text-white/25">
              <li>Market data via Yahoo Finance (yfinance)</li>
              <li>LLM drafting (OpenAI)</li>
              <li>Your saved runs in the hosted database</li>
            </ul>
          </section>

          <section className="border border-white/15 p-5 rounded-sm text-white/60">
            <h2 className="text-[10px] uppercase tracking-[0.25em] text-white/40 mb-3">Disclaimer</h2>
            <p>
              Informational only. Not investment advice. Verify material facts and consult a professional before
              allocating capital.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
