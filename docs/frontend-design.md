# Resume Assistant — Desktop Frontend Design Brief (Google Stitch)

Use this document as the single source of truth when generating a **desktop web app screen** for the **Resume Assistant** application. The frontend connects to an existing **Flask** backend running locally (`web_app.py`, default port `5000`).

## Stitch instruction summary

Design **one polished desktop screen** at **1440 × 900**. Do **not** design mobile, login, upload, billing, onboarding, or admin screens. Focus on a high-quality recruiter-facing chat interface with a left file sidebar and a main assistant workspace.

---

## 1. Product summary

**Resume Assistant** is an AI-powered recruiting tool. Users ask questions in natural language; a **Groq** LLM agent (OpenAI-compatible API) calls file-system tools to read, list, search, and summarize resume files stored in a local `resumes/` folder. Generated summaries and exports are written to `output/`.

| Attribute | Value |
|-----------|--------|
| App name | Resume Assistant |
| Primary use | Manual testing + recruiter demo |
| Backend | Flask REST API (Python) |
| LLM provider | Groq (`llama-3.3-70b-versatile` or similar) |
| Auth | None (local dev tool) |
| Supported resume formats | PDF, DOCX, TXT |

**Important:** Resume filenames do **not** require a `resume_` prefix. Examples: `Giulia Gonzalez.pdf`, `resume_john_doe.pdf`, `jane_smith.docx`.

---

## 2. Target users

- **Recruiters / hiring managers** — screen candidates, search skills, generate summaries  
- **Developers** — test LLM tool-calling and file I/O locally  

---

## 3. Core user flows

### Flow A — Ask a custom question
1. User types a question in the chat composer (e.g. “Find resumes mentioning machine learning”).
2. User clicks **Send** (or Ctrl+Enter).
3. UI shows loading state (10–60 seconds typical).
4. Assistant reply appears in the chat thread.
5. **Output** file list refreshes if a summary was written.

### Flow B — One-click example query
1. User clicks a suggested query chip.
2. Chip text fills the composer (optional) and sends immediately.
3. Same loading → response flow as Flow A.

### Flow C — Browse files
1. User views **Resumes** and **Output** lists in the sidebar.
2. Each row shows: file type icon, filename, extension badge, size, last modified.
3. Optional enhancement: click a resume row to pre-fill composer with “Summarize {filename}” or “Search {filename} for …”.

### Flow D — Check system status
1. Status area shows: connected / disconnected, provider name, model name, API key configured.
2. If disconnected, show actionable message: “Start backend: `python web_app.py`”.

---

## 4. Desktop Screen To Generate

### Canvas

- **Target size:** 1440 × 900 desktop web app
- **Theme:** Dark mode only
- **Layout:** Full-height app shell with fixed sidebar and main chat workspace
- **No mobile variant needed right now**

### Required desktop layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ APP SHELL 1440 × 900                                                        │
├──────────────────────────────┬───────────────────────────────────────────────┤
│ LEFT SIDEBAR 320px           │ MAIN WORKSPACE                                │
│                              │                                               │
│ Logo + Resume Assistant      │ Top bar: page title + status pill             │
│ Subtext: Local AI resume QA  │                                               │
│                              │ Example query chips                           │
│ Status card                  │                                               │
│ Groq · model · Connected     │ Scrollable chat thread                         │
│                              │ - Assistant welcome card                       │
│ Resumes section              │ - User bubble                                  │
│ Search/filter input          │ - Assistant answer bubble                      │
│ File list cards              │ - Loading bubble state                         │
│                              │                                               │
│ Output section               │ Sticky bottom composer                         │
│ Generated summary files      │ Multiline input + Send button + Ctrl+Enter     │
└──────────────────────────────┴───────────────────────────────────────────────┘
```

### Desktop proportions

| Area | Size / behavior |
|------|------------------|
| App shell | 1440 × 900, full viewport |
| Sidebar | 320px fixed width, full height, scroll within sections |
| Main workspace | Remaining width, column layout |
| Top bar | 72px height |
| Chat thread | Flexible height, scrollable |
| Composer | Sticky bottom, about 120px height |

### Desktop wireframe details

1. **Left sidebar**
   - Top brand block: small bot/spark icon, “Resume Assistant”, subtitle “Local AI resume QA”.
   - Status card with green dot: `Groq · llama-3.3-70b-versatile · Connected`.
   - `Resumes` section with count badge, refresh icon button, and compact search/filter input.
   - Resume file cards showing icon, filename, extension badge, size, modified date.
   - `Output` section showing generated text summaries.

2. **Main top bar**
   - Title: “AI Resume Workspace”.
   - Subtitle: “Ask questions across local PDF, DOCX, and TXT resumes.”
   - Right side: compact backend status pill and “Local Flask API” label.

3. **Main chat area**
   - Empty state card at top if no messages: “Ask the assistant to read, search, or summarize resumes.”
   - Four example query chips in a horizontal wrap row.
   - Chat bubbles below; user bubbles align right, assistant bubbles align left.
   - Assistant responses should support long readable text.

4. **Bottom composer**
   - Multiline input with placeholder: “Ask about skills, experience, or create a summary…”
   - Primary Send button on the right.
   - Secondary hint below input: “Ctrl+Enter to send”.
   - Loading state: disabled Send button, text “Thinking…”, subtle animated dots.

---

## 5. Desktop States To Include

Show these states within the desktop design, either as separate frames or clearly represented component states:

| Screen / state | Description |
|----------------|-------------|
| **Default (empty chat)** | Welcome message + 4 example query chips + hint text |
| **Chat in progress** | User message visible; assistant area shows loading skeleton or “Thinking…” |
| **Chat complete** | Full assistant response (long text, scrollable) |
| **API error** | Inline error card: missing API key, network failure, server 500 |
| **Empty resumes** | Illustration + “Add PDF, DOCX, or TXT files to the resumes/ folder” |
| **Empty output** | “No generated files yet. Ask the assistant to create a summary.” |
| **Offline backend** | Banner: cannot reach `http://127.0.0.1:5000` |

---

## 6. Example queries (chip labels)

Use these exact strings for quick-action buttons:

| Label | Query sent to API |
|-------|-------------------|
| Read all resumes | `Read all resumes in the resumes folder` |
| Find Python experience | `Find resumes mentioning Python experience` |
| Summarize John Doe PDF | `Create a summary file for resume_john_doe.pdf` |
| List resume files | `list the files in the resumes folder` |

**Enhancement (optional in design):** Dynamic chip “Summarize {selected file}” when user selects a row in the resumes list.

---

## 7. Visual design direction

### Mood & tone
- Professional HR / recruiting SaaS  
- Trustworthy, calm, efficient — not playful or consumer-social  

### Color palette (dark mode — primary)

| Token | Hex | Usage |
|-------|-----|--------|
| `bg-app` | `#0f1419` | Page background |
| `bg-surface` | `#1a2332` | Cards, sidebar, panels |
| `border` | `#2a3648` | Dividers, input borders |
| `text-primary` | `#e7ecf3` | Body text |
| `text-muted` | `#9aa8b8` | Labels, metadata |
| `accent` | `#3b82f6` | Primary buttons, links |
| `accent-hover` | `#2563eb` | Button hover |
| `success` | `#7dd3a8` | Connected status |
| `error` | `#f87171` | Errors, disconnected |

### Light mode
Do not create a light mode variant right now. Dark mode is required.

### Typography
- **UI:** Inter, system-ui, or similar sans-serif  
- **File paths / code snippets:** JetBrains Mono or ui-monospace  
- Scale: H1 28px, section title 14px semibold, body 15–16px, meta 13px  

### Spacing & shape
- Border radius: 8px inputs, 10px cards  
- Padding: 16–24px panels, 12px list items  
- Sidebar padding: 20px
- Main workspace padding: 24px
- Chat max width: 840px within main workspace

### Icons
- PDF → red/document icon  
- DOCX → blue/document icon  
- TXT → gray/document icon  
- Assistant → sparkles or bot avatar circle  
- User → person or initials avatar  

---

## 8. Component specifications

### 8.1 Connection status pill
- **Connected:** green dot + `Groq · {model} · Connected`  
- **No API key:** red/amber + `GROQ_API_KEY not configured`  
- **Offline:** red + `Backend unreachable`  

Data from `GET /api/health`:
```json
{
  "status": "ok",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "api_key_configured": true
}
```

### 8.2 File list item
| Element | Source field |
|---------|----------------|
| Title | `filename` |
| Subtitle | `{extension} · {size_bytes} bytes · modified {modified_at}` |
| Path (tooltip) | `filepath` e.g. `resumes/Giulia Gonzalez.pdf` |

Desktop visual requirements:
- PDF badge: red-tinted
- DOCX badge: blue-tinted
- TXT badge: gray-tinted
- Active/selected file row: subtle blue border and darker selected background
- Long filenames truncate with ellipsis, full path in tooltip

### 8.3 Chat bubble — user
- Right-aligned, accent background, white text, rounded corners  

### 8.4 Chat bubble — assistant
- Left-aligned, surface background, border, supports **long markdown-like prose** (plain text is fine)  

### 8.5 Composer
- Multiline textarea (min 3 rows, max ~8 rows auto-grow)  
- Primary **Send** button; disabled while loading  
- Secondary hint: `Ctrl+Enter to send`  
- Composer must be sticky at the bottom of the main workspace

### 8.6 Example query chips
- Outlined or soft-filled pills, wrap on small screens  
- Hover state; disabled during loading  

### 8.7 Loading indicator
- Text: “Thinking…” or skeleton in assistant bubble  
- Do not block entire page — only composer + chips disabled  

---

## 9. API contract (for developer handoff)

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Response |
|--------|----------|----------|
| `GET` | `/api/health` | `{ status, provider, model, api_key_configured }` |
| `GET` | `/api/resumes` | Array of file objects (see below) |
| `GET` | `/api/output` | Array of file objects |
| `POST` | `/api/chat` | Body: `{ "query": "string" }` → `{ "answer": "string" }` or `{ "error": "string" }` with 4xx/5xx |

**File object shape:**
```json
{
  "filename": "Giulia Gonzalez.pdf",
  "filepath": "resumes/Giulia Gonzalez.pdf",
  "extension": ".pdf",
  "size_bytes": 45231,
  "modified_at": "2026-05-24T14:32:00"
}
```

**Chat request example:**
```json
POST /api/chat
{ "query": "Find resumes mentioning Python experience" }
```

**Chat success response:**
```json
{ "answer": "Two resumes mention Python: ..." }
```

---

## 10. Sample content for mockups

### Resumes list
- `Giulia Gonzalez.pdf` — 81 KB — PDF  
- `resume_jane_smith.docx` — 37 KB — DOCX  
- `resume_alice_wang.txt` — 829 B — TXT  

### Output list
- `summary_john_doe.txt` — 181 B — TXT  

### Sample user message
> Find resumes mentioning machine learning experience

### Sample assistant response
> I searched all resumes in the folder. **Alice Wang** and **John Doe** mention machine learning or related skills. Jane Smith’s resume focuses on product management without ML keywords.  
>  
> Would you like a detailed summary of either candidate?

---

## 11. Accessibility

- Minimum contrast ratio **4.5:1** for body text on dark backgrounds  
- Visible focus rings on buttons, chips, textarea  
- `aria-live="polite"` region for new assistant messages  
- `prefers-reduced-motion`: replace spinner with static “Thinking…” text  
- Filenames with spaces: full name in `title` tooltip if truncated  
- Keyboard-accessible sidebar file rows and example query chips

---

## 12. Out of scope (do not design)

- Mobile layout or responsive screens for this request
- User login / registration / SSO  
- Billing, subscriptions, team management  
- Cloud deployment or environment switcher  
- Resume upload UI (files are added to `resumes/` on disk manually)  
- In-browser PDF viewer (optional future enhancement only)  

---

## 13. Deliverables checklist for Stitch

- [ ] One desktop layout (1440 × 900)  
- [ ] Component set: status pill, file row, chat bubbles, chips, composer, error banner  
- [ ] Design tokens (color, type, spacing, radius)  
- [ ] All states: empty, loading, success, error, offline  
- [ ] Dark mode (required)  
- [ ] No mobile or light-mode screens for now

---

## 14. Paste-Ready Google Stitch Prompt

Design one polished **desktop-only** web app screen (1440 × 900) for **Resume Assistant**, a local AI recruiting tool. Use a dark professional HR SaaS style. Left sidebar is 320px wide with brand header, Groq connection status, scrollable resume files (PDF/DOCX/TXT with icons, extension badges, file size, modified date), and output summary files. Main workspace has a top bar titled “AI Resume Workspace”, example query chips, a scrollable chat thread with user and assistant bubbles, and a sticky bottom composer with multiline input, Send button, Ctrl+Enter hint, and loading state. Color palette: app background `#0f1419`, surface `#1a2332`, border `#2a3648`, primary text `#e7ecf3`, muted text `#9aa8b8`, blue accent `#3b82f6`, green connected status, red error state. Include empty chat, loading, success response, API error, empty resumes, empty output, and offline backend states. REST API context: `GET /api/health`, `GET /api/resumes`, `GET /api/output`, `POST /api/chat` with `{query}`. Do not design mobile, login, upload, billing, admin, or light mode.

---

*Document version: 1.1 — desktop-only Stitch brief aligned with `web_app.py`, `llm_file_assistant.py`, and `fs_tools.py`.*
