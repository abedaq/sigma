import { ref } from 'vue';

export interface HistoryItem {
  id: string;
  fileName: string;
  fileSize?: string;
  sourceLang: string;
  targetLang: string;
  timestamp: number;
  srtContent?: string;
  status: 'completed' | 'failed';
}

const STORAGE_KEY = 'sigma_vtt_projects_history';
const historyItems = ref<HistoryItem[]>(loadHistory());

function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    return [];
  }
}

function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(historyItems.value));
  } catch (err) {
    console.error('Failed to save history to localStorage:', err);
  }
}

export function useHistory() {
  function addItem(item: Omit<HistoryItem, 'id' | 'timestamp'>) {
    const newItem: HistoryItem = {
      ...item,
      id: 'proj_' + Date.now().toString(36),
      timestamp: Date.now()
    };

    // Prepend to top and limit to 15 items
    historyItems.value = [newItem, ...historyItems.value.slice(0, 14)];
    saveHistory();
    return newItem;
  }

  function removeItem(id: string) {
    historyItems.value = historyItems.value.filter(i => i.id !== id);
    saveHistory();
  }

  function clearAll() {
    historyItems.value = [];
    saveHistory();
  }

  return {
    historyItems,
    addItem,
    removeItem,
    clearAll
  };
}
