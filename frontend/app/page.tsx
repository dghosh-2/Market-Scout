'use client';

import Link from 'next/link';
import NavBar from '../components/NavBar';
import ParticleWave from '../components/ParticleWave';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      <NavBar />

      <main className="flex-1 flex flex-col relative">
        <div className="flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-8 text-center">
          <p className="animate-fadeIn text-[10px] md:text-[11px] tracking-[0.45em] uppercase text-white/50 mb-8">
            Intelligence layer
          </p>
          <h1 className="animate-fadeIn text-4xl md:text-6xl lg:text-7xl font-extralight tracking-[0.12em] uppercase leading-tight">
            Market
            <br />
            Scout
          </h1>
          <p className="mt-10 text-sm text-white/40 font-light max-w-sm leading-relaxed">
            Research reports, price context, and portfolio fit—without the noise.
          </p>

          <div className="mt-14 flex flex-col sm:flex-row items-center gap-4">
            <Link
              href="/research"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-white text-black text-xs font-medium uppercase tracking-[0.2em] hover:bg-white/90 transition-colors"
            >
              Research
              <span aria-hidden>↗</span>
            </Link>
            <Link
              href="/portfolio"
              className="text-[10px] uppercase tracking-[0.25em] text-white/45 hover:text-white/80 transition-colors"
            >
              Portfolio
            </Link>
          </div>
        </div>

        <div className="h-[38vh] min-h-[200px] w-full relative border-t border-white/10">
          <ParticleWave className="absolute inset-0 opacity-90" density={16} />
        </div>
      </main>

      <footer className="border-t border-white/10 py-6 text-center text-[10px] uppercase tracking-[0.2em] text-white/30">
        Not investment advice
      </footer>
    </div>
  );
}
