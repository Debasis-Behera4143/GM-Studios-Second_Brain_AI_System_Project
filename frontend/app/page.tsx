"use client";

import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { Send, Plus, Mic, BrainCircuit } from 'lucide-react';

const MessageBubble = React.memo(({ msg }: { msg: any }) => {
  return (
    <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] p-4 rounded-2xl ${
        msg.role === 'user' 
          ? 'bg-primary-600 text-white rounded-br-sm shadow-md' 
          : 'bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-bl-sm shadow-sm'
      }`}>
        <p className="whitespace-pre-wrap">{msg.content}</p>
        
        {/* Citations block */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
            <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 block">Sources</span>
            <div className="flex flex-col gap-2">
              {msg.sources.map((src: any, j: number) => (
                <div key={j} className="text-xs p-2 rounded bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-100 dark:border-zinc-700">
                  {typeof src.similarity === 'number' && (
                    <p className="mb-1 font-medium text-primary-600 dark:text-primary-400">
                      Match: {Math.round(src.similarity * 100)}%
                    </p>
                  )}
                  <p className="line-clamp-2 text-zinc-600 dark:text-zinc-400">"{src.content}"</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

export default function Home() {
  const [inputText, setInputText] = useState("");
  const { messages, isQuerying, isIngesting, isInitializing, queryRAG, ingestNote, initializeSession } = useStore();

  useEffect(() => {
    void initializeSession();
  }, [initializeSession]);

  const handleSend = () => {
    if (!inputText.trim() || isInitializing) return;
    queryRAG(inputText);
    setInputText("");
  };

  const handleIngest = () => {
    if (!inputText.trim() || isInitializing) return;
    ingestNote(inputText, "text");
    setInputText("");
  };

  return (
    <div className="relative flex flex-col h-[90vh] bg-white/90 dark:bg-zinc-900/90 rounded-3xl shadow-2xl overflow-hidden border border-zinc-100/80 dark:border-zinc-800 backdrop-blur-sm">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 -right-20 h-56 w-56 rounded-full bg-primary-500/10 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-cyan-400/10 blur-3xl" />
      </div>
      {/* Header */}
      <header className="relative z-10 px-6 py-4 border-b border-zinc-100/80 dark:border-zinc-800 flex items-center gap-3 bg-white/70 dark:bg-zinc-900/70 backdrop-blur-sm">
        <div className="bg-primary-500 p-2 rounded-lg text-white">
          <BrainCircuit size={24} />
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-semibold tracking-tight">Second Brain</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Private notes, quick retrieval, and grounded answers.</p>
        </div>
        <div className="hidden sm:inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Session ready
        </div>
      </header>

      {/* Chat / View Area */}
      <div className="relative z-10 flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-50/80 dark:bg-zinc-950/40">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {isQuerying && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 p-4 rounded-2xl animate-pulse">
              <span className="text-zinc-400 w-12 block">Thinking...</span>
            </div>
          </div>
        )}
        {isInitializing && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 p-4 rounded-2xl">
              <span className="text-zinc-400 w-40 block">Starting secure session...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <footer className="relative z-10 p-4 bg-white/80 dark:bg-zinc-900/80 border-t border-zinc-100/80 dark:border-zinc-800 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto space-y-2">
          <div className="relative flex items-center gap-2">
          
          <button 
            className="p-3 text-zinc-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-full transition-colors flex-shrink-0"
            title="Ingest / Save Note"
            onClick={handleIngest}
            disabled={isIngesting || isInitializing}
          >
            <Plus size={20} className={isIngesting ? "animate-spin" : ""} />
          </button>

          <input 
            type="text" 
            placeholder="Ask a question or save a new note..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isInitializing}
            className="flex-1 py-3 px-4 bg-zinc-100 dark:bg-zinc-800 border-transparent focus:bg-white dark:focus:bg-zinc-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 rounded-full outline-none transition-all shadow-sm"
          />

          <button 
            disabled
            className="p-3 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors flex-shrink-0"
            title="Voice input is disabled until server transcription is enabled"
          >
            <Mic size={20} />
          </button>

          <button 
            onClick={handleSend}
            disabled={isQuerying || isInitializing || !inputText.trim()}
            className="p-3 bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            <Send size={20} />
          </button>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 px-1">Press Enter to ask, or use the plus button to save a note.</p>
        </div>
      </footer>
    </div>
  );
}
