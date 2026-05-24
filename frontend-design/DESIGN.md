---
name: Resume Assistant
colors:
  surface: '#0f1419'
  surface-dim: '#0f1419'
  surface-bright: '#353a3f'
  surface-container-lowest: '#0a0f14'
  surface-container-low: '#171c21'
  surface-container: '#1b2025'
  surface-container-high: '#252a30'
  surface-container-highest: '#30353b'
  on-surface: '#dee3ea'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dee3ea'
  inverse-on-surface: '#2c3136'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#bec7db'
  on-secondary: '#283140'
  secondary-container: '#3e4758'
  on-secondary-container: '#acb5c9'
  tertiary: '#bbc7de'
  on-tertiary: '#253143'
  tertiary-container: '#8591a7'
  on-tertiary-container: '#1e2a3c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#dae3f7'
  secondary-fixed-dim: '#bec7db'
  on-secondary-fixed: '#131c2a'
  on-secondary-fixed-variant: '#3e4758'
  tertiary-fixed: '#d7e3fb'
  tertiary-fixed-dim: '#bbc7de'
  on-tertiary-fixed: '#101c2d'
  on-tertiary-fixed-variant: '#3b475a'
  background: '#0f1419'
  on-background: '#dee3ea'
  surface-variant: '#30353b'
  text-primary: '#e7ecf3'
  text-muted: '#9aa8b8'
  success-green: '#7dd3a8'
  error-red: '#f87171'
  accent-hover: '#2563eb'
  pdf-badge: '#ef4444'
  docx-badge: '#3b82f6'
  txt-badge: '#64748b'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  meta-xs:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar-width: 320px
  topbar-height: 72px
  composer-min-height: 120px
  container-max-width: 840px
  gutter: 16px
  margin-page: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
---

## Brand & Style

The brand personality for the design system is **Professional, Technical, and Reliable**. As an AI-powered tool for recruiters and developers, the interface prioritizes efficiency and clarity over decorative flair. 

The design style is **Corporate Modern with a Developer-Centric edge**, characterized by a deep dark-mode palette, high-information density, and precise structural alignment. It draws inspiration from modern IDEs and sophisticated SaaS platforms, utilizing subtle tonal layering and crisp borders to define the workspace without creating visual noise. The emotional response should be one of "calm control" — the user should feel that the AI is a precise tool under their command.

**Key Visual Principles:**
- **Information Density:** Prioritize legibility of data (filenames, dates, sizes) over large whitespace.
- **Systemic Feedback:** Use distinct color states for backend connectivity and AI processing.
- **Monochromatic Core:** Lean heavily on the blue-gray scale, using the primary blue accent only for intentional action or focus.

## Colors

The color palette is architected for a high-contrast dark environment that reduces eye strain during long screening sessions.

- **Foundational Neutrals:** The `bg-app` (`#0f1419`) serves as the base layer, while `bg-surface` (`#1a2332`) is used for elevated containers like cards and the sidebar.
- **Accents & Semantics:** The primary blue (`#3b82f6`) is reserved for the most important calls to action. Success and error states use high-vibrancy green and red for immediate recognition of backend status.
- **Content Hierarchy:** Typography follows a strict hierarchy where `text-primary` handles core information and `text-muted` manages metadata, timestamps, and secondary labels.
- **File Tagging:** Specific colors are assigned to file extensions (PDF, DOCX, TXT) to allow for rapid visual scanning of the file list.

## Typography

The typography system relies on **Inter** for its exceptional legibility in UI contexts and **JetBrains Mono** for technical metadata and file paths.

- **Hierarchy:** Headlines use a tighter letter-spacing to appear more grounded. Body text uses a generous line height (1.6x) to ensure the AI's long-form markdown responses are easy to digest.
- **Labels:** Small caps with increased letter spacing are used for sidebar section headers (e.g., "RESUMES") to provide clear boundaries without using heavy lines.
- **Code/Technical:** Technical status and file paths should always use the monospaced font to maintain character alignment and a "pro-tool" aesthetic.

## Layout & Spacing

This design system utilizes a **Fixed Sidebar + Fluid Workspace** model.

- **Sidebar:** Fixed at 320px. It contains its own internal scroll areas for the file lists.
- **Main Workspace:** A fluid area that centers the chat content at a maximum width of 840px to maintain optimal line length for reading.
- **Spacing Rhythm:** An 8px-based grid governs the spacing. 16px is the standard gutter for card internals, while 24px is used for major page margins and section gaps.
- **Sticky Elements:** The Top Bar and the Chat Composer are fixed in place, with the chat thread scrolling in the area between them.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** rather than heavy shadows.

- **Level 0 (Base):** `#0f1419` used for the page background and chat thread area.
- **Level 1 (Surface):** `#1a2332` used for the sidebar, top bar, and individual cards.
- **Level 2 (Interaction):** `#2a3648` used for hover states on list items and input field backgrounds.
- **Outlines:** Low-contrast borders (`#2a3648`) are used to define the edges of all surface containers, providing a structural look that feels stable and organized.
- **Shadows:** Only used for the bottom composer to indicate it sits above the scrolling chat thread. Use a subtle, large-radius shadow: `0px -4px 20px rgba(0, 0, 0, 0.4)`.

## Shapes

The design uses a **Hybrid Roundedness** strategy to balance approachability with a professional tool aesthetic.

- **Standard Radius (10px):** Applied to all primary cards, chat bubbles, and major panels.
- **Input Radius (8px):** A slightly tighter radius for textareas, chips, and buttons to differentiate interactive elements from static containers.
- **Full Radius (Pill):** Used exclusively for status badges and example query chips to make them feel distinct as "tappable" or "indicator" items.

## Components

### Buttons & Chips
- **Primary Button:** Solid blue background (`#3b82f6`) with white text. 8px radius.
- **Example Chips:** Outlined with `#2a3648`, using a soft blue tint on hover. Pill-shaped.
- **Status Badge:** Small pill-shaped badges with subtle background tints and high-contrast text for file extensions.

### Chat Interface
- **User Bubbles:** Right-aligned, primary blue background, `headline-md` equivalent text color.
- **Assistant Bubbles:** Left-aligned, `bg-surface` background with a subtle border. These must support Markdown (bolding, lists, line breaks).
- **Composer:** A multiline textarea that expands vertically. Background is `#0f1419` to contrast against the `#1a2332` surface it sits on.

### Sidebar File Cards
- **Structure:** 3-column layout: [Icon] [Filename + Meta] [Status/Badge].
- **States:** Hovering a file card should transition the background to `#2a3648`. Selected files receive a left-side 2px blue border accent.

### Status Indicators
- **Connection Pill:** A dot icon (pulsing green when active) followed by monospaced text.
- **Loading:** In the assistant bubble, use a sequence of three bouncing dots or a "Thinking..." text string in `text-muted`.