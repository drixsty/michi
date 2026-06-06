'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { MessageSquare, X, Send, User, Building, Code2, ClipboardCopy, CheckCircle2 } from 'lucide-react';
import { useStore } from './StoreContext';

interface SupportContextType {
  openWidget: () => void;
  closeWidget: () => void;
}

const SupportContext = createContext<SupportContextType | undefined>(undefined);

export function SupportProvider({ children }: { children: React.ReactNode }) {
  const { user, currentOrganization } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'agent'; text: string; time: string }>>([
    { sender: 'agent', text: 'Bonjour ! Comment puis-je vous aider avec vos prévisions ou intégrations Michi ?', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [flowId, setFlowId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const provider = process.env.NEXT_PUBLIC_SUPPORT_PROVIDER;
  const widgetId = process.env.NEXT_PUBLIC_SUPPORT_WIDGET_ID;

  useEffect(() => {
    // Load stored flowId
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('michi_last_error_flow_id');
      if (stored) {
        setFlowId(stored);
      }
    }

    if (provider && widgetId && typeof window !== 'undefined') {
      if (provider === 'crisp') {
        // Crisp loader script
        (window as any).$crisp = [];
        (window as any).CRISP_WEBSITE_ID = widgetId;
        const d = document;
        const s = d.createElement('script');
        s.src = 'https://client.crisp.chat/l.js';
        s.async = true;
        d.getElementsByTagName('head')[0].appendChild(s);
      }
    }
  }, [provider, widgetId]);

  // Set user properties in the real chat widget if active
  useEffect(() => {
    if (user && typeof window !== 'undefined') {
      if (provider === 'crisp' && (window as any).$crisp) {
        (window as any).$crisp.push(['set', 'user:email', user.email]);
        (window as any).$crisp.push(['set', 'user:nickname', `${user.firstName || ''} ${user.lastName || ''}`.trim()]);
        if (currentOrganization) {
          (window as any).$crisp.push(['set', 'session:data', [['organization_id', currentOrganization.id], ['organization_name', currentOrganization.name]]]);
        }
        if (flowId) {
          (window as any).$crisp.push(['set', 'session:data', [['last_flow_id', flowId]]]);
        }
      }
    }
  }, [user, currentOrganization, provider, flowId]);

  const openWidget = () => {
    if (provider && widgetId) {
      if (provider === 'crisp' && (window as any).$crisp) {
        (window as any).$crisp.push(['do', 'chat:open']);
      }
    } else {
      setIsOpen(true);
    }
  };

  const closeWidget = () => {
    setIsOpen(false);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = {
      sender: 'user' as const,
      text: inputValue,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');

    // Simulate Agent reply
    setTimeout(() => {
      let replyText = "Merci pour votre message. Un agent support qualifié étudie votre demande. ";
      if (flowId) {
        replyText += `Nous avons bien détecté l'ID de corrélation ${flowId} lié à votre session pour faciliter notre analyse.`;
      } else {
        replyText += "N'hésitez pas à nous envoyer les détails de diagnostic si vous rencontrez un bug.";
      }

      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: replyText,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }, 1000);
  };

  const handleCopyDiagnostics = () => {
    if (typeof window === 'undefined') return;
    const diagInfo = {
      user: user ? { id: user.id, email: user.email, name: `${user.firstName || ''} ${user.lastName || ''}`.trim() } : 'Unauthenticated',
      organization: currentOrganization ? { id: currentOrganization.id, name: currentOrganization.name } : 'None',
      lastFlowId: flowId || 'None',
      url: window.location.href,
      userAgent: navigator.userAgent,
      time: new Date().toISOString()
    };
    navigator.clipboard.writeText(JSON.stringify(diagInfo, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <SupportContext.Provider value={{ openWidget, closeWidget }}>
      {children}

      {/* Floating Support Bubble Trigger (only if no real provider script is injected) */}
      {(!provider || !widgetId) && (
        <>
          <button
            onClick={openWidget}
            className="fixed bottom-6 right-6 z-[90] w-14 h-14 bg-primary text-white rounded-full flex items-center justify-center shadow-[0_4px_20px_rgba(var(--primary),0.3)] hover:scale-110 hover:shadow-[0_4px_25px_rgba(var(--primary),0.4)] transition-all active:scale-95 focus:ring-0 focus:outline-none"
            aria-label="Contacter le support"
          >
            <MessageSquare className="h-6 w-6" />
          </button>

          {/* Simulated Premium Support Widget Modal */}
          {isOpen && (
            <div className="fixed bottom-24 right-6 z-[100] w-[380px] max-w-[calc(100vw-2rem)] h-[560px] max-h-[calc(100vh-8rem)] bg-slate-900 border border-slate-800 rounded-2xl flex flex-col shadow-2xl overflow-hidden font-sans text-slate-100 animate-in slide-in-from-bottom-5 duration-300">
              {/* Header */}
              <div className="bg-slate-950 p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 border border-slate-950" />
                    <div className="w-9 h-9 bg-primary/10 border border-primary/20 rounded-lg flex items-center justify-center text-primary font-extrabold text-sm">
                      M
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white tracking-tight">Support Michi 道</h4>
                    <p className="text-[9px] text-slate-400 font-medium">Réponse sous 10 minutes</p>
                  </div>
                </div>
                <button
                  onClick={closeWidget}
                  className="p-1 hover:bg-slate-800 rounded-md text-slate-400 hover:text-white transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Chat Session Details (Collapsible / Diagnostic view) */}
              <div className="p-3 bg-slate-950/40 border-b border-slate-800/80 space-y-2 text-[9px] font-mono text-slate-400">
                <div className="flex justify-between items-center">
                  <span className="font-bold flex items-center gap-1"><User className="h-3 w-3 text-slate-500" /> Client</span>
                  <span className="text-slate-300 font-semibold truncate max-w-[200px]">{user?.email || 'Visiteur'}</span>
                </div>
                {currentOrganization && (
                  <div className="flex justify-between items-center">
                    <span className="font-bold flex items-center gap-1"><Building className="h-3 w-3 text-slate-500" /> Org</span>
                    <span className="text-slate-300 font-semibold truncate max-w-[200px]">{currentOrganization.name}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="font-bold flex items-center gap-1"><Code2 className="h-3 w-3 text-slate-500" /> Corrélation ID</span>
                  <div className="flex items-center gap-1">
                    <span className="text-slate-300 font-semibold truncate max-w-[150px]">{flowId || 'N/A'}</span>
                    <button
                      onClick={handleCopyDiagnostics}
                      className="p-0.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
                      title="Copier les métadonnées de diagnostic"
                    >
                      {copied ? <CheckCircle2 className="h-3 w-3 text-emerald-400" /> : <ClipboardCopy className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Messages Body */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-900/40">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex flex-col max-w-[85%] ${
                      msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
                    }`}
                  >
                    <div
                      className={`p-3 rounded-2xl text-xs leading-normal ${
                        msg.sender === 'user'
                          ? 'bg-primary text-white rounded-tr-none'
                          : 'bg-slate-800 text-slate-200 rounded-tl-none'
                      }`}
                    >
                      {msg.text}
                    </div>
                    <span className="text-[8px] text-slate-500 mt-1 font-semibold">{msg.time}</span>
                  </div>
                ))}
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-800 bg-slate-950 flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Tapez votre message..."
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-primary/40 focus:ring-0 focus:ring-offset-0"
                />
                <button
                  type="submit"
                  className="p-2 bg-primary hover:bg-primary/90 rounded-lg text-white transition-all active:scale-95 focus:ring-0 focus:outline-none"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          )}
        </>
      )}
    </SupportContext.Provider>
  );
}

export function useSupport() {
  const context = useContext(SupportContext);
  if (!context) {
    throw new Error('useSupport must be used within a SupportProvider');
  }
  return context;
}
