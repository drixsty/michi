import { create } from 'zustand';
import { Message, Session } from '../domain/models';
import { GraphQLAdapter } from '../infrastructure/adapters/GraphQLAdapter';
import { LocalStorageAdapter } from '../infrastructure/adapters/LocalStorageAdapter';

interface AssistantState {
  isOpen: boolean;
  isExpanded: boolean;
  isLoading: boolean;
  view: 'home' | 'chat' | 'history';
  sessionId: string | null;
  messages: Message[];
  sessions: Session[];
  
  // Actions
  setIsOpen: (isOpen: boolean) => void;
  setIsExpanded: (isExpanded: boolean) => void;
  setView: (view: 'home' | 'chat' | 'history') => void;
  setSessionId: (id: string | null) => void;
  
  // Thunks
  fetchSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  startNewChat: () => void;
  sendMessage: (content: string, files?: File[]) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, newTitle: string) => Promise<boolean>;
  rateMessage: (messageId: string, rating: 'UP' | 'DOWN', feedbackText?: string) => Promise<void>;
  
  // Local state for UI
  addMessage: (msg: Message) => void;
}

export const useAssistantState = create<AssistantState>((set, get) => ({
  isOpen: false,
  isExpanded: false,
  isLoading: false,
  view: 'home',
  sessionId: LocalStorageAdapter.getSessionId(),
  messages: [],
  sessions: [],

  setIsOpen: (isOpen) => set({ isOpen }),
  setIsExpanded: (isExpanded) => set({ isExpanded }),
  setView: (view) => set({ view }),
  setSessionId: (id) => {
    set({ sessionId: id });
    if (id) LocalStorageAdapter.setSessionId(id);
    else LocalStorageAdapter.clearSessionId();
  },

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  fetchSessions: async () => {
    try {
      const sessions = await GraphQLAdapter.fetchSessions();
      set({ sessions });
    } catch (e) {
      console.error(e);
    }
  },

  loadSession: async (sessionId) => {
    set({ isLoading: true });
    try {
      const messages = await GraphQLAdapter.getSession(sessionId);
      set({ messages, sessionId, view: 'chat' });
      LocalStorageAdapter.setSessionId(sessionId);
    } catch (e) {
      console.error(e);
      set({ messages: [] });
    } finally {
      set({ isLoading: false });
    }
  },

  startNewChat: () => {
    set({ sessionId: null, messages: [], view: 'chat' });
    LocalStorageAdapter.clearSessionId();
  },

  deleteSession: async (sessionId) => {
    try {
      await GraphQLAdapter.deleteSession(sessionId);
      set((state) => ({ sessions: state.sessions.filter(s => s.sessionId !== sessionId) }));
      if (get().sessionId === sessionId) {
        get().startNewChat();
      }
    } catch (e) {
      console.error(e);
    }
  },

  renameSession: async (sessionId, newTitle) => {
    try {
      await GraphQLAdapter.renameSession(sessionId, newTitle);
      set((state) => ({
        sessions: state.sessions.map(s => s.sessionId === sessionId ? { ...s, title: newTitle } : s)
      }));
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  },

  rateMessage: async (messageId, rating, feedbackText) => {
    try {
      const success = await GraphQLAdapter.rateMessage(messageId, rating, feedbackText);
      if (success) {
        set((state) => ({
          messages: state.messages.map(m => m.id === messageId ? { ...m, rating, feedbackText } : m)
        }));
      }
    } catch (e) {
      console.error(e);
    }
  },

  sendMessage: async (content, files = []) => {
    set({ isLoading: true });
    
    let processedContent = content;
    
    // Upload files and extract text (Phase 4)
    if (files.length > 0) {
      try {
        const fileResults = await Promise.all(
          files.map(file => GraphQLAdapter.uploadFile(file, get().sessionId))
        );
        processedContent = fileResults.join('\n\n') + '\n\n' + content;
      } catch (e) {
        console.error("File upload error:", e);
      }
    }

    const userMsg: Message = { 
      id: `u-${Date.now()}`, 
      role: 'user', 
      content, 
      files: files.map(f => ({ name: f.name, size: f.size })),
      timestamp: new Date().toISOString() 
    };
    get().addMessage(userMsg);

    const assistantMsgId = `a-${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isNew: true,
      timestamp: new Date().toISOString()
    };
    get().addMessage(assistantMsg);

    let fullContent = "";

    GraphQLAdapter.subscribeToMessage(
      processedContent,
      get().sessionId,
      (chunk, newSessionId, suggestedActions) => {
        fullContent += chunk;
        set((state) => ({
          messages: state.messages.map(m => m.id === assistantMsgId ? { 
            ...m, 
            content: fullContent,
            suggestedActions: suggestedActions || m.suggestedActions 
          } : m)
        }));
        
        if (!get().sessionId && newSessionId) {
          get().setSessionId(newSessionId);
          get().fetchSessions();
        }
      },
      (error) => {
        console.error("Stream Error:", error);
        set((state) => ({
          messages: state.messages.map(m => m.id === assistantMsgId ? { ...m, content: "Erreur de streaming." } : m),
          isLoading: false
        }));
      },
      () => {
        set({ isLoading: false });
      }
    );
  }
}));
