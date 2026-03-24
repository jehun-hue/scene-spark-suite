import { create } from 'zustand';

interface SettingsState {
  apiKey: string;
  setApiKey: (key: string) => void;
  loadApiKey: () => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  apiKey: localStorage.getItem('gemini_api_key') || '',
  setApiKey: (apiKey) => {
    localStorage.setItem('gemini_api_key', apiKey);
    set({ apiKey });
  },
  loadApiKey: () => {
    const key = localStorage.getItem('gemini_api_key') || '';
    set({ apiKey: key });
  },
}));
