import type { Metadata, Viewport } from 'next';
import '@fontsource-variable/big-shoulders-display';
import '@fontsource-variable/instrument-sans';
import '@fontsource/lobster/400.css';
import './globals.css';

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
      <body className="bg-sauce-cream text-sauce-ink antialiased">
        {children}
      </body>
    </html>
  );
}
