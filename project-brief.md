# Project Brief: iq.lab
*ngaji interactively*

## 1. Executive Summary
This project brief outlines the concept, technical design, and infrastructure readiness for **iq.lab**, an audio-driven Quranic application. Designed as a friendly, non-judgmental companion, the app allows users to search for specific verses using voice or audio file uploads and receive gentle, supportive feedback on their recitation.

---

## 2. Brand Identity & Product Tone
*   **Name:** iq.lab (Interactive Quran Laboratory)
*   **Tagline:** `ngaji interactively`
*   **Vibe:** Empathetic, modern, and supportive. It eliminates the fear of judgment, acting as an automated peer rather than a strict tester.

---

## 3. Technical Architecture
To maintain text accuracy and manage operational costs, the architecture bypasses generative LLMs for the search process, using a fast and deterministic hybrid pipeline:

1.  **Audio Input Layer:** Audio from the mic or file upload is received by the backend framework.
2.  **Transcription Engine (ASR):** An optimized open-source model, *Tadabur-Whisper-Small*, converts the classical recitation into text.
3.  **Data & Search Layer:** Text is checked against an immutable database of 6,236 verses using *PostgreSQL* and the *pgvector* extension.

---

## 4. Infrastructure Blueprint (Low-Cost VPS)
The application is specifically optimized to operate smoothly on a resource-constrained virtual private server (1 Core CPU, 4GB RAM, 500GB Disk):

| Component | Optimization Strategy | Memory Footprint |
| :--- | :--- | :--- |
| **Operating System** | Lean Linux/Ubuntu environment with a 4GB Swap file active safety buffer. | ~400 MB |
| **Database Layer** | PostgreSQL equipped with the native `pgvector` extension for similarity search. | ~300 MB |
| **ASR Engine** | `faster-whisper` runtime running via CTranslate2 using `int8` quantization. | ~500 MB |
| **API & App Layer** | Asynchronous FastAPI backend locked strictly to 1 CPU thread. | ~100 MB |

> **Operational Insight:** The baseline memory consumption is roughly 1.3 GB, leaving plenty of RAM headroom on a 4GB machine.

---

## 5. Key Challenges & UI Solutions
*   **The Concurrency Bottleneck:** With 1 CPU core, concurrent processing will cause requests to lock. 
    *   *Solution:* Implement an asynchronous FIFO (First-In, First-Out) request queue combined with a typing-indicator UI component to buffer wait times seamlessly.
*   **Short Clip Uncertainty:** Brief audio fragments yield high-entropy cross-references. 
    *   *Solution:* Present the top 3 or 4 highest confidence matches as an interactive choice grid instead of a single definitive output.
*   **Dialect Tolerances:** Strict acoustic targets discourage casual learners. 
    *   *Solution:* Calibrate the matching layer to look past minor regional phonetic variations (*lidah Indo*) unless it changes the verse definition.
