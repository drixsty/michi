'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, X, MessageSquare, Sparkles, Bot, User, Plus, History, Trash2, Edit2, Check, RotateCcw, ChevronLeft, ArrowRight, Settings,
  Minus, Maximize2, CornerDownLeft, Database, ChevronDown, Paperclip, ArrowUp, MoreHorizontal, ChevronRight, ThumbsUp, ThumbsDown, Copy,
  Minimize2, Search, Upload, AlertCircle, FileText, Tag, ExternalLink
} from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';

// --- Internal Components ---
const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-slate-100 rounded-lg ${className}`} />
);

const TypedText = ({ text, onComplete }: { text: string, onComplete?: () => void }) => {
  const [displayedText, setDisplayedText] = useState("");
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (index < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + text[index]);
        setIndex(prev => prev + 1);
      }, 15);
      return () => clearTimeout(timeout);
    } else {
      const timer = setTimeout(() => {
        onComplete?.();
      }, 300); // Small buffer to ensure user sees the end
      return () => clearTimeout(timer);
    }
  }, [index, text, onComplete]);

  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayedText}</ReactMarkdown>;
};

// --- Main Hook ---
const useAssistant = (endpoint: string = "http://localhost:8001/graphql") => {
  const [messages, setMessages] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isNewChatMode, setIsNewChatMode] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Load sessionId from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('michi_assistant_session_id');
      if (saved) setSessionId(saved);
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    const query = `query { listSessions { sessionId updatedAt title lastMessage } }`;
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ query })
      });
      const resJson = await response.json();
      if (resJson.data?.listSessions) setSessions(resJson.data.listSessions);
    } catch (e) { console.error("Sessions fetch error", e); }
  }, [endpoint]);

  const loadSession = useCallback(async (sid: string) => {
    setIsLoading(true);
    const query = `query { getSession(sessionId: "${sid}") { messages { role content timestamp } } }`;
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ query })
      });
      const resJson = await response.json();
      if (resJson.errors) {
        console.error("GraphQL Errors in loadSession:", resJson.errors);
      }

      if (resJson.data?.getSession) {
        setMessages(resJson.data.getSession.messages || []);
      } else {
        console.warn("Session not found or empty response for sid:", sid);
        // We don't clear immediately to allow retry or debugging
      }
    } catch (e) { 
      console.error("Network or parsing error in loadSession", e);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint]);

  const deleteSession = async (sid: string) => {
    const query = `mutation { deleteSession(sessionId: "${sid}") }`;
    try {
      setSessions(prev => prev.filter(s => s.sessionId !== sid));
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ query })
      });
      fetchSessions();
      if (sessionId === sid) {
        setSessionId(null);
        localStorage.removeItem('michi_assistant_session_id');
        setMessages([]);
      }
    } catch (e) { console.error("Delete error", e); fetchSessions(); }
  };

  const renameSession = async (sid: string, newTitle: string) => {
    if (!newTitle.trim()) return;
    const query = `mutation { updateSessionTitle(sessionId: "${sid}", title: "${newTitle}") }`;
    try {
      setSessions((prev: any[]) => prev.map((s: any) => s.sessionId === sid ? { ...s, title: newTitle } : s));
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ query })
      });
      const resJson = await response.json();
      console.log("Rename response:", resJson);
      if (resJson.errors) throw new Error("Rename error: " + JSON.stringify(resJson.errors));
      return true;
    } catch (e) { 
      console.error("Rename failed", e);
      fetchSessions();
      return false;
    }
  };

  const sendMessage = useCallback(async (content: string, files: File[] = []) => {
    setIsLoading(true);
    const userMsg = { 
      id: `u-${Date.now()}`, 
      role: 'user', 
      content, 
      files: files.map(f => ({ name: f.name, size: f.size })),
      timestamp: new Date().toISOString() 
    };
    setMessages(prev => [...prev, userMsg]);

    // Local Mock for Demo Chart
    if (content.includes("démo de graphique")) {
      setTimeout(() => {
        const reply = "Bien sûr ! Voici une analyse prévisionnelle de vos stocks pour les 6 prochains mois :\n\n```chart\n{\n  \"type\": \"line\",\n  \"title\": \"Prévisions de Stock - Produit Alpha\",\n  \"data\": [\n    {\"name\": \"Jan\", \"value\": 400},\n    {\"name\": \"Fév\", \"value\": 350},\n    {\"name\": \"Mar\", \"value\": 500},\n    {\"name\": \"Avr\", \"value\": 280},\n    {\"name\": \"Mai\", \"value\": 590},\n    {\"name\": \"Juin\", \"value\": 420}\n  ]\n}\n```\n\nOn observe une forte remontée prévue en Mai suite au réapprovisionnement programmé.";
        setMessages(prev => [...prev, { id: `a-${Date.now()}`, role: 'assistant', content: reply }]);
        setIsLoading(false);
      }, 1000);
      return;
    }

    const sessionIdPart = sessionId ? `"${sessionId}"` : "null";
    const query = `mutation { sendMessage(content: "${content}", sessionId: ${sessionIdPart}) { sessionId reply } }`;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ query })
      });
      const resJson = await response.json();
      if (resJson.data?.sendMessage) {
        const result = resJson.data.sendMessage;
        setMessages(prev => [...prev, { id: `a-${Date.now()}`, role: 'assistant', content: result.reply, isNew: true }]);
        if (!sessionId) {
          setSessionId(result.sessionId);
          localStorage.setItem('michi_assistant_session_id', result.sessionId);
          fetchSessions();
        }
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Erreur de connexion au serveur." }]);
    } finally { setIsLoading(false); }
  }, [endpoint, sessionId, fetchSessions]);

  return { 
    messages, sendMessage, sessions, setSessions, fetchSessions, loadSession, deleteSession, renameSession,
    isOpen, setIsOpen, isLoading, sessionId, setSessionId, setMessages,
    isNewChatMode, setIsNewChatMode,
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
  { icon: '✨', label: "Démo Graphique", prompt: "Montre-moi une démo de graphique d'analyse." },
];

export const AssistantMascot = () => {
  const pathname = usePathname();
  const { 
    messages, sendMessage, sessions, setSessions, fetchSessions, loadSession, deleteSession, renameSession,
    isOpen, setIsOpen, isLoading, sessionId, setSessionId, setMessages,
    isNewChatMode, setIsNewChatMode, suggestedActions
  } = useAssistant();
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [ratedMessages, setRatedMessages] = useState<Record<string, 'up' | 'down'>>({});
  const [finishedTypingIds, setFinishedTypingIds] = useState<Set<string>>(new Set());

  // Handle auto-scroll or other effects when messages change
  useEffect(() => {
    // ONLY mark old messages as finished. New messages (isNew: true) 
    // must be added to this set ONLY via the TypedText onComplete callback.
    if (messages.length > 0) {
      setFinishedTypingIds(prev => {
        const next = new Set(prev);
        messages.forEach(m => { 
          if (m.id && !m.isNew) next.add(m.id); 
        });
        return next;
      });
    }
  }, [messages.length]); 

  // Persistence for ratings
  useEffect(() => {
    const saved = localStorage.getItem('michi_rated_messages');
    if (saved) setRatedMessages(JSON.parse(saved));
  }, []);


  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(id);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleRate = (id: string, rate: 'up' | 'down') => {
    const next = { ...ratedMessages, [id]: rate };
    setRatedMessages(next);
    localStorage.setItem('michi_rated_messages', JSON.stringify(next));
  };
  
  const getContextualSuggestions = () => {
    const base = [...SUGGESTIONS];
    if (pathname?.includes('inventory')) {
      base.unshift({ icon: '📦', label: "Stock par entrepôt", prompt: "Donne-moi le détail des stocks par entrepôt." });
    }
    if (pathname?.includes('suppliers')) {
      base.unshift({ icon: '🏭', label: "Performance fournisseurs", prompt: "Analyse la performance de mes fournisseurs." });
    }
    if (pathname?.includes('forecasting')) {
      base.unshift({ icon: '🔮', label: "Risques de rupture", prompt: "Quels sont les produits à risque de rupture sous 15 jours ?" });
    }
    return base.slice(0, 5);
  };
  const dynamicSuggestions = getContextualSuggestions();
  const [view, setView] = useState<'home' | 'chat' | 'history'>('home');
  const [isEditorEmpty, setIsEditorEmpty] = useState(true);
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionSuggestions, setMentionSuggestions] = useState<any[]>([]);
  const [isMentionLoading, setIsMentionLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const searchTimerRef = useRef<any>(null);
  const [activeMentionIndex, setActiveMentionIndex] = useState(0);
  const [isSessionsLoading, setIsSessionsLoading] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null);
  const [renamingTitle, setRenamingTitle] = useState("");
  const [historySearch, setHistorySearch] = useState("");
  const [activeMentions, setActiveMentions] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);

  const filteredSessions = sessions.filter(s => 
    s.title?.toLowerCase().includes(historySearch.toLowerCase()) || 
    s.lastMessage?.toLowerCase().includes(historySearch.toLowerCase())
  );

  // Wrapper to track loading specifically for sessions list
  const handleFetchSessions = useCallback(async () => {
    setIsSessionsLoading(true);
    await fetchSessions();
    setIsSessionsLoading(false);
  }, [fetchSessions]);

  const handleRename = async (sid: string, newTitle: string) => {
    const success = await renameSession(sid, newTitle);
    if (success) {
      setRenamingSessionId(null);
    }
  };

  const handleRenameConfirm = (sid: string) => {
    handleRename(sid, renamingTitle);
  };


  // Global keyboard shortcuts
  useEffect(() => {
    const handleGlobalKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (mentionQuery !== null) setMentionQuery(null);
        else setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleGlobalKey);
    return () => window.removeEventListener('keydown', handleGlobalKey);
  }, [mentionQuery, setIsOpen]);

  // Fetch sessions only once when opening or after a mutation
  useEffect(() => {
    if (isOpen) {
      handleFetchSessions();
    }
  }, [isOpen, handleFetchSessions]);

  // Load specific session messages only if needed
  useEffect(() => {
    if (isOpen && sessionId && messages.length === 0) {
      loadSession(sessionId);
      setView('chat');
    }
  }, [isOpen, sessionId, loadSession, messages.length]); 

  // Ultimate auto-scroll logic using ResizeObserver to catch ALL layout changes
  useEffect(() => {
    if (view === 'chat' && scrollRef.current) {
      const element = scrollRef.current;
      
      const scrollToBottom = () => {
        element.scrollTop = element.scrollHeight;
      };

      // Initial scroll
      scrollToBottom();

      // Observe size changes (images loading, markdown rendering, etc.)
      const resizeObserver = new ResizeObserver(() => {
        scrollToBottom();
      });

      resizeObserver.observe(element);
      
      // Also scroll when dependencies change as a backup
      scrollToBottom();
      const timer = setTimeout(scrollToBottom, 100);

      return () => {
        resizeObserver.disconnect();
        clearTimeout(timer);
      };
    }
  }, [view, messages.length, isLoading]);

  const startNewChat = () => {
    setSessionId(null);
    localStorage.removeItem('michi_assistant_session_id');
    setMessages([]);
    setIsNewChatMode(true);
    setView('chat');
  };

  const handleSessionClick = (sid: string) => {
    setRenamingSessionId(null);
    setMessages([]); // Clear current chat to show loading
    setSessionId(sid);
    localStorage.setItem('michi_assistant_session_id', sid);
    loadSession(sid);
    setIsNewChatMode(false);
    setView('chat');
  };


  const searchMentions = async (query: string) => {
    if (query.length < 2) {
      setMentionSuggestions([]);
      return;
    }
    setIsMentionLoading(true);
    const mainApi = "http://localhost:8000/graphql";
    // Search products, suppliers, and sources
    const gql = `query { 
      products(title: "${query}") { id title sku }
      suppliers(name: "${query}") { id name }
      sources { id platform }
    }`;
    try {
      const orgId = localStorage.getItem('michi_org_id');
      const response = await fetch(mainApi, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          ...(orgId ? { 'michi-org-id': orgId } : {})
        },
        body: JSON.stringify({ query: gql })
      });
      const resJson = await response.json();
      const results = [];
      if (resJson.data?.products) {
        results.push(...resJson.data.products.slice(0, 3).map((p: any) => ({ id: p.id, title: p.title, subtitle: p.sku, type: 'product', icon: '📦' })));
      }
      if (resJson.data?.suppliers) {
        results.push(...resJson.data.suppliers.slice(0, 3).map((s: any) => ({ id: s.id, title: s.name, subtitle: 'Fournisseur', type: 'supplier', icon: '🏭' })));
      }
      if (resJson.data?.sources) {
        results.push(...resJson.data.sources.filter((s: any) => s.platform.toLowerCase().includes(query.toLowerCase())).slice(0, 2).map((s: any) => ({ id: s.id, title: s.platform, subtitle: 'Source de données', type: 'source', icon: '🔌' })));
      }

      // Final fallback for demo/empty DB (search in titles)
      if (results.length === 0 && query.length >= 2) {
        const demoData = [
          { id: 'demo-1', title: 'Huile Essentielle Lavande', subtitle: 'SKU-LAV-01', type: 'product', icon: '📦' },
          { id: 'demo-2', title: 'Sérum Anti-Âge Premium', subtitle: 'SKU-SRM-99', type: 'product', icon: '📦' }
        ];
        results.push(...demoData.filter(d => d.title.toLowerCase().includes(query.toLowerCase())));
      }

      setMentionSuggestions(results);
    } catch (e) { console.error("Mention search error", e); }
    finally { setIsMentionLoading(false); }
  };

  const insertMention = (item: any) => {
    const editor = editorRef.current;
    if (!editor) return;

    // Create the badge element
    const routeType = item.type === 'product' ? 'inventory' : item.type === 'supplier' ? 'suppliers' : 'settings';
    const path = `/dashboard/${routeType}/${item.id}`;
    
    // Use an emoji or a simple SVG for the tag icon since we're in raw HTML
    const badgeHtml = `
      <span 
        contenteditable="false" 
        class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-indigo-50 text-indigo-600 rounded-md font-bold text-[12px] mx-0.5 select-none border border-indigo-100/50"
        data-path="${path}"
        data-label="${item.title}"
      >
        <span style="font-size: 10px;">🏷️</span> ${item.title}
      </span>&nbsp;
    `;

    // Find the range to replace (the word starting with @)
    const selection = window.getSelection();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    
    // Move back to find the start of the word (the @)
    const node = range.startContainer;
    const offset = range.startOffset;
    const text = node.textContent || "";
    
    let start = offset - 1;
    while (start >= 0 && text[start] !== '@' && !/\s/.test(text[start])) {
      start--;
    }
    
    if (start >= 0 && text[start] === '@') {
      range.setStart(node, start);
      range.setEnd(node, offset);
      range.deleteContents();
      
      const el = document.createElement("div");
      el.innerHTML = badgeHtml;
      const frag = document.createDocumentFragment();
      let node_to_insert, last_node;
      while ((node_to_insert = el.firstChild)) {
        last_node = frag.appendChild(node_to_insert);
      }
      range.insertNode(frag);
      
      // Move cursor after the inserted content
      if (last_node) {
        range.setStartAfter(last_node);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }

    setMentionQuery(null);
    setMentionSuggestions([]);
    
    // Trigger input update
    handleEditorInput();
  };

  const handleEditorInput = () => {
    const editor = editorRef.current;
    if (!editor) return;
    
    setIsEditorEmpty(!editor.innerText.trim() && attachedFiles.length === 0);
    
    // Extract plain text for mention detection
    const selection = window.getSelection();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    const textBeforeCursor = range.startContainer.textContent?.substring(0, range.startOffset) || "";
    
    const words = textBeforeCursor.split(/\s/);
    const lastWord = words[words.length - 1];

    if (lastWord.startsWith('@')) {
      const query = lastWord.substring(1);
      setMentionQuery(query);
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
      searchTimerRef.current = setTimeout(() => searchMentions(query), 300);
      setActiveMentionIndex(0);
    } else {
      setMentionQuery(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const editor = editorRef.current;
    if (!editor) return;

    // Convert HTML to markdown with links
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = editor.innerHTML;
    
    // Replace badges with markdown links
    const badges = tempDiv.querySelectorAll('span[data-path]');
    badges.forEach(b => {
      const label = b.getAttribute('data-label');
      const path = b.getAttribute('data-path');
      b.replaceWith(`[${label}](${path})`);
    });

    const finalContent = tempDiv.innerText.trim();

    if ((finalContent || attachedFiles.length > 0) && !isLoading) {
      sendMessage(finalContent, attachedFiles);
      editor.innerHTML = "";
      setIsEditorEmpty(true);
      setAttachedFiles([]);
      setFileError(null);
      setIsNewChatMode(false);
    }
  };

  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const MAX_FILES = 5;
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setFileError(null);

    const incomingFiles = Array.from(e.dataTransfer.files);
    const validFiles: File[] = [];
    let error = "";

    if (attachedFiles.length + incomingFiles.length > MAX_FILES) {
      error = `Limite de ${MAX_FILES} fichiers atteinte.`;
    }

    incomingFiles.forEach(f => {
      if (f.size > MAX_FILE_SIZE) {
        error = "Certains fichiers dépassent 10 Mo.";
      } else if (validFiles.length + attachedFiles.length < MAX_FILES) {
        validFiles.push(f);
      }
    });

    if (error) {
      setFileError(error);
      setTimeout(() => setFileError(null), 4000);
    }

    if (validFiles.length > 0) {
      setAttachedFiles(prev => [...prev, ...validFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const incomingFiles = Array.from(e.target.files);
      const validFiles: File[] = [];
      let error = "";

      if (attachedFiles.length + incomingFiles.length > MAX_FILES) {
        error = `Limite de ${MAX_FILES} fichiers atteinte.`;
      }

      incomingFiles.forEach(f => {
        if (f.size > MAX_FILE_SIZE) {
          error = "Certains fichiers dépassent 10 Mo.";
        } else if (validFiles.length + attachedFiles.length < MAX_FILES) {
          validFiles.push(f);
        }
      });

      if (error) {
        setFileError(error);
        setTimeout(() => setFileError(null), 4000);
      }

      if (validFiles.length > 0) {
        setAttachedFiles(prev => [...prev, ...validFiles]);
      }
      e.target.value = '';
    }
  };

  return (
    <div 
      className="fixed bottom-5 right-5 z-[10000] font-sans flex flex-col items-end"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <style jsx global>{`
        .assistant-scrollbar::-webkit-scrollbar {
          width: 10px;
        }
        .assistant-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .assistant-scrollbar::-webkit-scrollbar-thumb {
          background-color: #e2e8f0;
          border-radius: 20px;
          border: 3px solid transparent;
          background-clip: padding-box;
          transition: all 0.3s ease;
        }
        .assistant-scrollbar:hover::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
        }
        .assistant-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: #6366f1;
          border: 2px solid transparent;
        }
        [contenteditable]:empty:before {
          content: attr(data-placeholder);
          color: #94a3b8;
          pointer-events: none;
          display: block;
        }
      `}</style>
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ 
              opacity: 0, 
              y: 0, 
              width: isExpanded ? '900px' : '450px',
              height: isExpanded ? '750px' : '600px'
            }}
            animate={{ 
              opacity: 1, 
              y: 0, 
              width: isExpanded ? '900px' : '450px',
              height: isExpanded ? '750px' : '600px',
            }}
            exit={{ opacity: 0, y: 0 }}
            className="absolute bottom-14 right-0 flex flex-col max-w-[calc(100vw-40px)] max-h-[calc(100vh-100px)] bg-white rounded-2xl shadow-[0_0_50px_-12px_rgba(0,0,0,0.25)] border border-slate-200 overflow-hidden font-sans z-[10000]"
          >
            {/* Header */}
            <div className="flex items-center h-14 px-4 border-b border-slate-100 bg-white shrink-0">
              {/* Left: Back/Logo */}
              <div className="shrink-0 mr-3">
                {view !== 'home' ? (
                  <button 
                    onClick={() => setView('home')}
                    className="p-1.5 -ml-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition-all"
                  >
                    <ChevronLeft size={20} />
                  </button>
                ) : (
                  <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                    <div className="text-sm font-serif text-white">道</div>
                  </div>
                )}
              </div>

              {/* Center: Title (Flexible) */}
              <div className="flex-1 min-w-0 overflow-hidden">
                <div className="flex flex-col">
                  <span className="text-[13.5px] font-bold text-slate-900 leading-none truncate pr-4">
                    {view === 'home' && "Assistant Michi"}
                    {view === 'history' && "Rechercher une discussion"}
                    {view === 'chat' && (sessionId && !isNewChatMode ? (sessions.find(s => s.sessionId === sessionId)?.title || "Discussion michi") : "Nouveau chat")}
                  </span>
                  {view === 'chat' && <span className="text-[10px] text-slate-400 font-medium italic mt-0.5">Conversation active</span>}
                </div>
              </div>

              {/* Right: Actions (Fixed) */}
              <div className="flex items-center gap-0.5 shrink-0 ml-2">
                <button onClick={startNewChat} title="Nouvelle discussion" className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all">
                  <Plus size={18} />
                </button>
                {view !== 'history' && (
                  <button onClick={() => setView('history')} title="Historique" className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all">
                    <History size={18} />
                  </button>
                )}
                <button onClick={() => setIsExpanded(!isExpanded)} title={isExpanded ? "Réduire" : "Agrandir"} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all hidden sm:flex">
                  {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                </button>
                <button onClick={() => setIsOpen(false)} title="Fermer" className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 flex flex-col overflow-hidden relative bg-white">
              <AnimatePresence mode="wait">
                {view === 'home' && (
                  <motion.div 
                    key="home"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-1 flex flex-col overflow-y-auto assistant-scrollbar px-6 pr-4 py-10 space-y-8"
                  >
                    <div className="flex flex-col items-center text-center space-y-4 py-4">
                      <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-100">
                        <div className="text-3xl font-serif text-white">道</div>
                      </div>
                      <div className="space-y-4">
                        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Assistant Michi</h2>
                        <p className="text-slate-500 text-sm max-w-[280px]">Optimisez vos stocks et vos prévisions en un clin d'œil.</p>
                      </div>
                      <button onClick={startNewChat} className="w-full max-w-[200px] flex items-center justify-center gap-2 bg-indigo-600 text-white py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all">
                        <Plus size={18} /> Nouvelle discussion
                      </button>
                      <div className="flex flex-wrap justify-center gap-2 max-w-[340px]">
                        {dynamicSuggestions.map((s, i) => (
                          <button key={i} onClick={() => { startNewChat(); sendMessage(s.prompt); }} className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-[13px] font-medium text-slate-700 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50/30 transition-all shadow-sm">
                            <span>{s.icon}</span> {s.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-400 tracking-wide">Discussions récentes</span>
                        <button onClick={() => setView('history')} className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 tracking-wide flex items-center gap-1">Voir tout <ChevronRight size={10} /></button>
                      </div>
                      <div className="space-y-1">
                        {isSessionsLoading ? (
                          [1, 2, 3].map(i => (
                            <div key={i} className="flex items-center gap-3 p-3">
                              <Skeleton className="w-8 h-8 shrink-0" />
                              <div className="flex-1 space-y-2">
                                <Skeleton className="h-4 w-3/4" />
                                <Skeleton className="h-3 w-1/2" />
                              </div>
                            </div>
                          ))
                        ) : (
                          sessions.slice(0, 4).map(s => (
                            <button key={s.sessionId} onClick={() => handleSessionClick(s.sessionId)} className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 group text-left transition-all border border-transparent hover:border-slate-100">
                              <div className="flex items-center gap-3 overflow-hidden">
                                <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center group-hover:bg-white transition-colors">
                                  <MessageSquare size={14} className="text-slate-400 group-hover:text-indigo-600" />
                                </div>
                                <div className="flex flex-col min-w-0">
                                  <span className="text-[13px] text-slate-700 font-medium truncate group-hover:text-slate-900 max-w-[200px]">{s.title || "Discussion Michi"}</span>
                                  <span className="text-[10px] text-slate-400 truncate max-w-[220px]">{s.lastMessage || "Ouvrir la conversation"}</span>
                                </div>
                              </div>
                              <ChevronRight size={14} className="text-slate-200 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
                            </button>
                          ))
                        )}
                        {!isSessionsLoading && sessions.length === 0 && (
                          <div className="flex flex-col items-center py-8 text-slate-400 space-y-2">
                            <Bot size={24} className="opacity-10" />
                            <p className="text-[11px] italic">Aucune discussion récente.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}

                {view === 'history' && (
                  <motion.div 
                    key="history"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-1 flex flex-col overflow-hidden bg-slate-50/30"
                  >
                    {/* Minimalist Search Bar */}
                    <div className="px-4 py-3 bg-white border-b border-slate-100 shadow-sm">
                      <div className="relative group">
                        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                        <input 
                          type="text"
                          placeholder="Rechercher une discussion..."
                          className="w-full h-11 bg-white border border-slate-200 rounded-md pl-11 pr-4 text-[13px] font-medium text-slate-600 placeholder:text-slate-400 transition-all focus:outline-none focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500/20"
                          value={historySearch}
                          onChange={e => setHistorySearch(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="flex-1 overflow-y-auto assistant-scrollbar px-2 py-4 space-y-6">
                      {isSessionsLoading ? (
                        <div className="space-y-1">
                          {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                            <div key={i} className="flex items-center gap-3 p-2">
                              <Skeleton className="w-8 h-8 shrink-0" />
                              <div className="flex-1 space-y-1">
                                <Skeleton className="h-3 w-1/3" />
                                <Skeleton className="h-2 w-full" />
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : filteredSessions.length > 0 ? (
                        (() => {
                          const groups: Record<string, any[]> = { 'Aujourd\'hui': [], 'Hier': [], 'Plus ancien': [] };
                          const today = new Date().toDateString();
                          const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
                          const yesterdayStr = yesterday.toDateString();

                          filteredSessions.forEach(s => {
                            const date = new Date(s.updatedAt).toDateString();
                            if (date === today) groups['Aujourd\'hui'].push(s);
                            else if (date === yesterdayStr) groups['Hier'].push(s);
                            else groups['Plus ancien'].push(s);
                          });

                          return Object.entries(groups).map(([label, items]) => items.length > 0 && (
                            <motion.div layout="position" key={label} className="space-y-1">
                              <motion.h4 layout="position" className="px-3 text-[9px] font-bold text-slate-300 tracking-widest mb-1">{label}</motion.h4>
                                <div className={`grid ${isExpanded ? 'grid-cols-2 gap-x-3' : 'grid-cols-1'}`}>
                                  <AnimatePresence initial={false}>
                                    {items.map(s => (
                                      <motion.div 
                                        key={s.sessionId} 
                                      initial={{ opacity: 0, y: 5 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      exit={{ opacity: 0, scale: 0.95 }}
                                      className={`group relative flex items-center gap-3 p-2 px-3 rounded-lg transition-colors border-b border-transparent last:border-none ${renamingSessionId === s.sessionId ? 'bg-indigo-50/50 cursor-default' : 'hover:bg-slate-50 cursor-pointer'}`}
                                      onClick={() => renamingSessionId !== s.sessionId && handleSessionClick(s.sessionId)}
                                    >
                                      <div className="w-7 h-7 rounded-lg bg-slate-50 flex items-center justify-center text-slate-400 shrink-0 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-all">
                                        <MessageSquare size={14} />
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <AnimatePresence mode="wait" initial={false}>
                                          {renamingSessionId === s.sessionId ? (
                                            <motion.div 
                                              key="edit"
                                              initial={{ opacity: 0, scale: 0.98 }}
                                              animate={{ opacity: 1, scale: 1 }}
                                              exit={{ opacity: 0, scale: 0.98 }}
                                              className="w-full" 
                                              onClick={e => e.stopPropagation()}
                                            >
                                              <div className="relative w-full">
                                                <input 
                                                  autoFocus
                                                  type="text"
                                                  maxLength={50}
                                                  value={renamingTitle}
                                                  onChange={e => setRenamingTitle(e.target.value)}
                                                  className="w-full h-10 bg-white border border-slate-200 rounded-md pl-3 pr-12 text-[13px] font-medium text-slate-900 transition-all focus:outline-none focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500/20"
                                                  placeholder="Nom de la discussion..."
                                                  onKeyDown={e => {
                                                    if (e.key === 'Enter') handleRenameConfirm(s.sessionId);
                                                    if (e.key === 'Escape') setRenamingSessionId(null);
                                                  }}
                                                />
                                                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex flex-col items-end pointer-events-none">
                                                  <span className={`text-[9px] font-bold tabular-nums transition-colors ${renamingTitle.length >= 45 ? 'text-amber-500' : 'text-slate-300'}`}>
                                                    {renamingTitle.length}/50
                                                  </span>
                                                </div>
                                              </div>
                                            </motion.div>
                                          ) : (
                                            <motion.div 
                                              key="view"
                                              initial={{ opacity: 0, x: 10 }}
                                              animate={{ opacity: 1, x: 0 }}
                                              exit={{ opacity: 0, x: -10 }}
                                            >
                                              <div className="flex items-center justify-between gap-2">
                                                <span className="text-[12px] font-semibold text-slate-600 truncate group-hover:text-slate-900 transition-colors max-w-[300px] sm:max-w-[450px]">{s.title || "Discussion Michi"}</span>
                                              </div>
                                              <p className="text-[11px] text-slate-400 truncate mt-0.5 opacity-80 group-hover:opacity-100">
                                                {s.lastMessage || "Ouvrir"}
                                              </p>
                                            </motion.div>
                                          )}
                                        </AnimatePresence>
                                      </div>

                                      {/* Actions logic: Swap Time and Buttons on Hover */}
                                      <div className="relative min-w-[60px] flex justify-end items-center h-full">
                                        <AnimatePresence mode="wait" initial={false}>
                                          {renamingSessionId === s.sessionId ? (
                                            <motion.div 
                                              key="edit-actions"
                                              initial={{ opacity: 0, x: 10 }}
                                              animate={{ opacity: 1, x: 0 }}
                                              exit={{ opacity: 0, x: 10 }}
                                              className="flex items-center gap-1"
                                              onClick={e => e.stopPropagation()}
                                            >
                                              <button 
                                                onClick={() => handleRenameConfirm(s.sessionId)}
                                                className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                                                title="Sauvegarder"
                                              >
                                                <Check size={16} />
                                              </button>
                                              <button 
                                                onClick={() => setRenamingSessionId(null)}
                                                className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-lg transition-all"
                                                title="Annuler"
                                              >
                                                <X size={16} />
                                              </button>
                                            </motion.div>
                                          ) : (
                                            <motion.div
                                              key="time-actions"
                                              className="relative flex items-center justify-end"
                                            >
                                              {/* Time (Visible by default) */}
                                              <motion.span 
                                                className="text-[9px] font-medium text-slate-300 group-hover:opacity-0 transition-opacity"
                                              >
                                                {new Date(s.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                              </motion.span>
                                              
                                              {/* Actions (Visible on Hover) */}
                                              <motion.div 
                                                className="absolute inset-0 flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none group-hover:pointer-events-auto"
                                                onClick={e => e.stopPropagation()}
                                              >
                                                <button 
                                                  onClick={() => { setRenamingSessionId(s.sessionId); setRenamingTitle(s.title || ""); }} 
                                                  className="p-1 text-slate-300 hover:text-indigo-600 hover:bg-white rounded transition-all shadow-sm bg-slate-50"
                                                  title="Modifier"
                                                >
                                                  <Edit2 size={12} />
                                                </button>
                                                <button 
                                                  onClick={() => deleteSession(s.sessionId)} 
                                                  className="p-1 text-slate-300 hover:text-red-500 hover:bg-white rounded transition-all shadow-sm bg-slate-50"
                                                  title="Supprimer"
                                                >
                                                  <Trash2 size={12} />
                                                </button>
                                              </motion.div>
                                            </motion.div>
                                          )}
                                        </AnimatePresence>
                                      </div>
                                    </motion.div>
                                  ))}
                                  </AnimatePresence>
                                </div>
                              </motion.div>
                          ));
                        })()
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4 py-20">
                          <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                            <History size={32} className="opacity-20" />
                          </div>
                          <div className="text-center">
                            <p className="text-[13px] font-bold text-slate-600">Aucune discussion trouvée</p>
                            <p className="text-[11px] text-slate-400 mt-1">{historySearch ? "Essayez d'autres mots-clés" : "Commencez une nouvelle discussion !"}</p>
                          </div>
                          {historySearch && (
                            <button onClick={() => setHistorySearch("")} className="text-[11px] font-bold text-indigo-600 hover:underline">Effacer la recherche</button>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}

                {view === 'chat' && (
                  <motion.div 
                    key="chat"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-1 flex flex-col overflow-hidden"
                  >
                    <div ref={scrollRef} className="flex-1 p-6 pr-4 overflow-y-auto assistant-scrollbar space-y-8 pb-10">
                      <AnimatePresence>
                        {isDragging && (
                          <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-indigo-600 z-50 flex flex-col items-center justify-center rounded-2xl"
                          >
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mb-4">
                              <Upload size={32} className="text-white" />
                            </div>
                            <p className="text-white font-bold text-lg">Déposez pour analyser</p>
                            <p className="text-white/70 text-sm mt-1">Images, PDF, Excel...</p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                      {messages.length === 0 && !isLoading && (
                        <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-20">
                          <Sparkles size={40} className="text-indigo-100" />
                          <div className="space-y-1">
                            <p className="text-sm font-semibold text-slate-800">Démarrer la discussion</p>
                            <p className="text-xs text-slate-400">Posez votre première question ci-dessous.</p>
                          </div>
                        </div>
                      )}
                      {messages.map((msg, i) => (
                        <motion.div 
                          key={msg.id || `${msg.role}-${i}`} 
                          initial={{ opacity: 0, y: 10, scale: 0.98 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          transition={{ duration: 0.3, ease: "easeOut" }}
                          className={`flex flex-col w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                        >
                          {msg.role === 'user' ? (
                            <div className="flex flex-col items-end max-w-[85%] space-y-2">
                              {msg.files && msg.files.length > 0 && (
                                <div className="flex flex-wrap gap-2 justify-end">
                                  {msg.files.map((f: any, idx: number) => (
                                    <div key={idx} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-xl text-[11px] font-bold text-slate-600 shadow-sm">
                                      <Paperclip size={10} className="text-slate-400" />
                                      <span className="truncate max-w-[150px]">{f.name}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {msg.content && (
                                <div className="bg-indigo-600 px-4 py-2 rounded-2xl rounded-tr-none text-[13.5px] text-white font-medium shadow-sm">{msg.content}</div>
                              )}
                            </div>
                          ) : (
                            <div className="w-full space-y-3">
                              <div className="flex items-center gap-2 text-[11px] text-slate-400 font-medium">
                                <Bot size={12} className="text-indigo-500" />
                                <span>Assistant Michi</span>
                              </div>
                              <div className="text-[14.5px] leading-relaxed text-slate-800 prose prose-slate prose-sm max-w-none ml-5 prose-p:my-2 prose-headings:text-slate-900 prose-code:text-indigo-600 prose-table:border prose-table:border-slate-100 prose-th:bg-slate-50 prose-th:px-2 prose-td:px-2">
                                {msg.isNew ? (
                                  <TypedText 
                                    text={msg.content} 
                                    onComplete={() => {
                                      if (msg.id) setFinishedTypingIds(prev => new Set(prev).add(msg.id));
                                    }} 
                                  />
                                ) : (
                                  <ReactMarkdown 
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                      a({ children, href, ...props }: any) {
                                        const isInternal = href?.startsWith('/dashboard/');
                                        if (isInternal) {
                                          return (
                                            <Link 
                                              href={href} 
                                              className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-md font-bold text-[12px] no-underline hover:bg-indigo-100 transition-all border border-indigo-100/50"
                                            >
                                              <Tag size={10} className="shrink-0" />
                                              {children}
                                              <ExternalLink size={10} className="shrink-0 opacity-40" />
                                            </Link>
                                          );
                                        }
                                        return <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 underline" {...props}>{children}</a>;
                                      },
                                      code({ inline, className, children, ...props }: any) {
                                        const match = /language-chart/.exec(className || '');
                                        if (!inline && match) {
                                          try {
                                            const config = JSON.parse(String(children));
                                            return (
                                              <div className="my-4 p-4 bg-slate-50 border border-slate-100 rounded-xl">
                                                <div className="text-[11px] font-bold text-slate-400 tracking-wide mb-4 flex items-center gap-2">
                                                  <Database size={12} /> {config.title || "Analyse de données"}
                                                </div>
                                                <div className="h-[200px] w-full">
                                                  <ResponsiveContainer width="100%" height="100%">
                                                    {config.type === 'bar' ? (
                                                      <BarChart data={config.data}>
                                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                                        <XAxis dataKey="name" fontSize={10} axisLine={false} tickLine={false} />
                                                        <YAxis fontSize={10} axisLine={false} tickLine={false} />
                                                        <Tooltip 
                                                          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                                                        />
                                                        <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                                                      </BarChart>
                                                    ) : (
                                                      <LineChart data={config.data}>
                                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                                        <XAxis dataKey="name" fontSize={10} axisLine={false} tickLine={false} />
                                                        <YAxis fontSize={10} axisLine={false} tickLine={false} />
                                                        <Tooltip />
                                                        <Line type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={2} dot={{ fill: '#4f46e5' }} />
                                                      </LineChart>
                                                    )}
                                                  </ResponsiveContainer>
                                                </div>
                                              </div>
                                            );
                                          } catch (e) {
                                            return <code className={className} {...props}>{children}</code>;
                                          }
                                        }
                                        return <code className={className} {...props}>{children}</code>;
                                      }
                                    }}
                                  >
                                    {msg.content}
                                  </ReactMarkdown>
                                )}
                              </div>
                              
                              {((msg.id && finishedTypingIds.has(msg.id)) || !msg.isNew) && (
                                <motion.div 
                                  initial={{ opacity: 0 }} 
                                  animate={{ opacity: 1 }}
                                  className="space-y-4"
                                >
                                  <div className="flex items-center gap-3 ml-5 mt-2">
                                    <div className="flex items-center gap-1">
                                      <button 
                                        onClick={() => handleRate(msg.id || i.toString(), 'up')}
                                        title="Pertinent" 
                                        className={`p-1 rounded-md transition-all ${ratedMessages[msg.id || i.toString()] === 'up' ? 'text-indigo-600 bg-indigo-50' : 'text-slate-300 hover:text-indigo-500 hover:bg-indigo-50'}`}
                                      >
                                        <ThumbsUp size={12} fill={ratedMessages[msg.id || i.toString()] === 'up' ? 'currentColor' : 'none'} />
                                      </button>
                                      <button 
                                        onClick={() => handleRate(msg.id || i.toString(), 'down')}
                                        title="Non pertinent" 
                                        className={`p-1 rounded-md transition-all ${ratedMessages[msg.id || i.toString()] === 'down' ? 'text-red-500 bg-red-50' : 'text-slate-300 hover:text-red-500 hover:bg-red-50'}`}
                                      >
                                        <ThumbsDown size={12} fill={ratedMessages[msg.id || i.toString()] === 'down' ? 'currentColor' : 'none'} />
                                      </button>
                                    </div>
                                    <div className="h-3 w-[1px] bg-slate-100" />
                                    <button 
                                      onClick={() => handleCopy(msg.id || i.toString(), msg.content)}
                                      className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 hover:text-indigo-600 transition-all"
                                    >
                                      {copiedMessageId === (msg.id || i.toString()) ? (
                                        <span className="flex items-center gap-1 text-green-600 animate-in fade-in zoom-in duration-300">
                                          <Check size={10} /> Copié !
                                        </span>
                                      ) : (
                                        <>
                                          <Copy size={10} /> Copier
                                        </>
                                      )}
                                    </button>
                                  </div>
                                  
                                  {/* Suggested Actions for the last assistant message */}
                                  {i === messages.length - 1 && suggestedActions.length > 0 && !isLoading && (
                                    <div className="flex flex-wrap gap-2 ml-5 mt-4">
                                      {suggestedActions.map((action, idx) => (
                                        <button 
                                          key={idx}
                                          onClick={() => sendMessage(action)}
                                          className="px-3 py-1.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-full text-[11px] font-semibold hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
                                        >
                                          {action}
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </motion.div>
                              )}
                            </div>
                          )}
                        </motion.div>
                      ))}
                      {isLoading && (
                        <motion.div 
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="flex items-center gap-2 ml-5 text-indigo-400 text-[11px] font-medium"
                        >
                          <Sparkles size={12} className="animate-pulse" />
                          <span>Michi réfléchit...</span>
                        </motion.div>
                      )}
                    </div>

                    {/* Input Bar inside chat view only */}
                    <div className="p-4 border-t border-slate-50">
                    <div className="relative">
                      {/* Attached Chips (Files & Mentions) */}
                      {(attachedFiles.length > 0 || activeMentions.length > 0) && (
                        <div className="flex flex-wrap gap-2 mb-3 px-1">
                          <AnimatePresence>
                            {attachedFiles.map((file, idx) => (
                              <motion.div 
                                key={`file-${file.name}-${idx}`}
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                className="flex items-center gap-2 bg-slate-50 border border-slate-100 pl-2 pr-1 py-1 rounded-lg group transition-all hover:bg-white hover:border-indigo-100"
                              >
                                <FileText size={12} className="text-indigo-500" />
                                <span className="text-[10px] font-medium text-slate-600 truncate max-w-[120px]">{file.name}</span>
                                <button 
                                  onClick={() => removeFile(idx)}
                                  className="p-1 text-slate-300 hover:text-red-500 rounded-md transition-all"
                                >
                                  <X size={10} />
                                </button>
                              </motion.div>
                            ))}
                            {activeMentions.map((m, idx) => (
                              <motion.div 
                                key={`mention-${m.path}-${idx}`}
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                className="flex items-center gap-2 bg-indigo-50 border border-indigo-100/30 pl-2 pr-1 py-1 rounded-lg group transition-all hover:bg-white hover:border-indigo-100"
                              >
                                <Link 
                                  href={m.path}
                                  className="flex items-center gap-1.5"
                                  title="Voir les détails"
                                >
                                  <Tag size={12} className="text-indigo-500" />
                                  <span className="text-[10px] font-bold text-indigo-600 truncate max-w-[120px]">{m.label}</span>
                                </Link>
                                <button 
                                  onClick={() => setActiveMentions(prev => prev.filter((_, i) => i !== idx))}
                                  className="p-1 text-indigo-300 hover:text-red-500 rounded-md transition-all"
                                >
                                  <X size={10} />
                                </button>
                              </motion.div>
                            ))}
                          </AnimatePresence>
                        </div>
                      )}

                      {/* File Error Message */}
                      <AnimatePresence>
                        {fileError && (
                          <motion.div 
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="mb-2 text-[10px] font-bold text-red-500 flex items-center gap-1.5 px-1"
                          >
                            <AlertCircle size={12} /> {fileError}
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Mention Suggestions UI */}
                      <AnimatePresence>
                        {mentionQuery !== null && (
                          <motion.div 
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.98 }}
                            className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden z-30"
                          >
                            <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-100 flex items-center justify-between">
                              <span className="text-[10px] font-bold text-slate-400 tracking-wide">Suggestions de données</span>
                              {isMentionLoading && <RotateCcw size={10} className="animate-spin text-slate-400" />}
                            </div>
                            <div className="max-h-48 overflow-y-auto p-1">
                              {mentionSuggestions.length > 0 ? mentionSuggestions.map((item, i) => (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={() => insertMention(item)}
                                  className={`w-full px-3 py-2 text-left text-[13px] rounded-lg flex items-center gap-3 transition-all group ${activeMentionIndex === i ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-50'}`}
                                >
                                  <div className={`w-6 h-6 rounded flex items-center justify-center text-[10px] ${activeMentionIndex === i ? 'bg-indigo-100' : 'bg-slate-100 group-hover:bg-indigo-100'}`}>{item.icon}</div>
                                  <div className="flex-1 min-w-0">
                                    <div className="font-medium truncate">{item.title}</div>
                                    <div className="text-[10px] text-slate-400 truncate">{item.subtitle}</div>
                                  </div>
                                  <CornerDownLeft size={10} className="text-slate-300 opacity-0 group-hover:opacity-100" />
                                </button>
                              )) : (
                                !isMentionLoading && (
                                  <div className="px-4 py-3 text-center text-[12px] text-slate-400 italic">
                                    {mentionQuery.length < 2 ? "Tapez au moins 2 caractères..." : "Aucun résultat trouvé."}
                                  </div>
                                )
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      <form onSubmit={handleSubmit} className="relative flex flex-col bg-white border border-slate-200 rounded-md p-1.5 transition-all focus-within:ring-4 focus-within:ring-indigo-500/5 focus-within:border-indigo-500/20">
                        <input 
                          type="file" 
                          ref={fileInputRef} 
                          className="hidden" 
                          multiple 
                          onChange={handleFileChange}
                        />
                        <div 
                          ref={editorRef}
                          contentEditable
                          onInput={handleEditorInput}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              if (mentionQuery !== null && mentionSuggestions.length > 0) {
                                e.preventDefault();
                                insertMention(mentionSuggestions[activeMentionIndex]);
                              } else {
                                e.preventDefault();
                                handleSubmit(e as any);
                              }
                            }
                            if (e.key === 'ArrowDown' && mentionQuery !== null) {
                              e.preventDefault();
                              setActiveMentionIndex(prev => (prev + 1) % (mentionSuggestions.length || 1));
                            }
                            if (e.key === 'ArrowUp' && mentionQuery !== null) {
                              e.preventDefault();
                              setActiveMentionIndex(prev => (prev - 1 + (mentionSuggestions.length || 1)) % (mentionSuggestions.length || 1));
                            }
                          }}
                          className="w-full bg-transparent border-none outline-none ring-0 focus:ring-0 pt-2 pb-0 px-2 text-[13px] font-medium text-slate-700 placeholder:text-slate-400 min-h-[60px] max-h-[200px] overflow-y-auto assistant-scrollbar"
                          data-placeholder="Posez une question ou tapez @ pour mentionner..."
                        />
                        <div className="flex items-center justify-between mt-0">
                          <button 
                            type="button" 
                            onClick={handleFileButtonClick}
                            className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                            title="Joindre un fichier"
                          >
                            <Paperclip size={20} />
                          </button>
                          <button 
                            type="submit" 
                            disabled={(isEditorEmpty && attachedFiles.length === 0) || isLoading} 
                            className={`p-2 rounded-lg transition-all ${ (!isEditorEmpty || attachedFiles.length > 0) && !isLoading ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200 hover:bg-indigo-700 active:scale-95' : 'text-slate-300'}`}
                          >
                            <ArrowUp size={20} />
                          </button>
                        </div>
                      </form>
                    </div>
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
        className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-xl transition-all ${isOpen ? 'bg-slate-900' : 'bg-indigo-600'}`}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div key="close" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><X className="text-white" size={18} /></motion.div>
          ) : (
            <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-white font-serif text-xl">道</motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
};
