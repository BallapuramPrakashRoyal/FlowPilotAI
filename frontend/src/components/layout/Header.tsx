'use client';

import React from 'react';
import { Search, Bell, Play, Menu } from 'lucide-react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  onQuickRun?: () => void;
  onToggleMobileMenu?: () => void;
}

export function Header({
  title = 'Dashboard',
  subtitle = 'Autonomous operations overview',
  onQuickRun,
  onToggleMobileMenu,
}: HeaderProps) {
  return (
    <header className="h-16 px-4 sm:px-6 border-b border-[rgba(67,139,255,0.15)] bg-[#080F20]/75 backdrop-blur-xl flex items-center justify-between sticky top-0 z-30 shadow-[0_4px_24px_rgba(4,9,20,0.4)] transition-all">
      <div className="flex items-center gap-3">
        {onToggleMobileMenu && (
          <button
            type="button"
            onClick={onToggleMobileMenu}
            className="p-2 rounded-xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.3)] text-[#A3B4CF] hover:text-[#53D7F5] lg:hidden transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}
        <div>
          <h1 className="text-base font-semibold text-[#F1F6FF] tracking-tight">{title}</h1>
          <p className="text-xs text-[#7285A5]">{subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Search / Command Shortcut */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-[#7285A5] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search workflows, nodes, logs (⌘K)..."
            className="w-64 pl-9 pr-4 py-1.5 rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] focus:border-[#438BFF] text-xs text-[#F1F6FF] placeholder-[#7285A5] focus:outline-none focus:shadow-[0_0_16px_rgba(67,139,255,0.25)] transition-all"
          />
        </div>

        {/* Quick Execute Button */}
        {onQuickRun && (
          <button
            onClick={onQuickRun}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-[#28C995] to-[#20A27A] hover:from-[#2ED8A0] hover:to-[#24B88A] text-white text-xs font-medium shadow-md shadow-[#28C995]/25 border border-white/20 transition-all active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Execute</span>
          </button>
        )}

        {/* Notifications */}
        <button
          type="button"
          aria-label="System notifications"
          className="p-2 rounded-xl bg-[#111E35]/70 hover:bg-[#172743] border border-[rgba(67,139,255,0.18)] hover:border-[rgba(83,215,245,0.3)] text-[#A3B4CF] hover:text-[#53D7F5] transition-all relative shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
        >
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-[#438BFF] absolute top-1.5 right-1.5 animate-pulse shadow-[0_0_8px_rgba(67,139,255,0.8)]" />
        </button>
      </div>
    </header>
  );
}
