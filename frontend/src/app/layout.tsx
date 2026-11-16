import type { Metadata } from 'next';
import './globals.css';
import { AppShell } from '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: 'FlowPilot AI — Autonomous AI Workflow Automation Platform',
  description: 'Design, generate, execute, and monitor intelligent multi-agent workflows with human-in-the-loop governance.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#10131B] text-[#F8FAFC]">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
