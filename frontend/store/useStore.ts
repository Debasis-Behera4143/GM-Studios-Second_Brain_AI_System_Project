import { create } from 'zustand';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

interface AppState {
  messages: Message[];
  isIngesting: boolean;
  isQuerying: boolean;
  isInitializing: boolean;
  sessionToken: string | null;
  initializeSession: () => Promise<void>;
  addMessage: (msg: Message) => void;
  ingestNote: (content: string, type: string) => Promise<void>;
  queryRAG: (query: string) => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
const SESSION_STORAGE_KEY = 'second-brain-session-token';

const readStoredSessionToken = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem(SESSION_STORAGE_KEY);
};

const writeStoredSessionToken = (token: string) => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(SESSION_STORAGE_KEY, token);
  }
};

const clearStoredSessionToken = () => {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  }
};

const buildHeaders = (token: string | null) =>
  token
    ? {
        'X-Session-Token': token,
      }
    : {};

export const useStore = create<AppState>((set, get) => ({
  messages: [{ role: 'assistant', content: 'Hello! I am your Second Brain. How can I help you today?' }],
  isIngesting: false,
  isQuerying: false,
  isInitializing: false,
  sessionToken: null,
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  initializeSession: async () => {
    if (get().sessionToken) {
      return;
    }

    const storedToken = readStoredSessionToken();
    if (storedToken) {
      set({ sessionToken: storedToken });
      return;
    }

    set({ isInitializing: true });
    try {
      const res = await axios.post(`${API_BASE}/session`);
      const token =
        typeof res.data?.session_token === 'string' && res.data.session_token.trim()
          ? res.data.session_token
          : null;

      if (!token) {
        throw new Error('Missing session token');
      }

      writeStoredSessionToken(token);
      set({ sessionToken: token });
    } catch (error) {
      console.error(error);
      get().addMessage({
        role: 'assistant',
        content: 'I could not start a secure session. Please refresh and try again.'
      });
      throw error;
    } finally {
      set({ isInitializing: false });
    }
  },
  
  ingestNote: async (content, type) => {
    set({ isIngesting: true });
    try {
      await get().initializeSession();
      const token = get().sessionToken ?? readStoredSessionToken();
      await axios.post(`${API_BASE}/ingest`, {
        content: content,
        source_type: type
      }, {
        headers: buildHeaders(token)
      });
      get().addMessage({
        role: 'assistant',
        content: 'Your note was saved successfully. Ask a question about it any time.'
      });
    } catch (error) {
      console.error(error);
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        clearStoredSessionToken();
        set({ sessionToken: null });
      }
      get().addMessage({
        role: 'assistant',
        content: 'I could not save that note right now. Please check that the backend is running and try again.'
      });
    } finally {
      set({ isIngesting: false });
    }
  },

  queryRAG: async (query) => {
    set({ isQuerying: true });
    get().addMessage({ role: 'user', content: query });
    
    try {
      await get().initializeSession();
      let token = get().sessionToken ?? readStoredSessionToken();
      const res = await axios.post(`${API_BASE}/query`, {
        query: query
      }, {
        headers: buildHeaders(token)
      });
      
      const answer =
        typeof res.data?.answer === 'string' && res.data.answer.trim()
          ? res.data.answer
          : 'I found matching notes, but the answer came back empty. Please try again.';

      get().addMessage({
        role: 'assistant',
        content: answer,
        sources: Array.isArray(res.data?.sources) ? res.data.sources : []
      });
    } catch (error) {
      console.error(error);
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        clearStoredSessionToken();
        set({ sessionToken: null });
      }
      get().addMessage({
        role: 'assistant',
        content: 'Sorry, there was an error retrieving the answer.'
      });
    } finally {
      set({ isQuerying: false });
    }
  }
}));
