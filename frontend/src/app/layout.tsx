import './globals.css';
import React from 'react';

export const metadata = {
  title: 'SEOOps - Autonomous AI-Powered SEO Engine',
  description: 'Continuous SEO monitoring, incremental crawling, hashing, and AI fix recommendations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          {children}
        </div>
      </body>
    </html>
  );
}
