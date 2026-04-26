import { useState, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const useAssistant = (endpoint: string = "http://localhost:8001/graphql") => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string, jwt?: string) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'user', content }]);

    const query = `
      mutation SendMessage($content: String!, $sessionId: String) {
        sendMessage(content: $content, sessionId: $sessionId) {
          reply
          sessionId
          suggestedActions
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
      setSessionId(result.sessionId);
    } catch (error) {
      console.error("[Assistant] Error sending message:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Désolé, j'ai une petite perte de connexion." }]);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint, sessionId]);

  return {
    messages,
    sendMessage,
    isOpen,
    setIsOpen,
    isLoading
  };
};
