import { useState, useCallback, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const useAssistant = (endpoint: string = "http://localhost:8001/graphql") => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Hydrate sessionId from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('michi_assistant_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  const loadHistory = useCallback(async (sid: string) => {
    const query = `
      query GetChatHistory($sessionId: String!) {
        getChatHistory(sessionId: $sessionId) {
          role
          content
        }
      }
    `;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          variables: { sessionId: sid },
        }),
      });

      const result = await response.json();
      if (result.data?.getChatHistory) {
        setMessages(result.data.getChatHistory);
      }
    } catch (error) {
      console.error("[Assistant] Error loading history:", error);
    }
  }, [endpoint]);

  // Load history when sessionId is hydrated or changed
  useEffect(() => {
    if (sessionId && messages.length === 0) {
      loadHistory(sessionId);
    }
  }, [sessionId, loadHistory, messages.length]);

  const sendMessage = useCallback(async (content: string, jwt?: string) => {
    setIsLoading(true);
    // Optimistic update
    setMessages(prev => [...prev, { role: 'user', content }]);

    const query = `
      mutation SendMessage($content: String!, $sessionId: String) {
        sendMessage(content: $content, sessionId: $sessionId) {
          reply
          sessionId
        }
      }
    `;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(jwt ? { 'Authorization': `Bearer ${jwt}` } : {}),
        },
        body: JSON.stringify({
          query,
          variables: { content, sessionId },
        }),
      });

      const data = await response.json();
      const result = data.data.sendMessage;

      setMessages(prev => [...prev, { role: 'assistant', content: result.reply }]);
      
      if (result.sessionId !== sessionId) {
        setSessionId(result.sessionId);
        localStorage.setItem('michi_assistant_session_id', result.sessionId);
      }
    } catch (error) {
      console.error("[Assistant] Error sending message:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Désolé, j'ai une petite perte de connexion." }]);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint, sessionId]);

  const clearSession = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem('michi_assistant_session_id');
  }, []);

  return {
    messages,
    sendMessage,
    clearSession,
    isOpen,
    setIsOpen,
    isLoading
  };
};
