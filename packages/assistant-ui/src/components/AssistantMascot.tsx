import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAssistant } from '../hooks/useAssistant';

export const AssistantMascot = () => {
  const { messages, sendMessage, clearSession, isOpen, setIsOpen, isLoading } = useAssistant();
  const [input, setInput] = React.useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="mb-4 w-80 h-[32rem] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium flex justify-between items-center shadow-lg">
              <div className="flex items-center gap-2">
                 <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                 <span>Michi Assistant</span>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={clearSession} 
                  title="Nouvelle conversation"
                  className="text-white/60 hover:text-white transition-colors p-1"
                >
                  ↺
                </button>
                <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white p-1 ml-1">✕</button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4 scroll-smooth">
              {messages.length === 0 && (
                <div className="text-gray-500 text-sm text-center mt-10">
                  <div className="text-3xl mb-4">👋</div>
                  Bonjour ! Je suis l'assistant Michi.<br/>Comment puis-je vous aider aujourd'hui ?
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-3 rounded-2xl text-sm shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-indigo-600 text-white rounded-br-none' 
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 p-3 rounded-2xl rounded-bl-none animate-pulse text-xs text-gray-400">
                    En train de réfléchir...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100 flex gap-2 bg-gray-50/50">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Posez votre question..."
                className="flex-1 text-sm outline-none bg-transparent border-b border-gray-200 focus:border-indigo-500 transition-colors py-1"
              />
              <button 
                type="submit" 
                disabled={!input.trim() || isLoading}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                  input.trim() && !isLoading ? 'bg-indigo-600 text-white shadow-md' : 'bg-gray-200 text-gray-400'
                }`}
              >
                ↑
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-16 h-16 bg-gradient-to-tr from-purple-600 to-indigo-600 rounded-full shadow-lg flex items-center justify-center cursor-pointer overflow-hidden border-2 border-white/20"
      >
        <motion.div
          animate={isOpen ? { scale: 1.2 } : { 
            scale: [1, 1.2, 1],
            rotate: [0, 5, -5, 0]
          }}
          transition={{ 
            duration: 4, 
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="w-8 h-8 bg-white rounded-full opacity-80 blur-sm"
        />
        <div className="absolute inset-0 flex items-center justify-center text-white font-bold text-xl">
          {isOpen ? '💬' : '道'}
        </div>
      </motion.div>
    </div>
  );
};
