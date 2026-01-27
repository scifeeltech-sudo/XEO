# UI Layout Redesign Plan

## Overview
PostEditor 컴포넌트의 레이아웃을 개선하여 데스크톱과 모바일에서 더 나은 UX를 제공합니다.

## Current Issues
1. 두 Suggestion 박스(Post Suggestion, AI Personalized)가 입력 영역에 섞여 있음
2. 페르소나 선택기가 두 박스에 중복 존재
3. 모바일에서 정보 과부하

## Target File
`frontend/src/components/editor/PostEditor.tsx`

---

## Desktop Layout (≥1024px)

### Structure: 3-Row Layout

```
┌─────────────────┬─────────────────┐
│ INPUT           │ ANALYSIS        │  Row 1
│ - Post type     │ - Radar Chart   │
│ - Reset button  │ - Quick Tips    │
│ - URL input     │ - Apply button  │
│ - Content       │                 │
│ - Analyze btn   │                 │
└─────────────────┴─────────────────┘
┌─────────────────────────────────────┐
│ TARGET POST PREVIEW (200자)          │  Row 2
│ Full metrics + Opportunity Score    │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ PERSONA SELECTOR (unified)          │  Row 3
│ [😊 Empathetic][🔥 Contrarian]...   │
│ ┌────────────────┬────────────────┐ │
│ │ ✨ Suggestion  │ 🤖 Personalized│ │
│ │ (from tips)    │ (auto-gen)     │ │
│ └────────────────┴────────────────┘ │
└─────────────────────────────────────┘
```

---

## Mobile Layout (<1024px)

### Structure: Single Column with Collapsible Sections + Tabs

```
┌─────────────────────────┐
│ [My Post][Reply][Quote] │
│ [Reset]                 │
├─────────────────────────┤
│ Target URL [_________]  │
├─────────────────────────┤
│ TARGET PREVIEW (1줄 50자)│
│ @user: "text..."        │
│ ❤️1K 🔁234 💬56         │
├─────────────────────────┤
│ Content [__________]    │
│ [🔍 Analyze]            │
├─────────────────────────┤
│ 📊 Score: 72/100 ▼      │  ← Collapsible
├─────────────────────────┤
│ 💡 Tips (2 selected) ▼  │  ← Collapsible
│ [✨ Apply Tips]         │
├─────────────────────────┤
│ [😊][🔥][🌱][🎓]        │  ← Unified persona
├─────────────────────────┤
│ [✨ Suggestion][🤖 AI]  │  ← Tab switcher
│ ┌─────────────────────┐ │
│ │ Generated content   │ │
│ └─────────────────────┘ │
│ [Polish▼][Trans▼][Copy] │  ← Dropdowns
└─────────────────────────┘
```

---

## Implementation Details

### 1. New State Variables

```tsx
// Tab for mobile suggestion switching
const [activeTab, setActiveTab] = useState<"suggestion" | "personalized">("personalized");

// Collapsible sections for mobile
const [expandedSections, setExpandedSections] = useState({
  score: false,
  tips: true,
});

// Dropdown menus for mobile
const [showPolishMenu, setShowPolishMenu] = useState(false);
const [showTranslateMenu, setShowTranslateMenu] = useState(false);
```

### 2. Remove Duplicate State

```tsx
// REMOVE: suggestionPersona (use selectedPersona for both)
// Before: const [suggestionPersona, setSuggestionPersona] = useState<PersonaType | null>(null);
// After: Use selectedPersona for both suggestion panels
```

### 3. Layout Structure Change

```tsx
// Current
<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
  {/* Left column: inputs + suggestions */}
  {/* Right column: analysis */}
</div>

// New
<div className="flex flex-col gap-6">
  {/* Row 1: Input + Analysis (2-col on desktop) */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
    {/* Input section */}
    {/* Analysis section */}
  </div>

  {/* Row 2: Target Preview (full width) */}
  {/* Show only when postType !== "original" && targetPostContext */}

  {/* Row 3: Suggestions (full width) */}
  {/* Unified persona selector + side-by-side panels */}
</div>
```

### 4. Target Preview - Responsive Content Length

```tsx
{/* Content text - responsive */}
<p className="text-gray-300 mb-3">
  {/* Mobile: 50 chars */}
  <span className="lg:hidden">
    {text.length > 50 ? text.slice(0, 50) + "..." : text}
  </span>
  {/* Desktop: 200 chars (unchanged) */}
  <span className="hidden lg:inline">
    {text.length > 200 ? text.slice(0, 200) + "..." : text}
  </span>
</p>

{/* Opportunity Score - desktop only */}
<div className="hidden lg:block mt-3 pt-3 border-t border-gray-700">
  {/* existing opportunity score UI */}
</div>
```

### 5. Unified Persona Selector

```tsx
{/* Single persona selector - applies to both suggestions */}
<div className="mb-4 p-3 bg-gray-700/50 rounded-lg">
  <span className="text-gray-300 text-sm block mb-2">
    Choose Your Voice:
  </span>
  <div className="flex flex-wrap gap-2">
    {personas.map((persona) => (
      <button
        key={persona.id}
        onClick={() => setSelectedPersona(
          selectedPersona === persona.id ? null : persona.id
        )}
        className={`px-3 py-2 rounded-lg text-sm flex items-center gap-2 ${
          selectedPersona === persona.id
            ? "bg-blue-600 text-white ring-2 ring-blue-400"
            : "bg-gray-700 text-gray-300 hover:bg-gray-600"
        }`}
      >
        <span>{persona.icon}</span>
        <span className="hidden sm:inline">{persona.name}</span>
      </button>
    ))}
  </div>
</div>
```

### 6. Mobile Tab Switcher

```tsx
{/* Mobile: Tab switcher */}
<div className="flex lg:hidden border-b border-gray-700 mb-4">
  <button
    onClick={() => setActiveTab("suggestion")}
    className={`flex-1 py-3 text-center ${
      activeTab === "suggestion"
        ? "border-b-2 border-blue-500 text-blue-400"
        : "text-gray-500"
    }`}
  >
    ✨ Suggestion
  </button>
  <button
    onClick={() => setActiveTab("personalized")}
    className={`flex-1 py-3 text-center ${
      activeTab === "personalized"
        ? "border-b-2 border-purple-500 text-purple-400"
        : "text-gray-500"
    }`}
  >
    🤖 AI Post
  </button>
</div>

{/* Desktop: Side by side */}
<div className="hidden lg:grid lg:grid-cols-2 gap-4">
  {/* Post Suggestion */}
  {/* AI Personalized */}
</div>

{/* Mobile: Show based on active tab */}
<div className="lg:hidden">
  {activeTab === "suggestion" && suggestion && (
    {/* Post Suggestion content */}
  )}
  {activeTab === "personalized" && (
    {/* AI Personalized content */}
  )}
</div>
```

### 7. Collapsible Section Component

```tsx
function CollapsibleSection({
  title,
  isExpanded,
  onToggle,
  children,
  summary
}: {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  summary?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-xl overflow-hidden">
      {/* Mobile: Collapsible header */}
      <button
        onClick={onToggle}
        className="lg:hidden w-full flex justify-between items-center p-4"
      >
        <span className="font-semibold text-white">{title}</span>
        <div className="flex items-center gap-2">
          {summary && <span className="text-gray-400 text-sm">{summary}</span>}
          <span className="text-gray-500">{isExpanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Desktop: Always show header */}
      <div className="hidden lg:block p-4 pb-0">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>

      {/* Content: Collapsible on mobile, always visible on desktop */}
      <div className={`p-4 pt-2 ${!isExpanded ? 'hidden lg:block' : ''}`}>
        {children}
      </div>
    </div>
  );
}
```

### 8. Polish/Translate Dropdown (Mobile)

```tsx
{/* Mobile: Dropdown menus */}
<div className="flex lg:hidden gap-2">
  {/* Polish dropdown */}
  <div className="relative">
    <button
      onClick={() => setShowPolishMenu(!showPolishMenu)}
      className="px-3 py-2 bg-gray-700 rounded-lg text-sm"
    >
      ✍️ Polish ▼
    </button>
    {showPolishMenu && (
      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10">
        <button onClick={() => handlePolish("grammar")} className="...">Keep Tone</button>
        <button onClick={() => handlePolish("twitter")} className="...">Twitter Style</button>
        <button onClick={() => handlePolish("280char")} className="...">Fit 280</button>
      </div>
    )}
  </div>

  {/* Translate dropdown */}
  <div className="relative">
    <button
      onClick={() => setShowTranslateMenu(!showTranslateMenu)}
      className="px-3 py-2 bg-gray-700 rounded-lg text-sm"
    >
      🌐 Translate ▼
    </button>
    {showTranslateMenu && (
      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10">
        <button onClick={() => handlePolish("translate_en")} className="...">🇺🇸 English</button>
        <button onClick={() => handlePolish("translate_ko")} className="...">🇰🇷 한국어</button>
        <button onClick={() => handlePolish("translate_zh")} className="...">🇨🇳 中文</button>
      </div>
    )}
  </div>

  <button onClick={() => handleCopy(...)} className="...">📋 Copy</button>
</div>

{/* Desktop: All buttons visible (existing UI) */}
<div className="hidden lg:flex flex-wrap gap-2">
  {/* existing polish buttons */}
</div>
```

---

## Testing Checklist

- [ ] Desktop: 3-row layout displays correctly
- [ ] Desktop: Two suggestion panels side by side
- [ ] Desktop: Target preview shows 200 chars
- [ ] Mobile: Single column layout
- [ ] Mobile: Target preview shows 50 chars (1 line)
- [ ] Mobile: Collapsible Score section works
- [ ] Mobile: Collapsible Tips section works
- [ ] Mobile: Tab switching between suggestions works
- [ ] Mobile: Polish dropdown works
- [ ] Mobile: Translate dropdown works
- [ ] Unified persona selector applies to both panels
- [ ] All existing functionality preserved

---

## Notes

- Breakpoint: `lg:` = 1024px
- Keep all existing state and API calls unchanged
- Only restructure the JSX layout
- Consider extracting CollapsibleSection as a reusable component
