'use strict';
import { useState, useRef, useCallback, useEffect } from 'react';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useIdentify } from './hooks/useIdentify';
import { useHistory } from './hooks/useHistory';
import { extractCleanArabic, WAQF_SIGNS } from './data/mockVerses';
import './index.css';

/* ── Icons (inline SVG, Lucide-style) ────────────────────────── */
const IconMic = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" x2="12" y1="19" y2="22"/>
  </svg>
);

const IconMicOff = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="2" x2="22" y1="2" y2="22"/>
    <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/>
    <path d="M5 10v2a7 7 0 0 0 12 5"/>
    <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>
    <path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>
    <line x1="12" x2="12" y1="19" y2="22"/>
  </svg>
);

const IconUpload = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" x2="12" y1="3" y2="15"/>
  </svg>
);

const IconCopy = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
    <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
  </svg>
);

const IconCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);

const IconAlertCircle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" x2="12" y1="8" y2="12"/>
    <line x1="12" x2="12.01" y1="16" y2="16"/>
  </svg>
);

const IconAlertTriangle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
    <path d="M12 9v4"/>
    <path d="M12 17h.01"/>
  </svg>
);

const IconSearchX = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m13.5 8.5-5 5"/>
    <path d="m8.5 8.5 5 5"/>
    <circle cx="11" cy="11" r="8"/>
    <path d="m21 21-4.3-4.3"/>
  </svg>
);

const IconRefresh = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
    <path d="M21 3v5h-5"/>
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
    <path d="M8 16H3v5"/>
  </svg>
);

const IconBook = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
  </svg>
);

/* ── Confidence bar ──────────────────────────────────────────── */
function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  return (
    <div className="verse-confidence">
      <span className="verse-confidence-label">{pct}%</span>
      <div className="confidence-bar-track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={`Confidence: ${pct}%`}>
        <div className="confidence-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/* ── Copy button ─────────────────────────────────────────────── */
function CopyButton({ verse }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy(e) {
    e.stopPropagation();
    const text = extractCleanArabic(verse);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback — textarea copy
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <button
      className={`copy-btn${copied ? ' copied' : ''}`}
      onClick={handleCopy}
      aria-label={copied ? 'Tersalin!' : 'Salin ayah'}
      title={copied ? 'Tersalin!' : 'Salin ayah'}
    >
      {copied ? <IconCheck /> : <IconCopy />}
      {copied ? 'Tersalin!' : 'Salin Ayah'}
    </button>
  );
}

/* ── parseMakhrajFeedback ────────────────────────────────────── */
function parseMakhrajFeedback(html) {
  if (!html) return [];
  // Matches: <span class="makhraj-highlight makhraj-pass" title="Message" data-start="1.2" data-end="1.8">ح</span>
  const regex = /<span class="makhraj-highlight\s+makhraj-(pass|fail)"\s+title="([^"]+)"\s+data-start="([^"]+)"\s+data-end="([^"]+)">([^<]+)<\/span>/g;
  const feedback = [];
  let match;
  while ((match = regex.exec(html)) !== null) {
    feedback.push({
      status: match[1],   // 'pass' or 'fail'
      message: match[2],  // The playful feedback message
      start: match[3],    // Start timestamp
      end: match[4],      // End timestamp
      letter: match[5],   // The letter (ح or ع)
    });
  }
  return feedback;
}

/* ── AudioCompareButton ──────────────────────────────────────── */
function AudioCompareButton({ label, audioUrl, start, end, type }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);
  const timerRef = useRef(null);

  const handlePlay = (e) => {
    e.stopPropagation();
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      if (timerRef.current) clearTimeout(timerRef.current);
    } else {
      audio.currentTime = start ? parseFloat(start) : 0;
      audio.play();
      setIsPlaying(true);

      if (end) {
        const duration = (parseFloat(end) - parseFloat(start)) * 1000;
        timerRef.current = setTimeout(() => {
          audio.pause();
          setIsPlaying(false);
        }, duration);
      }
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <button className={`audio-compare-btn ${type}`} onClick={handlePlay} type="button">
      <audio ref={audioRef} src={audioUrl} onEnded={() => setIsPlaying(false)} preload="auto" />
      {isPlaying ? (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <rect x="6" y="4" width="4" height="16" rx="1"/>
          <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
      ) : (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M8 5v14l11-7z"/>
        </svg>
      )}
      <span>{label}</span>
    </button>
  );
}

/* ── MakhrajFeedbackPanel ────────────────────────────────────── */
function MakhrajFeedbackPanel({ feedback, audioBlob }) {
  const [audioUrl, setAudioUrl] = useState(null);

  useEffect(() => {
    if (!audioBlob) return;
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audioBlob]);

  // Calculate Makhraj Score
  const total = feedback.length;
  const passed = feedback.filter(f => f.status === 'pass').length;
  const score = total > 0 ? Math.round((passed / total) * 100) : 100;

  // Map letters to their local example audios
  const exampleAudioMap = {
    'ح': '/audio/examples/ha.mp3',
    'ع': '/audio/examples/ayn.mp3',
    'ص': '/audio/examples/sad.mp3'
  };

  return (
    <div className="makhraj-feedback-panel animate-slide-down">
      <div className="makhraj-panel-header">
        <div className="makhraj-score-container">
          <div className="makhraj-score-circle" style={{ '--score-pct': score }}>
            <span className="makhraj-score-val">{score}%</span>
          </div>
          <div className="makhraj-score-meta">
            <h4>Evaluasi Makhraj</h4>
            <p>{passed} dari {total} huruf tepat</p>
          </div>
        </div>
      </div>

      <div className="makhraj-feedback-list">
        {feedback.map((item, index) => (
          <div key={index} className={`makhraj-feedback-item ${item.status}`}>
            <div className="makhraj-item-header">
              <span className={`makhraj-letter-badge ${item.status}`}>{item.letter}</span>
              <span className={`makhraj-status-label ${item.status}`}>
                {item.status === 'pass' ? 'Fasih' : 'Hampir Tepat'}
              </span>
            </div>
            <p className="makhraj-item-message">{item.message}</p>
            
            <div className="makhraj-item-controls">
              {/* Correct Example Audio */}
              {exampleAudioMap[item.letter] && (
                <AudioCompareButton 
                  label="Dengarkan Contoh" 
                  audioUrl={exampleAudioMap[item.letter]} 
                  type="example"
                />
              )}
              {/* User's own audio segment */}
              {audioUrl && (
                <AudioCompareButton 
                  label="Suaramu" 
                  audioUrl={audioUrl} 
                  start={item.start} 
                  end={item.end} 
                  type="user"
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Waqf Legend ─────────────────────────────────────────────── */
function WaqfLegend() {
  return (
    <div className="waqf-legend" aria-label="Panduan tanda waqf">
      <p className="waqf-legend-title">Tanda Baca Waqf</p>
      <div className="waqf-legend-grid">
        {WAQF_SIGNS.map(({ sign, cls, label, desc }) => (
          <div key={cls} className="waqf-legend-item" title={desc}>
            <span className={`waqf-legend-sign waqf ${cls}`} aria-hidden="true">{sign}</span>
            <span className="waqf-legend-label">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Verse Card ──────────────────────────────────────────────── */
function VerseCard({ verse, isSelected, onSelect, audioBlob }) {
  const feedback = parseMakhrajFeedback(verse.tajweedHtml);
  const hasErrors = feedback.some(f => f.status === 'fail');

  return (
    <article
      className={`verse-card${isSelected ? ' selected' : ''}${hasErrors ? ' has-makhraj-errors' : ''}`}
      onClick={() => !isSelected && onSelect(verse)}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      aria-label={`${verse.surahName} ayat ${verse.ayahNumber}, keyakinan ${Math.round(verse.confidence * 100)}%`}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (!isSelected) onSelect(verse); } }}
    >
      {/* ── Header: always visible ── */}
      <div className="verse-card-header">
        <span className="verse-surah-badge">
          {verse.surahNameAr} · {verse.surahName} : {verse.ayahNumber}
        </span>
        <div className="verse-card-header-right">
          <ConfidenceBar value={verse.confidence} />
          {isSelected && (
            <button
              className="verse-card-close"
              onClick={e => { e.stopPropagation(); onSelect(verse); }}
              aria-label="Tutup detail"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* ── Arabic text: always visible, larger when selected ── */}
      <div
        className={`verse-arabic${isSelected ? ' verse-arabic--expanded' : ''}`}
        dir="rtl"
        lang="ar"
        dangerouslySetInnerHTML={{ __html: verse.tajweedHtml }}
      />

      {/* ── Collapsed hint & Makhraj Badge ── */}
      {!isSelected && (
        <div className="verse-card-collapsed-footer">
          {feedback.length > 0 && (
            <div className={`makhraj-summary-badge ${hasErrors ? 'error' : 'success'}`}>
              {hasErrors ? (
                <>
                  <IconAlertTriangle />
                  <span>Ada catatan makhraj! Ketuk untuk detail</span>
                </>
              ) : (
                <>
                  <IconCheck />
                  <span>Makhraj 100% fasih!</span>
                </>
              )}
            </div>
          )}
          <p className="verse-tap-hint">Ketuk untuk terjemahan &amp; evaluasi makhraj</p>
        </div>
      )}

      {/* ── Expanded: makhraj panel + translation + waqf legend ── */}
      {isSelected && (
        <div className="verse-expanded" role="region" aria-label="Detail ayat">
          {/* ── Combined Makhraj Panel (Option B & C) ── */}
          {feedback.length > 0 && (
            <MakhrajFeedbackPanel feedback={feedback} audioBlob={audioBlob} />
          )}

          <p className="verse-translation">{verse.translation}</p>
          <WaqfLegend />
          <div className="verse-card-footer">
            <CopyButton verse={verse} />
          </div>
        </div>
      )}

      {/* ── Copy in collapsed footer (subtle) ── */}
      {!isSelected && (
        <div className="verse-card-footer verse-card-footer--collapsed">
          <CopyButton verse={verse} />
        </div>
      )}
    </article>
  );
}

/* ── Quotes & Icons for Queue ────────────────────────────────── */
const IconQuote = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.75-2-2-2H4c-1.25 0-2 .75-2 2v6c0 1.25.75 2 2 2h3c0 4-3 6-3 6Zm11 0c3 0 7-1 7-8V5c0-1.25-.75-2-2-2h-4c-1.25 0-2 .75-2 2v6c0 1.25.75 2 2 2h3c0 4-3 6-3 6Z"/>
  </svg>
);

const ISLAMIC_QUOTES = [
  {
    text: "Barangsiapa menempuh jalan untuk mencari ilmu, Allah akan mudahkan baginya jalan menuju surga.",
    author: "HR. Muslim",
    category: "Hadits"
  },
  {
    text: "Ilmu tanpa amal adalah kegilaan, dan amal tanpa ilmu adalah kesia-siaan.",
    author: "Imam Al-Ghazali",
    category: "Kalam Hikmah"
  },
  {
    text: "Jika kamu tidak tahan terhadap penatnya belajar, maka kamu harus tahan terhadap perihnya kebodohan.",
    author: "Imam Asy-Syafi'i",
    category: "Kalam Hikmah"
  },
  {
    text: "Menghidupkan hati dengan ilmu seperti menghidupkan bumi yang mati dengan air hujan.",
    author: "Ibn Qayyim Al-Jawziyyah",
    category: "Kalam Hikmah"
  },
  {
    text: "Al-Khwarizmi menciptakan konsep Al-Jabar & Algoritma, menjadi fondasi dasar bagi komputer modern dan kecerdasan buatan (AI) hari ini.",
    author: "Fakta Sejarah",
    category: "Sains Islam"
  },
  {
    text: "Fatima Al-Fihri mendirikan Universitas Al-Qarawiyyin pada 859 M di Maroko, diakui oleh UNESCO sebagai universitas tertua di dunia.",
    author: "Fakta Sejarah",
    category: "Sejarah Islam"
  },
  {
    text: "Ibn Al-Haitham (Alhazen) merumuskan teori penglihatan modern & optik (Kamera Obscura) dengan membuktikan bahwa cahaya merambat lurus.",
    author: "Fakta Sejarah",
    category: "Sains Islam"
  },
  {
    text: "Kata 'Al-Ilm' (ilmu) beserta turunannya disebutkan sebanyak 779 kali dalam Al-Qur'an, menunjukkan betapa agungnya posisi ilmu.",
    author: "Fakta Al-Qur'an",
    category: "Statistik Al-Qur'an"
  }
];

/* ── Queue Indicator ─────────────────────────────────────────────── */
function QueueIndicator({ onCancel, audioBlob }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0); // 0-100
  const [audioUrl, setAudioUrl] = useState(null);
  
  // Quote rotation state
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);

  // Create & revoke object URL from blob
  useEffect(() => {
    if (!audioBlob) return;
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audioBlob]);

  // Sync progress bar with audio
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    function onTimeUpdate() {
      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }
    }
    function onEnded() {
      setIsPlaying(false);
      setProgress(0);
    }
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('ended', onEnded);
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('ended', onEnded);
    };
  }, [audioUrl]);

  // Quote rotation effect (every 5.5 seconds: 5s display + 0.5s fade out/in transition)
  useEffect(() => {
    const interval = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setQuoteIndex((prev) => (prev + 1) % ISLAMIC_QUOTES.length);
        setIsFading(false);
      }, 400); // Wait for fade-out animation to complete
    }, 5500);
    
    return () => clearInterval(interval);
  }, []);

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.currentTime = 0;
      audio.play();
      setIsPlaying(true);
    }
  }

  const currentQuote = ISLAMIC_QUOTES[quoteIndex];

  return (
    <div className="queue-indicator" role="status" aria-live="polite" aria-label="Sedang memproses audio">
      <div className="queue-dots" aria-hidden="true">
        <div className="queue-dot" />
        <div className="queue-dot" />
        <div className="queue-dot" />
      </div>
      <p className="queue-text">Sedang memproses rekaman…</p>

      {/* ── Did You Know & Quote Card ── */}
      <div className={`quote-card ${isFading ? 'fade-out' : 'fade-in'}`}>
        <div className="quote-header">
          <span className="quote-category">{currentQuote.category}</span>
          <div className="quote-icon" aria-hidden="true">
            <IconQuote />
          </div>
        </div>
        <p className="quote-content">"{currentQuote.text}"</p>
        <span className="quote-author">— {currentQuote.author}</span>
      </div>

      {/* ── Replay player ── */}
      {audioUrl && (
        <div className="replay-player">
          <audio ref={audioRef} src={audioUrl} preload="auto" />
          <button
            className={`replay-btn${isPlaying ? ' playing' : ''}`}
            onClick={togglePlay}
            aria-label={isPlaying ? 'Jeda putar ulang' : 'Putar rekaman'}
            title={isPlaying ? 'Jeda' : 'Putar ulang rekaman'}
          >
            {isPlaying ? (
              /* Pause icon */
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1"/>
                <rect x="14" y="4" width="4" height="16" rx="1"/>
              </svg>
            ) : (
              /* Play icon */
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            )}
          </button>
          <div className="replay-progress-track" aria-hidden="true">
            <div className="replay-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="replay-label">Dengarkan ulang</span>
        </div>
      )}

      <button className="queue-cancel" onClick={onCancel}>Batalkan</button>
    </div>
  );
}

/* ── Error Banner ────────────────────────────────────────────── */
function ErrorBanner({ type, message }) {
  const isWarning = type === 'warning';
  return (
    <div className={`error-banner ${isWarning ? 'warning' : 'error'}`} role="alert">
      {isWarning ? <IconAlertTriangle /> : <IconAlertCircle />}
      <p>{message}</p>
    </div>
  );
}

/* ── Zero Match ──────────────────────────────────────────────── */
function ZeroMatch({ onReset }) {
  return (
    <div className="zero-match">
      <div className="zero-match-icon" aria-hidden="true">
        <IconSearchX />
      </div>
      <h3>Tidak Ada Kecocokan</h3>
      <p>Kami tidak dapat menemukan ayat yang cocok. Coba rekam lebih jelas atau dengan klip yang lebih panjang.</p>
      <button className="try-again-btn" onClick={onReset}>
        <IconRefresh /> Coba Lagi
      </button>
    </div>
  );
}

/* ── History Strip ───────────────────────────────────────────── */
function HistoryStrip({ history }) {
  if (history.length === 0) return null;
  return (
    <section className="history-section" aria-label="Riwayat pencarian">
      <p className="history-label">Riwayat</p>
      <div className="history-strip">
        {history.map((v, i) => (
          <button key={`${v.surahNumber}-${v.ayahNumber}-${i}`} className="history-chip" aria-label={`${v.surahName} ayat ${v.ayahNumber}`}>
            <span className="history-chip-surah">{v.surahNameAr}</span>
            <span>{v.surahName} : {v.ayahNumber}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

/* ── Upload validation ───────────────────────────────────────── */
const ACCEPTED_AUDIO_TYPES = [
  'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave',
  'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a',
  'audio/ogg', 'audio/webm', 'audio/flac',
];

function isAudioFile(file) {
  if (ACCEPTED_AUDIO_TYPES.includes(file.type)) return true;
  const ext = file.name.split('.').pop().toLowerCase();
  return ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'aac'].includes(ext);
}

/* ── Format timer ────────────────────────────────────────────── */
function formatTime(s) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

/* ── App ─────────────────────────────────────────────────────── */
export default function App() {
  const recorder = useAudioRecorder();
  const identifier = useIdentify();
  const { history, addToHistory } = useHistory();

  const [selectedVerse, setSelectedVerse] = useState(null);
  const [inputError, setInputError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showOtherResults, setShowOtherResults] = useState(false);

  // Track the active audio blob (from mic or file upload) so QueueIndicator can replay it
  const [activeAudioBlob, setActiveAudioBlob] = useState(null);

  const fileInputRef = useRef(null);
  const isProcessing = identifier.state === 'processing';

  /* Mic handlers */
  async function handleMicClick() {
    if (recorder.isRecording) {
      recorder.stopRecording();
    } else {
      setInputError(null);
      identifier.reset();
      setSelectedVerse(null);
      try {
        await recorder.startRecording();
      } catch {
        setInputError({ type: 'error', message: 'Akses mikrofon ditolak. Izinkan akses mikrofon di pengaturan browser.' });
      }
    }
  }

  // When blob is ready, send it for identification
  // useEffect ensures this runs AFTER state has fully settled (not during render)
  const lastBlobRef = useRef(null);
  useEffect(() => {
    if (!recorder.audioBlob) return;
    if (recorder.isRecording) return;
    if (recorder.audioBlob === lastBlobRef.current) return;

    lastBlobRef.current = recorder.audioBlob;

    // Only reject truly empty recordings (< 1s = accidental tap)
    if (recorder.seconds < 1) {
      setInputError({ type: 'warning', message: 'Rekaman terlalu pendek — coba rekam beberapa kata.' });
      return;
    }

    setActiveAudioBlob(recorder.audioBlob);
    identifier.identify(recorder.audioBlob);
  }, [recorder.audioBlob, recorder.isRecording]);

  /* Upload handlers */
  function handleFileSelect(file) {
    if (!file) return;
    if (!isAudioFile(file)) {
      setInputError({ type: 'error', message: 'File harus berformat audio (mp3, wav, m4a, ogg, webm).' });
      return;
    }
    setInputError(null);
    identifier.reset();
    setSelectedVerse(null);
    recorder.reset();
    setActiveAudioBlob(file);
    identifier.identify(file);
  }

  function handleFileInputChange(e) {
    handleFileSelect(e.target.files?.[0]);
    e.target.value = '';
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    handleFileSelect(file);
  }, []);

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave() {
    setIsDragOver(false);
  }

  /* Verse selection */
  function handleVerseSelect(verse) {
    if (selectedVerse?.id === verse.id) {
      setSelectedVerse(null);
    } else {
      setSelectedVerse(verse);
      addToHistory(verse);
    }
  }

  /* Reset to idle */
  function handleReset() {
    recorder.reset();
    identifier.reset();
    setSelectedVerse(null);
    setInputError(null);
    setActiveAudioBlob(null);
    lastBlobRef.current = null;
    setShowOtherResults(false);
  }

  const showInput = !isProcessing && identifier.state !== 'results' && identifier.state !== 'zero_match';

  return (
    <>
      <div className="app" role="main">
        {/* Ambient glow overlay — decorative */}
        <div className="main-panel">

          {/* Header */}
          <header className="app-header">
            <div className="app-logo" aria-label="iq.lab">
              <div className="app-logo-mark" aria-hidden="true">
                <IconBook />
              </div>
              <span className="app-name">iq<span>.</span>lab</span>
            </div>
            <p className="app-tagline">ngaji interactively</p>
          </header>

          {/* Audio Input */}
          {showInput && (
            <section className="input-section" aria-label="Input audio">

              {/* Mic button */}
              <div className="mic-wrapper">
                <div className={`mic-pulse-ring${recorder.isRecording ? ' active' : ''}`} aria-hidden="true" />
                <button
                  className={`mic-button${recorder.isRecording ? ' recording' : ''}`}
                  onClick={handleMicClick}
                  disabled={isProcessing}
                  aria-label={recorder.isRecording ? 'Hentikan rekaman' : 'Mulai rekam'}
                  aria-pressed={recorder.isRecording}
                >
                  {recorder.isRecording ? <IconMicOff /> : <IconMic />}
                </button>
              </div>

              {recorder.isRecording ? (
                <span className="recording-timer" aria-live="polite" aria-label={`Waktu rekaman: ${formatTime(recorder.seconds)}`}>
                  {formatTime(recorder.seconds)}
                </span>
              ) : (
                <p className="mic-label">Ketuk untuk merekam bacaan</p>
              )}

              {/* Divider */}
              {!recorder.isRecording && (
                <>
                  <div className="input-divider" aria-hidden="true">
                    <span>atau</span>
                  </div>

                  {/* Upload zone */}
                  <label
                    className={`upload-zone${isDragOver ? ' dragover' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    aria-label="Unggah file audio"
                  >
                    <IconUpload />
                    <span>
                      Unggah file audio
                      <span className="upload-hint">mp3, wav, m4a, ogg, webm — maks. 10 menit</span>
                    </span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="audio/*"
                      className="upload-input"
                      onChange={handleFileInputChange}
                      aria-hidden="true"
                      tabIndex={-1}
                    />
                  </label>
                </>
              )}

              {/* Inline error */}
              {inputError && (
                <ErrorBanner type={inputError.type} message={inputError.message} />
              )}
            </section>
          )}

          {/* Processing */}
          {isProcessing && (
            <QueueIndicator
              audioBlob={activeAudioBlob}
              onCancel={() => { identifier.cancel(); handleReset(); }}
            />
          )}

          {/* Results */}
          {identifier.state === 'results' && (
            <>
              <section className="results-section" aria-label="Hasil pencocokan">
                <p className="results-heading">Kemungkinan Ayat</p>
                {/* High confidence results (>= 50%) */}
                {identifier.results.filter(v => v.confidence >= 0.5).map(verse => (
                  <VerseCard
                    key={verse.id}
                    verse={verse}
                    isSelected={selectedVerse?.id === verse.id}
                    onSelect={handleVerseSelect}
                    audioBlob={activeAudioBlob}
                  />
                ))}

                {/* Low confidence results (< 50%) */}
                {identifier.results.filter(v => v.confidence < 0.5).length > 0 && (
                  <div className="other-results-container">
                    <button
                      className="other-results-toggle"
                      onClick={() => setShowOtherResults(!showOtherResults)}
                      aria-expanded={showOtherResults}
                    >
                      {showOtherResults ? 'Sembunyikan hasil lain' : `Other results (${identifier.results.filter(v => v.confidence < 0.5).length})`}
                    </button>
                    
                    {showOtherResults && (
                      <div className="other-results-list animate-fade-in">
                        {identifier.results.filter(v => v.confidence < 0.5).map(verse => (
                          <VerseCard
                            key={verse.id}
                            verse={verse}
                            isSelected={selectedVerse?.id === verse.id}
                            onSelect={handleVerseSelect}
                            audioBlob={activeAudioBlob}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </section>
              <button className="try-again-btn" onClick={handleReset} style={{ alignSelf: 'center' }}>
                <IconRefresh /> Rekam Lagi
              </button>
            </>
          )}

          {/* Zero match */}
          {identifier.state === 'zero_match' && (
            <ZeroMatch onReset={handleReset} />
          )}

          {/* Network error */}
          {identifier.state === 'error' && (
            <>
              <ErrorBanner type="error" message="Gagal terhubung ke server. Periksa koneksi dan coba lagi." />
              <button className="try-again-btn" onClick={handleReset} style={{ alignSelf: 'center', marginTop: 'var(--sp-2)' }}>
                <IconRefresh /> Coba Lagi
              </button>
            </>
          )}

          {/* History */}
          <HistoryStrip history={history} />

        </div>
      </div>
    </>
  );
}
