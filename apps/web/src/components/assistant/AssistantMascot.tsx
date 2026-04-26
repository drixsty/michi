'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X, MessageSquare, Sparkles, Bot, User, Plus, History, Trash2, Edit2, Check, RotateCcw, ChevronLeft, ArrowRight, Settings } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// --- Types & Logic ---
const useAssistant = (endpoint: string = "http://localhost:8001/graphql") => {
  const [messages, setMessages] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(typeof window !== 'undefined' ? localStorage.getItem('michi_assistant_session_id') : null);

  const fetchSessions = useCallback(async () => {
    const query = `query { listSessions { sessionId updatedAt lastMessage } }`;
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('michi_token')}`
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      if (data.data?.listSessions) setSessions(data.data.listSessions);
    } catch (e) { console.error(e); }
  }, [endpoint]);

  const loadSession = useCallback(async (sid: string) => {
    const query = `query GetHistory($sid: String!) { getChatHistory(sessionId: $sid) { role content timestamp } }`;
    setIsLoading(true);
    setSessionId(sid);
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('michi_token')}`
        },
        body: JSON.stringify({ query, variables: { sid } }),
      });
      const data = await response.json();
      if (data.data?.getChatHistory) setMessages(data.data.getChatHistory);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  }, [endpoint]);

  const deleteSession = useCallback(async (sid: string) => {
    const query = `mutation Delete($sid: String!) { deleteSession(sessionId: $sid) }`;
    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('michi_token')}`
        },
        body: JSON.stringify({ query, variables: { sid } }),
      });
      if (sessionId === sid) {
        setSessionId(null);
        setMessages([]);
      }
      fetchSessions();
    } catch (e) { console.error(e); }
  }, [endpoint, sessionId, fetchSessions]);

  const sendMessage = useCallback(async (content: string, editIndex?: number) => {
    if (!content.trim()) return;
    setIsLoading(true);

    if (editIndex !== undefined && sessionId) {
      const truncateQuery = `mutation Truncate($sid: String!, $idx: Int!) { truncateSession(sessionId: $sid, index: $idx) }`;
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('michi_token')}` },
        body: JSON.stringify({ query: truncateQuery, variables: { sid: sessionId, idx: editIndex } }),
      });
      setMessages(prev => prev.slice(0, editIndex));
    }

    setMessages(prev => [...prev, { role: 'user', content }]);

    const query = `mutation Send($c: String!, $s: String) { sendMessage(content: $c, sessionId: $s) { reply sessionId } }`;
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('michi_token')}` },
        body: JSON.stringify({ query, variables: { c: content, s: sessionId } }),
      });
      const data = await response.json();
      const result = data.data.sendMessage;
      setMessages(prev => [...prev, { role: 'assistant', content: result.reply }]);
      if (!sessionId) {
        setSessionId(result.sessionId);
        localStorage.setItem('michi_assistant_session_id', result.sessionId);
        fetchSessions();
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Erreur de connexion au serveur." }]);
    } finally { setIsLoading(false); }
  }, [endpoint, sessionId, fetchSessions]);

  return { 
    messages, 
    sendMessage, 
    sessions, 
    fetchSessions, 
    loadSession, 
    deleteSession, 
    isOpen, 
    setIsOpen, 
    isLoading, 
    sessionId, 
    setSessionId, 
    setMessages,
    suggestedActions: messages.length > 0 && messages[messages.length - 1].role === 'assistant' 
      ? ["Optimiser mon stock", "Voir les alertes", "Générer un rapport"] 
      : []
  };
};

const SUGGESTIONS = [
  { icon: '📊', label: "Analyse de stock", prompt: "Analyse l'état de mon stock actuel." },
  { icon: '🚨', label: "Risques de rupture", prompt: "Quels sont mes produits à risque de rupture ?" },
  { icon: '💰', label: "Valeur totale", prompt: "Quelle est la valeur totale de mon stock ?" },
  { icon: '📈', label: "Prévisions 30j", prompt: "Quelles sont les prévisions de ventes pour le mois prochain ?" },
];

const COMMON_QUERIES = [
  "Analyse mon stock actuel",
  "Quels sont les risques de rupture ?",
  "Quelle est la valeur de mon stock ?",
  "Donne-moi les prévisions pour le mois prochain",
  "Générer un rapport d'inventaire",
  "Voir les alertes récentes",
  "Optimiser mes niveaux de stock",
  "Analyse du produit "
];

// --- Components ---

export const AssistantMascot = () => {
  const { 
    messages, sendMessage, sessions, fetchSessions, loadSession, deleteSession, 
    isOpen, setIsOpen, isLoading, sessionId, setSessionId, setMessages, suggestedActions 
  } = useAssistant();
  const [view, setView] = useState<'home' | 'chat'>('home');
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const filteredQueries = input.trim() && input.length > 1
    ? COMMON_QUERIES.filter(q => q.toLowerCase().includes(input.toLowerCase()) && q.toLowerCase() !== input.toLowerCase())
    : [];

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isLoading, view]);

  useEffect(() => { 
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen, fetchSessions]);

  // Initial load if sessionId exists
  useEffect(() => {
    if (sessionId && messages.length === 0) {
      loadSession(sessionId);
      setView('chat');
    }
  }, []); // Only on mount

  const startNewChat = () => {
    setSessionId(null);
    localStorage.removeItem('michi_assistant_session_id');
    setMessages([]);
    setView('chat');
  };

  const handleSessionClick = (sid: string) => {
    loadSession(sid);
    localStorage.setItem('michi_assistant_session_id', sid);
    setView('chat');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      if (editingIndex !== null) {
        sendMessage(input, editingIndex);
        setEditingIndex(null);
      } else {
        sendMessage(input);
      }
      setInput('');
    }
  };

  const startEdit = (index: number, content: string) => {
    setEditingIndex(index);
    setInput(content);
  };

  return (
    <div className="fixed bottom-8 right-8 z-[100] font-sans flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-20 right-0 w-[340px] max-h-[calc(100vh-120px)] h-[500px] bg-white rounded-lg shadow-[0_10px_30px_rgba(0,0,0,0.1)] border border-slate-200 flex flex-col overflow-hidden"
          >
            {/* --- HEADER FLAT --- */}
            <div className="px-5 py-4 bg-slate-900 text-white flex justify-between items-center shrink-0">
              <div className="flex items-center gap-3">
                {view === 'chat' && (
                  <button onClick={() => setView('home')} className="p-1 -ml-1 hover:bg-slate-800 rounded-lg transition-colors">
                    <ChevronLeft size={20} />
                  </button>
                )}
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-lg">道</div>
                <div>
                  <h3 className="text-sm font-bold leading-none">Michi</h3>
                  <span className="text-[10px] text-slate-400 mt-1 block">Assistant stratégique</span>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                <X size={18} />
              </button>
            </div>

            {/* --- BODY --- */}
            <div className="flex-1 flex flex-col overflow-hidden relative bg-white">
              <AnimatePresence mode="wait">
                {view === 'home' ? (
                  <motion.div 
                    key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex-1 overflow-y-auto p-5 space-y-6"
                  >
                    {/* Welcome Card */}
                    <div className="bg-slate-50 p-5 rounded-lg border border-slate-100 mb-4">
                      <h4 className="text-slate-900 font-bold text-base mb-1">Bonjour ! 👋</h4>
                      <p className="text-slate-500 text-xs leading-relaxed mb-4">Bienvenue dans l'assistant stratégique Michi.</p>
                      <button 
                        onClick={startNewChat}
                        className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-bold text-sm flex items-center justify-center gap-2 hover:bg-indigo-700 transition-colors shadow-md"
                      >
                        Nouvelle discussion <Plus size={16} />
                      </button>
                    </div>

                    {/* Recent Chats */}
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[11px] font-bold text-slate-400">Conversations récentes</span>
                        <History size={14} className="text-slate-300" />
                      </div>
                      <div className="space-y-3">
                        {sessions.length === 0 ? (
                          <div className="text-center py-6 border-2 border-dashed border-slate-100 rounded-lg text-slate-400 text-xs">
                            Aucun historique pour le moment
                          </div>
                        ) : (
                          sessions.slice(0, 4).map((s) => {
                            const date = new Date(s.updatedAt);
                            const now = new Date();
                            const isToday = date.toDateString() === now.toDateString();
                            const dateStr = isToday 
                              ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                              : date.toLocaleDateString([], { day: 'numeric', month: 'short' });

                            return (
                              <div key={s.sessionId} className="flex items-center gap-2 group">
                                <button 
                                  onClick={() => handleSessionClick(s.sessionId)}
                                  className="flex-1 flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-left"
                                >
                                  <div className="w-8 h-8 bg-slate-100 rounded flex items-center justify-center text-slate-400 shrink-0">
                                    <MessageSquare size={14} />
                                  </div>
                                  <div className="flex-1 overflow-hidden">
                                    <div className="flex justify-between items-center mb-0.5">
                                      <span className="text-[11px] font-bold text-slate-800 truncate pr-2">
                                        {s.lastMessage || "Nouvelle discussion"}
                                      </span>
                                      <span className="text-[9px] text-slate-400 whitespace-nowrap">{dateStr}</span>
                                    </div>
                                    <div className="text-[9px] text-slate-400 uppercase tracking-tighter opacity-60">
                                      ID: {s.sessionId.slice(0, 8)}
                                    </div>
                                  </div>
                                  <ArrowRight size={14} className="text-slate-300" />
                                </button>
                                <button 
                                  onClick={() => deleteSession(s.sessionId)}
                                  className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                  title="Supprimer"
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex-1 flex flex-col overflow-hidden"
                  >
                    <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50">
                      {messages.length === 0 && (
                        <div className="space-y-6 py-4">
                          <div className="text-center">
                            <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-inner">
                              <Sparkles size={24} />
                            </div>
                            <h4 className="text-slate-900 font-bold text-sm">Comment puis-je vous aider ?</h4>
                            <p className="text-slate-400 text-[10px] mt-1">Choisissez une suggestion ou tapez votre question.</p>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3">
                            {SUGGESTIONS.map((s, i) => (
                              <button
                                key={i}
                                onClick={() => sendMessage(s.prompt)}
                                className="flex flex-col items-start p-3 bg-white border border-slate-200 rounded-xl hover:border-indigo-400 hover:shadow-md transition-all text-left group"
                              >
                                <span className="text-xl mb-2 group-hover:scale-110 transition-transform">{s.icon}</span>
                                <span className="text-[11px] font-bold text-slate-700 leading-tight mb-1">{s.label}</span>
                                <span className="text-[9px] text-slate-400 line-clamp-2">{s.prompt}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {messages.map((msg, i) => (
                        <div key={i} className={`flex items-start gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${msg.role === 'user' ? 'bg-indigo-50 border-indigo-100 text-indigo-600' : 'bg-slate-900 border-slate-800 text-white'}`}>
                            {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
                          </div>
                          <div className="flex flex-col gap-1 max-w-[85%] group">
                            <div className={`px-3 py-2 rounded-lg text-[12.5px] leading-relaxed shadow-sm prose prose-sm max-w-none ${
                              msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none'
                            }`}>
                              <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
                                table: ({children}) => <div className="overflow-x-auto my-2"><table className="min-w-full border border-slate-200 text-[11px] bg-white">{children}</table></div>,
                                th: ({children}) => <th className="border border-slate-200 bg-slate-50 px-2 py-1 font-bold text-left">{children}</th>,
                                td: ({children}) => <td className="border border-slate-200 px-2 py-1">{children}</td>,
                                a: ({href, children}) => <a href={href} className="text-indigo-600 font-bold underline hover:text-indigo-800">{children}</a>
                              }}>
                                {msg.content}
                              </ReactMarkdown>
                            </div>
                            {msg.role === 'user' && !isLoading && (
                              <button onClick={() => startEdit(i, msg.content)} className="self-end px-2 py-1 text-slate-400 hover:text-indigo-600 text-[9px] font-bold uppercase tracking-widest">
                                Éditer
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                      {isLoading && (
                        <div className="flex items-center gap-2 text-indigo-600 text-[10px] font-bold bg-white px-3 py-1.5 rounded-lg border border-slate-100 shadow-sm animate-pulse">
                          <RotateCcw size={12} className="animate-spin" /> Analyse en cours...
                        </div>
                      )}

                      {!isLoading && suggestedActions.length > 0 && (
                        <div className="flex flex-wrap gap-2 py-2">
                          {suggestedActions.map((action, idx) => (
                            <button
                              key={idx}
                              onClick={() => sendMessage(action)}
                              className="px-3 py-1.5 bg-white border border-indigo-100 text-indigo-600 rounded-full text-[10px] font-bold hover:bg-indigo-50 transition-colors shadow-sm"
                            >
                              {action}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="p-3 bg-white border-t border-slate-100 shrink-0 relative">
                      {/* Interactive Suggestions Overlay */}
                      <AnimatePresence>
                        {filteredQueries.length > 0 && (
                          <motion.div 
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            className="absolute bottom-full left-0 right-0 mb-2 mx-3 bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden z-20"
                          >
                            <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-100 flex items-center gap-2">
                              <Sparkles size={10} className="text-indigo-500" />
                              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Suggestions de saisie</span>
                            </div>
                            <div className="max-h-32 overflow-y-auto">
                              {filteredQueries.map((q, i) => (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={() => {
                                    setInput(q);
                                    // Optionnel: focus l'input après sélection
                                  }}
                                  className="w-full px-3 py-2 text-left text-xs text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors border-b border-slate-50 last:border-0"
                                >
                                  {q}
                                </button>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      <form onSubmit={handleSubmit} className={`relative flex flex-col bg-slate-50 rounded-lg border transition-all ${editingIndex !== null ? 'border-orange-300' : 'border-slate-200 focus-within:border-indigo-500'}`}>
                        {editingIndex !== null && (
                          <div className="px-3 py-1 bg-orange-100 text-[9px] font-bold text-orange-700 flex justify-between items-center border-b border-orange-200 rounded-t-lg uppercase">
                            <span>Mode édition</span>
                            <button onClick={() => { setEditingIndex(null); setInput(''); }}><X size={10} /></button>
                          </div>
                        )}
                        <div className="flex items-center p-1">
                          <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Écrivez ici..."
                            className="flex-1 bg-transparent px-3 py-2 text-[12.5px] outline-none text-slate-700 placeholder:text-slate-400"
                          />
                          <button 
                            type="submit" 
                            disabled={!input.trim() || isLoading}
                            className={`w-8 h-8 flex items-center justify-center rounded-lg transition-all ${editingIndex !== null ? 'bg-orange-500 text-white' : 'bg-indigo-600 text-white'} disabled:opacity-30`}
                          >
                            {editingIndex !== null ? <Check size={16} /> : <Send size={16} />}
                          </button>
                        </div>
                      </form>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`relative w-14 h-14 rounded-lg flex items-center justify-center shadow-lg transition-all duration-300 ${isOpen ? 'bg-slate-900' : 'bg-indigo-600'}`}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div key="close" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <X className="text-white" size={22} />
            </motion.div>
          ) : (
            <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-white font-bold text-2xl">
              道
            </motion.div>
          )}
        </AnimatePresence>
        {!isOpen && <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 border-4 border-white rounded-full shadow-sm" />}
      </motion.button>
    </div>
  );
};
