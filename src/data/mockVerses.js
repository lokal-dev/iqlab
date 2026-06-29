// Mock Quran data for UI development
// In production: fetched from FastAPI backend → pgvector search results
//
// Uthmani waqf signs included in tajweedHtml:
//   م  = Waqf Lazim  (WAJIB berhenti)
//   ج  = Waqf Jaiz   (boleh berhenti atau lanjut)
//   صلى = Wasl Awla  (lebih baik lanjut)
//   قلى = Waqf Awla  (lebih baik berhenti)
//   لا  = La Waqf    (JANGAN berhenti)
//   ط   = Waqf Mutlak (berhenti sempurna)
//   ۝  = Tanda akhir ayat

export const MOCK_RESULTS = [
  {
    id: 1,
    surahNumber: 1,
    surahName: 'Al-Fatihah',
    surahNameAr: 'الفاتحة',
    ayahNumber: 1,
    arabicText: 'بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ',
    // tajweedHtml: full Uthmani text with tajweed spans + waqf marks
    tajweedHtml:
      'بِسْمِ ٱللَّهِ ' +
      '<span class="tj-madd">ٱلرَّحْمَـٰنِ</span> ' +
      '<span class="tj-madd">ٱلرَّحِيمِ</span>' +
      '<span class="waqf waqf-ayah" data-waqf="ayah" title="Akhir ayat">۝١</span>',
    translation: 'Dengan nama Allah Yang Maha Pengasih, Maha Penyayang.',
    confidence: 0.94,
  },
  {
    id: 2,
    surahNumber: 1,
    surahName: 'Al-Fatihah',
    surahNameAr: 'الفاتحة',
    ayahNumber: 2,
    arabicText: 'ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ',
    tajweedHtml:
      '<span class="tj-idgham">ٱلْحَمْدُ</span> لِلَّهِ رَبِّ ' +
      '<span class="tj-madd">ٱلْعَـٰلَمِينَ</span>' +
      '<span class="waqf waqf-ayah" data-waqf="ayah" title="Akhir ayat">۝٢</span>',
    translation: 'Segala puji bagi Allah, Tuhan semesta alam.',
    confidence: 0.81,
  },
  {
    id: 3,
    surahNumber: 112,
    surahName: 'Al-Ikhlas',
    surahNameAr: 'الإخلاص',
    ayahNumber: 1,
    arabicText: 'قُلْ هُوَ ٱللَّهُ أَحَدٌ',
    tajweedHtml:
      '<span class="tj-qalqalah">قُلْ</span> هُوَ ٱللَّهُ ' +
      '<span class="tj-ikhfa">أَحَدٌ</span>' +
      '<span class="waqf waqf-ayah" data-waqf="ayah" title="Akhir ayat">۝١</span>',
    translation: 'Katakanlah (Muhammad), "Dialah Allah, Yang Maha Esa."',
    confidence: 0.72,
  },
];

// Waqf sign definitions for the legend
export const WAQF_SIGNS = [
  { sign: 'م',   cls: 'waqf-lazim',  label: 'Wajib berhenti',      desc: 'Waqf Lazim — harus berhenti di sini' },
  { sign: 'ط',   cls: 'waqf-mutlak', label: 'Berhenti sempurna',    desc: 'Waqf Mutlak — berhenti penuh' },
  { sign: 'ج',   cls: 'waqf-jaiz',   label: 'Boleh berhenti',       desc: 'Waqf Jaiz — berhenti atau lanjut sama-sama boleh' },
  { sign: 'صلى', cls: 'waqf-wasl',   label: 'Lebih baik lanjut',    desc: 'Wasl Awla — dianjurkan menyambung' },
  { sign: 'قلى', cls: 'waqf-waqfa',  label: 'Lebih baik berhenti',  desc: 'Waqf Awla — dianjurkan berhenti' },
  { sign: 'لا',  cls: 'waqf-mamnu',  label: 'Jangan berhenti',      desc: 'La Waqf — dilarang berhenti di sini' },
  { sign: '۝',  cls: 'waqf-ayah',   label: 'Akhir ayat',           desc: 'Tanda akhir ayat — berhenti di sini' },
];

/**
 * Strips all HTML spans and waqf marks, returns clean Arabic + reference.
 * Used for clipboard copy.
 */
export function extractCleanArabic(verse) {
  const div = document.createElement('div');
  div.innerHTML = verse.tajweedHtml;
  // Remove waqf spans (they carry the mark characters we don't want in copy)
  div.querySelectorAll('.waqf').forEach(el => el.remove());
  const cleanText = (div.textContent || div.innerText || verse.arabicText).trim();
  return `${cleanText}\n— ${verse.surahName} : ${verse.ayahNumber}`;
}
