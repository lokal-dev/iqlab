import { useState, useEffect } from 'react';

const HISTORY_KEY = 'iqlab:history';
const MAX_HISTORY = 10;

/**
 * Recent search history stored in localStorage.
 * Returns: { history, addToHistory, clearHistory }
 */
export function useHistory() {
  const [history, setHistory] = useState(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch {
      // localStorage full or unavailable — silent fail
    }
  }, [history]);

  function addToHistory(verse) {
    setHistory(prev => {
      // Remove duplicate if same surah:ayah exists
      const filtered = prev.filter(
        v => !(v.surahNumber === verse.surahNumber && v.ayahNumber === verse.ayahNumber)
      );
      // Prepend and cap at MAX_HISTORY
      return [verse, ...filtered].slice(0, MAX_HISTORY);
    });
  }

  function clearHistory() {
    setHistory([]);
  }

  return { history, addToHistory, clearHistory };
}
