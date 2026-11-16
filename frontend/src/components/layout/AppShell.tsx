'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { api } from '@/services/api';
import { PublicLandingView } from '@/features/landing/PublicLandingView';
import { User } from '@/types';
import { ToastProvider } from '@/components/ui/Toast';

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(1);
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!api.getToken()) {
      queueMicrotask(() => setAuthChecked(true));
      return;
    }

    api.getMe()
      .then(setUser)
      .catch(() => api.clearSession())
      .finally(() => setAuthChecked(true));
  }, []);

  useEffect(() => {
    if (!user) return;
    async function checkPending() {
      try {
        const apprs = await api.listApprovals('PENDING');
        setPendingApprovalsCount(apprs.length);
      } catch {
        setPendingApprovalsCount(0);
      }
    }
    checkPending();
  }, [user]);

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-[#080F20] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-[#438BFF]/30 border-t-[#438BFF] animate-spin" />
      </div>
    );
  }

  if (!user || pathname === '/auth') {
    return <PublicLandingView onAuthenticated={setUser} />;
  }

  return (
    <ToastProvider>
      <div className="relative flex h-screen w-screen overflow-hidden bg-[#080F20] text-[#F1F6FF] selection:bg-[#287BFA]/30 selection:text-[#53D7F5]">
        {/* Ambient Liquid Glass Floating Glows (Hardware accelerated, non-blocking) */}
        <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
          {/* Top-left electric blue liquid orb */}
          <div className="absolute -top-32 -left-32 w-[600px] h-[500px] rounded-full bg-gradient-to-br from-[#287BFA]/10 via-[#438BFF]/05 to-transparent blur-3xl" />
          {/* Top-right soft cyan liquid highlight */}
          <div className="absolute -top-24 right-0 w-[550px] h-[450px] rounded-full bg-gradient-to-bl from-[#53D7F5]/08 via-[#287BFA]/04 to-transparent blur-3xl" />
          {/* Bottom-center deep indigo reflection */}
          <div className="absolute -bottom-48 left-1/3 w-[700px] h-[550px] rounded-full bg-gradient-to-t from-[#1E3A8A]/10 via-[#111E35]/06 to-transparent blur-3xl" />
        </div>

        {/* Mobile Backdrop Overlay */}
        {mobileMenuOpen && (
          <div
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
            aria-hidden="true"
          />
        )}

        {/* Navigation Sidebar */}
        <Sidebar
          pendingApprovalsCount={pendingApprovalsCount}
          user={user}
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          onLogout={() => {
            void api.logout();
            setUser(null);
          }}
        />

        {/* Main Application Area */}
        <div className="relative z-10 flex-1 flex flex-col min-w-0 overflow-y-auto w-full">
          <Header onToggleMobileMenu={() => setMobileMenuOpen((prev) => !prev)} />
          <main className="flex-1 min-w-0 w-full">{children}</main>
        </div>
      </div>
    </ToastProvider>
  );
}
