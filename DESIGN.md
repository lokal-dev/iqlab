---
name: iq.lab
description: ngaji interactively
colors:
  primary: "#e5a21e"
  neutral-bg: "#0d0b17"
  bg-surface: "#161322"
  bg-elevated: "#201c2e"
  bg-overlay: "#2a253a"
  border-subtle: "#3a334f"
  border-strong: "#5e4d84"
  ink-primary: "#f7f6f9"
  ink-secondary: "#b2aac8"
  ink-muted: "#7f7697"
  accent-gold: "#e5a21e"
  accent-indigo: "#8270cd"
  semantic-error: "#d62d3a"
  semantic-warning: "#dca026"
  semantic-success: "#62b36b"
typography:
  display:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(2rem, 5vw, 3rem)"
    fontWeight: 700
    lineHeight: 1.1
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "6px"
  md: "12px"
  lg: "20px"
  xl: "28px"
  full: "9999px"
spacing:
  sp-1: "4px"
  sp-2: "8px"
  sp-3: "12px"
  sp-4: "16px"
  sp-5: "20px"
  sp-6: "24px"
  sp-8: "32px"
  sp-10: "40px"
  sp-12: "48px"
  sp-16: "64px"
  sp-20: "80px"
components:
  button-primary:
    backgroundColor: "{colors.accent-gold}"
    textColor: "{colors.neutral-bg}"
    rounded: "{rounded.full}"
    padding: "8px 16px"
---

# Design System: iq.lab

## 1. Overview

**Creative North Star: "The Quran Laboratory"**

iq.lab is a modern Quranic verse identification interface that acts as an automated, empathetic peer. The design language merges clean, technical dark-mode grids and precise waveforms with classical, elegant Arabic typography. Spacing follows a strict 8pt grid, and visual boundaries rely on subtle tonal shifts rather than high-contrast dividing lines.

Delight is achieved through smooth, micro-reactive states: buttons scale and glow, audio waveform trackers glide organically, and Quranic words transition smoothly through colors as playback progresses. The system rejects neon-rainbow gradients, complex authenticated dashboards, and aggressive layout shifts.

**Key Characteristics:**
- Dark Mode by Default: Deep purple-black base with gold and indigo accents.
- Typographic Focus: High contrast for Arabic Uthmani scripts paired with clean sans-serif Latin UI elements.
- Fluid Reactive Transitions: 150-250ms exponential easing on interactive state changes.
- Responsive task layout: Main content card scales smoothly, collapsing to compact lists on mobile viewports.

---

## 2. Colors

Colors follow a Restrained strategy. The primary gold accent is applied to active playback, makhraj success states, and key interactive highlights only.

### Neutral
- **Deep base background** (`#0d0b17` / `oklch(0.10 0.025 270)`): Primary screen backing.
- **Card surface** (`#161322` / `oklch(0.14 0.022 270)`): Base card containers.
- **Elevated surface** (`#201c2e` / `oklch(0.18 0.020 270)`): Dropdowns, hover states, and details panels.
- **Border subtle** (`#3a334f` / `oklch(0.28 0.030 270)`): Default borders and layout divisions.

### Accent
- **Aura Gold** (`#e5a21e` / `oklch(0.75 0.135 85)`): Audio active indicators, focus highlights, and makhraj letters.
- **Muted Indigo** (`#8270cd` / `oklch(0.58 0.175 275)`): Secondary actions, inactive progress tracks, and decorative labels.

### Semantic
- **Makhraj Success** (`#62b36b` / `oklch(0.68 0.150 155)`): Correct pronunciation.
- **Makhraj Warning** (`#dca026` / `oklch(0.73 0.155 70)`): Minor pronunciation checks.
- **Makhraj Error** (`#d62d3a` / `oklch(0.62 0.200 25)`): Incorrect pronunciation.

**The Golden Rarity Rule.** The primary gold accent must carry less than 10% of any given screen area. Its visual weight is preserved by keeping the surrounding canvas dark and neutral.

---

## 3. Typography

**Display Font:** 'Inter', sans-serif  
**Body Font:** 'Inter', sans-serif  
**Arabic Font:** 'Noto Naskh Arabic', 'Amiri', serif  
**Arabic UI Font:** 'Noto Sans Arabic', sans-serif  

The typography pairing contrasts a highly geometric Latin UI font (Inter) with the flowing, diacritic-rich classical Naskh script for Quranic verses.

### Hierarchy
- **Display** (Bold, `clamp(2rem, 5vw, 3rem)`, `1.1`): Brand headings and large hero callouts.
- **Headline** (Semi-Bold, `1.5rem`, `1.2`): Page titles and card headers.
- **Arabic Verse** (Regular, `clamp(1.375rem, 3.5vw, 1.875rem)`, `2.0`): Quranic script. Line height is expanded to prevent diacritic clipping.
- **Body** (Regular, `1rem`, `1.5`): Translations, notes, and general UI copy (max length 70ch).
- **Label** (Medium, `0.875rem`, letter-spacing `0.02em`): Badges, tooltips, and state labels.

**The Diacritic Breathing Room Rule.** Any element rendering Uthmani Arabic script must have a line-height of at least `2.0` and relative padding to prevent combining characters (harakat) from clipping adjacent rows.

---

## 4. Elevation

iq.lab is flat and container-based at rest. Depth is communicated using tonal layering and subtle, colored back-glows.

### Shadow Vocabulary
- **Card Hover Glow** (`0 0 32px oklch(0.75 0.135 85 / 0.1)`): Applied to selected verse cards.
- **Active State Shadow** (`0 4px 16px oklch(0 0 0 / 0.55)`): Applied to active modals and dropdowns.

**The Glowing Interactive Rule.** Shadows are never static. They act strictly as a response to interactive state changes (hover, selection, or playback).

---

## 5. Components

### Buttons
- **Shape:** Full pill shape (radius `9999px`).
- **Primary Play Button:** Gold background, transparent border, deep base text.
- **Circular Replay Control:** 26px circle with a `1.5px` border-color of gold, background transparent at rest.
- **State Changes:** Hover triggers scale `1.08` and subtle gold glow. Active/playing state fills the circle with solid gold and flips the icon to dark.

### Cards
- **Shape:** Rounded corners (radius `12px`).
- **Border:** `1px` border subtle (`#3a334f`).
- **Background:** Card surface (`#161322`).
- **State Changes:** Hover scales card border slightly. Selection changes border to gold, expands the makhraj grading details panel, and activates the hover glow shadow.

### Inputs / Uploaders
- **Style:** Drag-and-drop zone with a dashed border subtle (`#3a334f`) and radius `12px`.
- **Focus / Drag Over:** Border changes to gold, and background darkens to deep base.

---

## 6. Do's and Don'ts

### Do:
- **Do** wrap every Arabic letter and its accompanying diacritics (harakat) in the same HTML `makhraj-highlight` span to ensure cohesive coloring.
- **Do** use a minimum `line-height: 2.0` on all Quranic verses to prevent diacritics from overlapping.
- **Do** transition word highlighting during audio playback sequentially from right-to-left using `oklch` transitions.

### Don't:
- **Don't** use neon-colored gradients for headers or text clips.
- **Don't** use sharp square corners for cards or buttons; keep them rounded (`12px` or `full`).
- **Don't** add side-stripe borders (e.g. `border-left: 4px solid gold`) on active cards; rely on full borders and gold back-glows.
