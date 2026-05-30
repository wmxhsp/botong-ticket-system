---
name: self-improving
description: "Self-reflection and learning from corrections for the Botong Ticket System project. Invoke when user corrects your work, a command fails, you discover a better approach, or after completing significant work on the project."
---

# Self-Improving for Botong Ticket System

Learn from corrections, mistakes, and reflections to continuously improve work quality on this project.

## When to Use

- User corrects you or points out mistakes
- A command, test, or build fails
- You discover a better approach after completing work
- You complete significant multi-step work and want to evaluate the outcome
- User says "remember this" or "always do X"

## Architecture

Memory lives in the project directory with tiered structure:

```
.trae/self-improving/
├── memory.md          # HOT: ≤100 lines, always loaded
├── corrections.md     # Last 50 corrections log
├── patterns/          # Per-domain patterns
│   ├── flask.md       # Flask/DDD patterns
│   ├── vue.md         # Vue 3 patterns
│   └── business.md    # Business rules patterns
└── archive/           # COLD: decayed patterns
```

## Learning Signals

### Corrections — add to `corrections.md`

Log when you notice these patterns:
- "No, that's not right..." / "Actually, it should be..."
- "You're wrong about..." / "I prefer X, not Y"
- "Remember that I always..." / "I told you before..."
- "Stop doing X" / "Why do you keep..."
- Test failures that reveal incorrect assumptions
- Build errors from wrong patterns

### Preference signals — add to `memory.md` if explicit

- "I like when you..." / "Always do X for me"
- "Never do Y" / "My style is..."
- "For this project, use..."

### Pattern candidates — track, promote after 3x

- Same instruction repeated 3+ times
- Workflow that works well repeatedly
- User praises specific approach

### Ignore (don't log)

- One-time instructions ("do X now")
- Context-specific ("in this file...")
- Hypotheticals ("what if...")

## Self-Reflection

After completing significant work, pause and evaluate:

1. **Did it meet expectations?** — Compare outcome vs intent
2. **What could be better?** — Identify improvements for next time
3. **Is this a pattern?** — If yes, log to `corrections.md`

**Log format:**
```
CONTEXT: [type of task]
REFLECTION: [what I noticed]
LESSON: [what to do differently]
```

**Example:**
```
CONTEXT: Fixing AmountCalculator float precision
REFLECTION: Used float instead of Decimal, caused 0.01 error in totals
LESSON: Always use Decimal for financial calculations in this project
```

## Project-Specific Patterns

### Flask DDD Architecture

```
api/v1/          → HTTP only, no business logic
application/     → Business orchestration, transaction management
domain/          → Pure business rules (AmountCalculator)
infrastructure/  → Database, messaging, DI
```

**Common mistakes to avoid:**
- Putting business logic in API layer
- Direct SQL in application services
- Bypassing AmountCalculator for fee calculations
- Not wrapping multi-step operations in transactions

### Vue 3 Frontend

```
views/           → Page components
components/      → Reusable components (tickets/, common/, layout/, selectors/)
api/             → API modules (client.js is Axios base)
composables/     → useApi, useConfirm, useToast, useFormValidation
stores/          → Pinia stores (auth, app)
```

**Common mistakes to avoid:**
- Not using `useApi()` for API calls (misses AbortController)
- Using stores for CSRF tokens instead of `api/client.js`
- Not using `useToast()` for notifications
- Forgetting to destroy Chart.js instances in `onBeforeUnmount`
- Missing debounce on search/filter inputs

### Business Rules

- **Profit = Labor margin + Goods margin**
- **Three billing types**: hourly, daily, package
- **AmountCalculator is the ONLY place for fee calculations**
- **CSRF**: `fetchCsrfToken()` from `api/client.js` only
- **Export**: `toolsApi.exportXxx()` + `downloadBlob()`
- **Chart.js**: Register via `plugins/chart.js`, never inline

## Memory Tiers

| Tier | Location | Size Limit | Behavior |
|------|----------|------------|----------|
| HOT | memory.md | ≤100 lines | Always loaded |
| WARM | patterns/*.md | ≤200 lines each | Load on context match |
| COLD | archive/ | Unlimited | Load on explicit query |

### Promotion Rules

- Pattern used 3x in 7 days → promote to HOT
- Pattern unused 30 days → demote to WARM
- Pattern unused 90 days → archive to COLD
- Never delete without asking

## Quick Queries

| User says | Action |
|-----------|--------|
| "What have you learned?" | Show last 10 from `corrections.md` |
| "Show my patterns" | List `memory.md` (HOT) |
| "Forget X" | Remove from all tiers (confirm first) |

## Core Rules

1. **Learn from explicit corrections only** — Never infer from silence
2. **Cite sources** — "Using X (from patterns/flask.md:12)"
3. **Never store credentials** — Security boundary
4. **Compact when exceeding limits** — Merge similar entries, never delete confirmed preferences
5. **Transparency** — Always explain which pattern is being applied
