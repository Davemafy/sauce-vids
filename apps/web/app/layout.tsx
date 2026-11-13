import type { Metadata, Viewport } from 'next';
import { Big_Shoulders, Instrument_Sans, Lobster } from 'next/font/google';
import './globals.css';

const display = Big_Shoulders({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-big-shoulders',
  adjustFontFallback: false,
  weight: ['600', '700', '800', '900'],
});

const body = Instrument_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-instrument',
});

const script = Lobster({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-lobster',
  weight: '400',
});

export const metadata: Metadata = {
  title: 'Sauce — Make software worth watching',
  description:
    'Sauce turns real product interactions into polished, AI-directed demos for launches, changelogs, and pull requests. Join the early-access waitlist.',
  applicationName: 'Sauce Vids',
  openGraph: {
    title: 'Sauce — Make software worth watching',
    description: 'Real product interactions. AI-directed demo films. Early access is opening.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#b30713',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} ${script.variable} bg-sauce-cream text-sauce-ink antialiased`}>
        {children}
      </body>
    </html>
  );
}
