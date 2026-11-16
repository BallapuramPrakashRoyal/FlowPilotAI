'use client';

import React, { FormEvent, useState } from 'react';
import { AlertCircle, Loader2, LogIn, UserPlus, Zap } from 'lucide-react';
import { api } from '@/services/api';
import { User } from '@/types';

interface AuthViewProps {
  onAuthenticated: (user: User) => void;
}

export function AuthView({ onAuthenticated }: AuthViewProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result =
        mode === 'login'
          ? await api.login(email, password)
          : await api.register(email, password, fullName);
      onAuthenticated(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to authenticate. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#080F20] px-4 py-8 overflow-hidden">
      {/* Ambient liquid glass lights */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-[#287BFA]/10 to-transparent blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-[450px] h-[450px] rounded-full bg-gradient-to-tl from-[#53D7F5]/08 to-transparent blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-md rounded-3xl bg-[#111E35]/75 backdrop-blur-2xl border border-[rgba(67,139,255,0.22)] p-8 shadow-[0_20px_50px_rgba(4,9,20,0.7),inset_0_1px_1px_rgba(255,255,255,0.15)]">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#287BFA] via-[#438BFF] to-[#53D7F5] flex items-center justify-center shadow-lg shadow-[#287BFA]/30 ring-1 ring-white/20">
            <Zap className="w-5 h-5 text-white fill-white" />
          </div>
          <div>
            <div className="text-lg font-bold text-[#F1F6FF] tracking-tight">FlowPilot AI</div>
            <div className="text-xs text-[#7285A5]">Autonomous Automation</div>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-[#F1F6FF] tracking-tight">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>
        <p className="mt-2 text-sm text-[#A3B4CF]">
          {mode === 'login'
            ? 'Sign in to manage your workflows and executions.'
            : 'Start building governed AI workflows in your own workspace.'}
        </p>

        <div className="mt-6 grid grid-cols-2 gap-2 rounded-2xl bg-[#0C1629]/70 p-1 border border-[rgba(67,139,255,0.15)]">
          <button
            type="button"
            onClick={() => { setMode('login'); setError(null); }}
            className={`rounded-xl px-3 py-2 text-xs font-semibold transition-all ${
              mode === 'login'
                ? 'bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white shadow-md shadow-[#287BFA]/25 border border-white/20'
                : 'text-[#A3B4CF] hover:text-[#F1F6FF]'
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => { setMode('register'); setError(null); }}
            className={`rounded-xl px-3 py-2 text-xs font-semibold transition-all ${
              mode === 'register'
                ? 'bg-gradient-to-r from-[#287BFA] to-[#438BFF] text-white shadow-md shadow-[#287BFA]/25 border border-white/20'
                : 'text-[#A3B4CF] hover:text-[#F1F6FF]'
            }`}
          >
            Create account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {mode === 'register' && (
            <label className="block text-xs font-medium text-[#A3B4CF]">
              Full name
              <input
                required
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="mt-1.5 w-full rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] px-3.5 py-2.5 text-xs text-[#F1F6FF] outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] transition-all"
                autoComplete="name"
              />
            </label>
          )}
          <label className="block text-xs font-medium text-[#A3B4CF]">
            Email
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1.5 w-full rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] px-3.5 py-2.5 text-xs text-[#F1F6FF] outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] transition-all"
              autoComplete="email"
            />
          </label>
          <label className="block text-xs font-medium text-[#A3B4CF]">
            Password
            <input
              required
              minLength={8}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1.5 w-full rounded-xl bg-[#0C1629]/70 border border-[rgba(67,139,255,0.18)] px-3.5 py-2.5 text-xs text-[#F1F6FF] outline-none focus:border-[#438BFF] focus:shadow-[0_0_12px_rgba(67,139,255,0.25)] transition-all font-mono"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </label>

          {error && (
            <div className="flex items-start gap-2 rounded-2xl border border-[#F16B7A]/35 bg-[#24121B]/85 px-3.5 py-2.5 text-xs text-[#F16B7A] backdrop-blur-xl">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#287BFA] to-[#438BFF] hover:from-[#3786FF] hover:to-[#53D7F5] px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-[#287BFA]/30 border border-white/20 transition-all hover:-translate-y-0.5 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === 'login' ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
            {isSubmitting ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  );
}
