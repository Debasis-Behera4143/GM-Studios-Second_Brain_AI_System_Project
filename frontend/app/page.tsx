"use client";

import React, { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';
import { Send, Plus, Mic, BrainCircuit, Upload, RefreshCw, Sparkles, Menu, X, Square } from 'lucide-react';
import { AudioRecorder, blobToFile, isAudioRecordingSupported } from '../lib/audioRecorder';

const MessageBubble = React.memo(({ msg }: { msg: any }) => {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl p-4 ${
          isUser
            ? 'rounded-br-sm bg-primary-600 text-white shadow-lg'
            : 'rounded-bl-sm border border-zinc-200/70 bg-white/90 shadow-sm dark:border-zinc-700 dark:bg-zinc-900/90'
        }`}
      >
        <p className="whitespace-pre-wrap">{msg.content}</p>
        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-4 border-t border-zinc-200 pt-4 dark:border-zinc-700">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-wider text-zinc-500">Sources</span>
            <div className="flex flex-col gap-2">
              {msg.sources.map((src: any, idx: number) => (
                <div key={idx} className="rounded-xl border border-zinc-200 bg-zinc-50 p-2 text-xs dark:border-zinc-700 dark:bg-zinc-950/60">
                  {typeof src.similarity === 'number' && (
                    <p className="mb-1 font-medium text-primary-600 dark:text-primary-400">Match: {Math.round(src.similarity * 100)}%</p>
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
  const [askText, setAskText] = useState('');
  const [saveText, setSaveText] = useState('');
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<'save' | 'upload' | 'resurface'>('save');
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingMode, setRecordingMode] = useState<'microphone' | 'file' | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const voiceInputRef = useRef<HTMLInputElement | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [canRecord] = useState(isAudioRecordingSupported());

  const {
    messages,
    isQuerying,
    isIngesting,
    isInitializing,
    isFetchingSuggestions,
    resurfacingSuggestions,
    queryRAG,
    ingestNote,
    ingestFile,
    queryByVoice,
    fetchResurfacing,
    initializeSession,
  } = useStore();

  useEffect(() => {
    const bootstrap = async () => {
      await initializeSession();
      await fetchResurfacing();
    };
    void bootstrap();
  }, [initializeSession, fetchResurfacing]);

  useEffect(() => {
    return () => {
      // Cleanup: stop recording and clear timer on unmount
      if (isRecordingVoice && recorderRef.current) {
        try {
          recorderRef.current.stop();
        } catch (error) {
          console.error('Failed to stop recorder on unmount:', error);
        }
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecordingVoice]);

  const handleAsk = () => {
    if (!askText.trim() || isInitializing) return;
    queryRAG(askText.trim());
    setAskText('');
  };

  const handleSave = () => {
    if (!saveText.trim() || isInitializing) return;
    const trimmed = saveText.trim();
    const sourceType = /^https?:\/\//i.test(trimmed) ? 'url' : 'text';
    ingestNote(trimmed, sourceType);
    setSaveText('');
  };

  const handlePickFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    void ingestFile(file);
    event.target.value = '';
  };

  const handlePickVoice = () => {
    if (canRecord) {
      setRecordingMode('microphone');
    } else {
      setRecordingMode('file');
    }
  };

  const handleStartRecording = async () => {
    try {
      const recorder = new AudioRecorder({
        onStart: () => {
          setIsRecordingVoice(true);
          setRecordingTime(0);
        },
        onStop: () => {
          setIsRecordingVoice(false);
          if (timerRef.current) {
            clearInterval(timerRef.current);
          }
        },
        onError: (error) => {
          console.error('Recording error:', error);
          setIsRecordingVoice(false);
          setRecordingMode(null);
        },
      });

      await recorder.start();
      recorderRef.current = recorder;

      // Start timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      timerRef.current = setInterval(() => {
        setRecordingTime((t) => t + 1);
      }, 1000);
    } catch (error) {
      console.error('Failed to start recording:', error);
      setRecordingMode('file');
    }
  };

  const handleStopRecording = async () => {
    try {
      if (recorderRef.current && recorderRef.current.isRecordingNow()) {
        const audioBlob = recorderRef.current.stop();
        const audioFile = blobToFile(audioBlob, 'voice-query.wav');
        setRecordingMode(null);
        void queryByVoice(audioFile);
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const handlePickVoiceFile = () => {
    setRecordingMode('file');
    voiceInputRef.current?.click();
  };

  const handleVoiceSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    void queryByVoice(file);
    setRecordingMode(null);
    event.target.value = '';
  };

  return (
    <div className="relative flex h-[100dvh] md:h-[92vh] overflow-hidden rounded-none border-0 bg-white/80 md:rounded-3xl md:border md:border-zinc-200/80 md:shadow-2xl dark:bg-zinc-900/70 dark:md:border-zinc-800">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 left-1/3 h-72 w-72 rounded-full bg-primary-500/12 blur-3xl" />
        <div className="absolute -bottom-24 left-8 h-72 w-72 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      <aside className="relative z-10 hidden w-80 flex-col gap-4 border-r border-zinc-200/70 bg-zinc-50/85 p-5 dark:border-zinc-800 dark:bg-zinc-900/65 lg:flex xl:w-96">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary-600 p-2 text-white shadow-md">
            <BrainCircuit size={22} />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Second Brain Studio</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Capture, retrieve, resurface.</p>
          </div>
        </div>

        <section className="rounded-2xl border border-zinc-200/70 bg-white/85 p-4 dark:border-zinc-800 dark:bg-zinc-900/75">
          <h2 className="mb-2 text-sm font-semibold">Save Note or URL</h2>
          <textarea
            value={saveText}
            onChange={(e) => setSaveText(e.target.value)}
            placeholder="Write note or paste URL"
            className="h-28 w-full resize-none rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-primary-500 dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button
            onClick={handleSave}
            disabled={!saveText.trim() || isIngesting || isInitializing}
            className="mt-3 inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-700 disabled:opacity-50"
          >
            <Plus size={16} /> Save
          </button>
        </section>

        <section className="rounded-2xl border border-zinc-200/70 bg-white/85 p-4 dark:border-zinc-800 dark:bg-zinc-900/75">
          <h2 className="mb-2 text-sm font-semibold">File Ingestion</h2>
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelected} />
          <button
            onClick={handlePickFile}
            disabled={isIngesting || isInitializing}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            <Upload size={16} /> Upload and Ingest
          </button>
        </section>

        <section className="rounded-2xl border border-zinc-200/70 bg-white/85 p-4 dark:border-zinc-800 dark:bg-zinc-900/75">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Resurfacing</h2>
            <button
              onClick={() => void fetchResurfacing()}
              className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-200"
            >
              <RefreshCw size={14} className={isFetchingSuggestions ? 'animate-spin' : ''} /> Refresh
            </button>
          </div>
          <div className="space-y-2">
            {resurfacingSuggestions.length === 0 && (
              <p className="text-xs text-zinc-500 dark:text-zinc-400">No suggestions yet.</p>
            )}
            {resurfacingSuggestions.map((item) => (
              <div key={item.id} className="rounded-xl border border-zinc-200 bg-zinc-50 p-2 text-xs dark:border-zinc-700 dark:bg-zinc-950/60">
                {item.content}
              </div>
            ))}
          </div>
        </section>
      </aside>

      <main className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-200/70 bg-white/70 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900/70 md:px-5 md:py-4">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-primary-500" />
            <h2 className="text-sm font-semibold md:text-base">Grounded Chat</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobilePanelOpen((prev) => !prev)}
              className="inline-flex items-center justify-center rounded-xl border border-zinc-300 p-2 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800 lg:hidden"
              title="Toggle tools"
            >
              {mobilePanelOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
            <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
              secure session
            </span>
          </div>
        </header>

        {mobilePanelOpen && (
          <section className="border-b border-zinc-200/70 bg-white/92 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900/88 lg:hidden">
            <div className="mb-3 flex items-center gap-2 overflow-x-auto">
              {(['save', 'upload', 'resurface'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setMobileTab(tab)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize ${mobileTab === tab ? 'bg-primary-600 text-white' : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300'}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {mobileTab === 'save' && (
              <div className="space-y-2">
                <textarea
                  value={saveText}
                  onChange={(e) => setSaveText(e.target.value)}
                  placeholder="Write note or paste URL"
                  className="h-24 w-full resize-none rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-primary-500 dark:border-zinc-700 dark:bg-zinc-900"
                />
                <button
                  onClick={handleSave}
                  disabled={!saveText.trim() || isIngesting || isInitializing}
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
                >
                  <Plus size={14} /> Save
                </button>
              </div>
            )}

            {mobileTab === 'upload' && (
              <button
                onClick={handlePickFile}
                disabled={isIngesting || isInitializing}
                className="inline-flex items-center gap-2 rounded-xl border border-zinc-300 px-3 py-2 text-xs font-medium transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
              >
                <Upload size={14} /> Upload file
              </button>
            )}

            {mobileTab === 'resurface' && (
              <div className="space-y-2">
                <button
                  onClick={() => void fetchResurfacing()}
                  className="inline-flex items-center gap-2 rounded-xl border border-zinc-300 px-3 py-2 text-xs font-medium transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  <RefreshCw size={14} className={isFetchingSuggestions ? 'animate-spin' : ''} /> Refresh
                </button>
                <div className="max-h-28 space-y-1 overflow-y-auto">
                  {resurfacingSuggestions.length === 0 && (
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">No suggestions yet.</p>
                  )}
                  {resurfacingSuggestions.map((item) => (
                    <div key={item.id} className="rounded-lg border border-zinc-200 bg-zinc-50 p-2 text-xs dark:border-zinc-700 dark:bg-zinc-950/60">
                      {item.content}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        <div className="flex-1 space-y-4 overflow-y-auto bg-zinc-50/70 p-4 dark:bg-zinc-950/30 md:space-y-5 md:p-5">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}
          {isQuerying && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-zinc-200 bg-white p-3 text-sm text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900">
                Thinking with your notes...
              </div>
            </div>
          )}
        </div>

        <footer className="border-t border-zinc-200/70 bg-white/75 p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] dark:border-zinc-800 dark:bg-zinc-900/75 md:p-4 md:pb-4">
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask a grounded question from your notes"
              value={askText}
              onChange={(e) => setAskText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              disabled={isInitializing || isRecordingVoice}
              className="flex-1 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-primary-500 dark:border-zinc-700 dark:bg-zinc-900"
            />

            <input ref={voiceInputRef} type="file" accept="audio/*" className="hidden" onChange={handleVoiceSelected} />
            
            {!isRecordingVoice ? (
              <button
                onClick={handlePickVoice}
                disabled={isQuerying || isInitializing}
                className="rounded-xl border border-zinc-300 px-3 py-3 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
                title={canRecord ? "Record voice or upload audio file" : "Upload audio file"}
              >
                <Mic size={18} />
              </button>
            ) : (
              <button
                onClick={handleStopRecording}
                className="animate-pulse rounded-xl border border-red-300 bg-red-50 px-3 py-3 text-red-500 transition dark:border-red-900 dark:bg-red-950/30"
                title="Stop recording"
              >
                <Square size={18} />
              </button>
            )}

            <button
              onClick={handleAsk}
              disabled={isQuerying || isInitializing || !askText.trim() || isRecordingVoice}
              className="rounded-xl bg-primary-600 px-4 py-3 text-white transition hover:bg-primary-700 disabled:opacity-50"
            >
              <Send size={18} />
            </button>
          </div>
          
          {recordingMode && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
                <h3 className="mb-4 text-center text-lg font-semibold">Voice Input</h3>
                
                {!isRecordingVoice ? (
                  <div className="space-y-3">
                    {canRecord && (
                      <button
                        onClick={handleStartRecording}
                        className="w-full rounded-xl bg-red-600 px-4 py-3 text-white transition hover:bg-red-700 flex items-center justify-center gap-2"
                      >
                        <Mic size={18} /> Start Recording
                      </button>
                    )}
                    <button
                      onClick={handlePickVoiceFile}
                      className="w-full rounded-xl border border-zinc-300 px-4 py-3 text-sm font-medium transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
                    >
                      Upload Audio File
                    </button>
                    <button
                      onClick={() => setRecordingMode(null)}
                      className="w-full rounded-xl border border-zinc-300 px-4 py-3 text-sm font-medium transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center gap-3">
                      <div className="h-3 w-3 animate-pulse rounded-full bg-red-600"></div>
                      <span className="text-sm font-medium">Recording...</span>
                      <span className="text-sm text-zinc-500">{Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}</span>
                    </div>
                    <button
                      onClick={handleStopRecording}
                      className="w-full rounded-xl bg-red-600 px-4 py-3 text-white transition hover:bg-red-700 flex items-center justify-center gap-2"
                    >
                      <Square size={18} /> Stop & Send
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">Mobile and laptop both support Ask, Save, Upload, and Resurface.</p>
        </footer>
      </main>
    </div>
  );
}
