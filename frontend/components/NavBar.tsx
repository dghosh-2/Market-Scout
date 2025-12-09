'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function NavBar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Home' },
    { href: '/research', label: 'Research' },
    { href: '/portfolio', label: 'Portfolio' },
    { href: '/papers', label: 'Papers' },
    { href: '/about', label: 'About' },
  ];

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-neutral-200/60">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-emerald-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <span className="text-lg font-semibold text-neutral-900 group-hover:text-blue-600 transition-colors">
              MarketScout
            </span>
          </Link>
          
          <div className="flex items-center gap-1">
            {links.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-neutral-100 text-neutral-900'
                      : 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
