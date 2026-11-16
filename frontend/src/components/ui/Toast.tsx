'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType, duration?: number) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const success = useCallback((msg: string) => addToast(msg, 'success'), [addToast]);
  const error = useCallback((msg: string) => addToast(msg, 'error'), [addToast]);
  const info = useCallback((msg: string) => addToast(msg, 'info'), [addToast]);

  return (
    <ToastContext.Provider value={{ toast: addToast, success, error, info }}>
      {children}
      <div
        role="region"
        aria-live="polite"
        className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl border shadow-2xl backdrop-blur-xl transition-all animate-in slide-in-from-bottom-2 duration-200 ${
              t.type === 'success'
                ? 'bg-[#0C2422]/85 border-[#28C995]/40 text-[#28C995] shadow-[0_8px_32px_rgba(4,9,20,0.5),inset_0_1px_0_rgba(40,201,149,0.3)]'
                : t.type === 'error'
                ? 'bg-[#24121B]/85 border-[#F16B7A]/40 text-[#F16B7A] shadow-[0_8px_32px_rgba(4,9,20,0.5),inset_0_1px_0_rgba(241,107,122,0.3)]'
                : 'bg-[#111E35]/85 border-[#438BFF]/40 text-[#8DBBFF] shadow-[0_8px_32px_rgba(4,9,20,0.5),inset_0_1px_0_rgba(67,139,255,0.3)]'
            }`}
          >
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-[#28C995] shrink-0 mt-0.5" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 text-[#F16B7A] shrink-0 mt-0.5" />}
            {t.type === 'info' && <Info className="w-4 h-4 text-[#438BFF] shrink-0 mt-0.5" />}
            <span className="text-xs font-medium leading-relaxed flex-1 text-[#F1F6FF]">{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              className="text-[#7285A5] hover:text-white transition-colors"
              aria-label="Close notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      toast: (msg) => console.log(`[Toast] ${msg}`),
      success: (msg) => console.log(`[Toast Success] ${msg}`),
      error: (msg) => console.error(`[Toast Error] ${msg}`),
      info: (msg) => console.log(`[Toast Info] ${msg}`),
    };
  }
  return context;
}
