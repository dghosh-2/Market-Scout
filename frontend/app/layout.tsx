import './globals.css';
import { QueryProvider } from '@/components/QueryProvider';

export const metadata = {
  title: 'StockResearch - AI-Powered Stock Analysis',
  description: 'Generate comprehensive research reports on any publicly traded company',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
