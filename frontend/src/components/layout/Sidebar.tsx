'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  GitFork,
  Sparkles,
  Workflow,
  CheckCircle2,
  Activity,
  Layers,
  BookOpen,
  BarChart3,
  Settings,
  ChevronDown,
  ShieldCheck,
  Zap,
  Compass,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { User } from '@/types';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

interface SidebarProps {
  pendingApprovalsCount?: number;
  user?: User | null;
  onLogout?: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ pendingApprovalsCount = 0, user, onLogout, isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();

  const navItems: NavItem[] = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Guided Setup', href: '/onboarding', icon: Compass },
    { name: 'Workflows', href: '/workflows', icon: GitFork },
    { name: 'AI Generator', href: '/generator', icon: Sparkles },
    { name: 'Workflow Studio', href: '/studio', icon: Workflow },
    { name: 'Approvals', href: '/approvals', icon: CheckCircle2, badge: pendingApprovalsCount },
    { name: 'Executions', href: '/executions', icon: Activity },
    { name: 'Integrations', href: '/integrations', icon: Layers },
    { name: 'Knowledge Base', href: '/knowledge', icon: BookOpen },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 h-screen flex flex-col bg-[#0C1629]/95 lg:bg-[#0C1629]/80 backdrop-blur-2xl border-r border-[rgba(67,139,255,0.15)] shadow-[inset_-1px_0_1px_rgba(255,255,255,0.05),0_8px_32px_rgba(4,9,20,0.5)] select-none shrink-0 transition-transform duration-300 lg:static lg:translate-x-0',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      {/* Brand & Workspace Switcher */}
      <div className="p-4 border-b border-[rgba(67,139,255,0.12)]">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#287BFA] via-[#438BFF] to-[#53D7F5] flex items-center justify-center shadow-lg shadow-[#287BFA]/30 ring-1 ring-white/20">
              <Zap className="w-5 h-5 text-white fill-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]" />
            </div>
            <div>
              <div className="font-semibold text-[#F1F6FF] tracking-tight flex items-center gap-1.5 text-sm">
                FlowPilot AI
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#287BFA]/15 text-[#53D7F5] border border-[#287BFA]/30">
                  v1.0
                </span>
              </div>
              <div className="text-xs text-[#7285A5]">Autonomous Automation</div>
            </div>
          </div>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#7285A5] hover:text-[#F1F6FF] hover:bg-[#111E35] lg:hidden transition-colors"
              aria-label="Close navigation"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Workspace selector */}
        <button
          type="button"
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-[#111E35]/70 hover:bg-[#172743]/90 border border-[rgba(67,139,255,0.16)] hover:border-[rgba(83,215,245,0.3)] text-xs text-[#F1F6FF] transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
        >
          <div className="flex items-center gap-2 truncate">
            <div className="w-2 h-2 rounded-full bg-[#28C995] shadow-[0_0_8px_rgba(40,201,149,0.7)]" />
            <span className="truncate font-medium">Acme Autonomous Ops</span>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-[#7285A5]" />
        </button>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={cn(
                'flex items-center justify-between px-3 py-2 rounded-xl text-sm font-medium transition-all group relative',
                isActive
                  ? 'bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white shadow-[0_0_20px_rgba(40,123,250,0.35),inset_0_1px_0_rgba(255,255,255,0.3)] border border-white/20'
                  : 'text-[#A3B4CF] hover:text-[#F1F6FF] hover:bg-[#111E35]/60 hover:border hover:border-[rgba(67,139,255,0.15)] border border-transparent'
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    'w-4 h-4 transition-colors',
                    isActive
                      ? 'text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.3)]'
                      : 'text-[#7285A5] group-hover:text-[#53D7F5]'
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={cn(
                    'px-2 py-0.5 text-xs font-semibold rounded-full transition-colors',
                    isActive
                      ? 'bg-white text-[#287BFA]'
                      : 'bg-[#F2B65D]/15 text-[#F2B65D] border border-[#F2B65D]/30 shadow-[0_0_8px_rgba(242,182,93,0.2)]'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User profile & system status */}
      <div className="p-3 border-t border-[rgba(67,139,255,0.12)] bg-[#080F20]/50 backdrop-blur-md">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#111E35]/60 border border-[rgba(67,139,255,0.12)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#287BFA] to-[#53D7F5] flex items-center justify-center text-xs font-bold text-white uppercase shadow-md shadow-[#287BFA]/20 ring-1 ring-white/20">
            {user?.full_name ? user.full_name.slice(0, 2).toUpperCase() : 'AM'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-[#F1F6FF] truncate">{user?.full_name || 'User'}</div>
            <div className="text-[11px] text-[#7285A5] flex items-center gap-1 truncate">
              <ShieldCheck className="w-3 h-3 text-[#28C995]" /> {user?.is_superuser ? 'Owner' : 'Member'}
            </div>
          </div>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="text-[11px] text-[#7285A5] hover:text-[#53D7F5] transition-colors px-1.5 py-1 rounded-md hover:bg-[#172743]"
              title="Sign out"
            >
              Sign out
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
