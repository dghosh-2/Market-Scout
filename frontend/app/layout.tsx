import './globals.css';
import { QueryProvider } from '../components/QueryProvider';
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  weight: ['200', '300', '400', '500', '600'],
  display: 'swap',
});

export const metadata = {
  title: 'Market Scout',
  description: 'Stock research, distilled.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-black text-white antialiased`}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
