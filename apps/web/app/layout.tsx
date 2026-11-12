import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sauce — A screen recording is not a demo.',
  description:
    'Capture real browser interactions and turn them into product demos worth watching. Sauce is open-source and built for developers and AI agents.',
  applicationName: 'Sauce Vids',
  openGraph: {
    title: 'Sauce — A screen recording is not a demo.',
    description: 'Real software. Better presentation. Made for people who ship.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#f9ede0',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}