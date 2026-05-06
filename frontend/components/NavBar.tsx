'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/research', label: 'Research' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/papers', label: 'Papers' },
  { href: '/about', label: 'About' },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2 text-white tracking-[0.2em] uppercase text-[11px] font-medium">
          <span className="inline-grid grid-cols-2 gap-0.5 w-3 h-3 opacity-90" aria-hidden>
            <span className="bg-white rounded-[1px]" />
            <span className="bg-white rounded-[1px]" />
            <span className="bg-white rounded-[1px]" />
            <span className="bg-white rounded-[1px]" />
          </span>
          Market Scout
        </Link>

        <nav className="hidden sm:flex items-center rounded-full border border-white/15 bg-white/[0.04] px-1 py-1">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 text-[10px] uppercase tracking-[0.2em] rounded-full transition-colors ${
                  active ? 'bg-white text-black' : 'text-white/55 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <Link
          href="/research"
          className="text-[10px] uppercase tracking-[0.2em] px-4 py-2 rounded-full bg-white text-black font-medium hover:bg-white/90 transition-colors shrink-0 inline-flex items-center gap-1"
        >
          Start
          <span aria-hidden className="text-xs">
            ↗
          </span>
        </Link>
      </div>
    </header>
  );
}
