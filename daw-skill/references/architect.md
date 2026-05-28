# DAW Module: Phase 1 — Semantic Analysis (The Architect)

## Objective

Understand the business requirement and output a structured narrative blueprint — a semantic map of what the page must communicate, feel, and achieve — without any technical implementation detail. The Architect answers *why* and *what*, never *how*.

---

## 1. Brand Identity Analysis

Before touching layout, establish the brand's narrative posture:

```json
{
  "brand_archetype": "Sage / Caregiver / Creator / Hero / Outlaw / etc.",
  "brand_voice": {
    "tone": "aspirational / authoritative / warm / academic / rebellious",
    "formality": "formal / neutral / casual",
    "audience_age": "teens / young-adults / professionals / executives / mixed",
    "cultural_context": "Mexican / Latin American / global — including regional expressions, values, and taboos"
  },
  "emotional_target": "How should the user feel after the page? (trust, urgency, curiosity, belonging, inspiration, relief)"
}
```

**Guiding questions:**
- Is this institutional (trust, tradition, authority) or commercial (desire, urgency, FOMO)?
- What emotional barrier is the user overcoming? (fear of cost, distrust, confusion, apathy)
- What existing mental model does the user bring? (school = "boring", nonprofit = "poor quality", premium = "exclusive")

---

## 2. Narrative Architecture

Choose the page's narrative arc. These determine section ordering, pacing, and emotional trajectory:

| Arc | Structure | Best For |
|-----|-----------|----------|
| **Hero's Call** | Identity → Problem → Solution → Social Proof → CTA | Admissions, enrollment, signups |
| **Before/After** | Pain State → Bridge → Desired State → Testimonial → CTA | Transformation stories, therapy, coaching |
| **Ladder of Value** | Feature → Benefit → Emotional Outcome → Belonging → CTA | Premium products, memberships |
| **Trust Cascade** | Credentials → Authority Proof → Social Proof → Risk Reversal → CTA | Institutions, financial services, healthcare |
| **Problem/Ax** | Agitate Problem → Present Solution → Evidence → Objection Handling → CTA | B2B, complex services, high-consideration |
| **Revelation** | Curiosity Hook → Mystery → Reveal → Amplify → CTA | Events, launches, news |
| **Monolith** | Single strong message repeated across angled sections | Brand awareness, manifesto pages |

**Output:** Declare the chosen arc and justify:

```json
{
  "narrative_arc": "Hero's Call",
  "rationale": "Prospective students need to see themselves in the story: current state (lost/unsure) → encounter (discover programs) → transformation (graduate) → mission (apply)"
}
```

---

## 3. Emotional Journey Mapping

Map each section to an emotional state. The page should feel like a deliberate journey, not a checklist.

```json
{
  "emotional_arc": [
    {"section": "Hero",         "feeling": "awe / curiosity",       "intensity": 0.9},
    {"section": "About/Values", "feeling": "trust / belonging",    "intensity": 0.6},
    {"section": "Programs",     "feeling": "aspiration / desire",  "intensity": 0.7},
    {"section": "Testimonials", "feeling": "validation / relief",  "intensity": 0.8},
    {"section": "CTA",          "feeling": "urgency / excitement", "intensity": 1.0}
  ]
}
```

**Rules:**
- Intensity should generally trend upward (don't end weaker than you start).
- Alternate high/low intensity to avoid emotional fatigue.
- Never put two low-intensity sections consecutively (user disengages).

---

## 4. Section Intent Typology

Every section must serve a clear intent. Classify each section into exactly one type:

| Intent | Purpose | Typical Elements |
|--------|---------|-----------------|
| `hook` | Grab attention, establish relevance | Hero image, bold headline, sub-header |
| `educate` | Inform about offering | Features grid, expandable content, icons |
| `empathize` | Acknowledge pain/need | Quote, scenario, diagnostic question |
| `authority` | Build credibility | Logos, credentials, awards, years |
| `social_proof` | Show others trust | Testimonials, stats, case numbers |
| `transform` | Show desired outcome | Before/after, success story, visual result |
| `objection_handle` | Remove barriers | FAQ, guarantee, risk reversal, pricing |
| `reassure` | Build confidence | Trust badges, accreditations, security |
| `inspire` | Emotional connection | Video, story, mission statement |
| `convert` | Drive action | Primary CTA, urgency trigger, form |

```json
{
  "sections": [
    {"name": "Hero",             "intent": "hook"},
    {"name": "Mission Values",   "intent": "inspire"},
    {"name": "Programs Grid",    "intent": "educate"},
    {"name": "Testimonials",     "intent": "social_proof"},
    {"name": "Why Us",           "intent": "authority"},
    {"name": "FAQ",              "intent": "objection_handle"},
    {"name": "Final CTA",        "intent": "convert"}
  ]
}
```

**Do not** put two `educate` sections consecutively — interleave with `social_proof` or `empathize`.

---

## 5. Content Hierarchy & Information Architecture

Define what information lives at each depth level:

```json
{
  "content_hierarchy": {
    "level_1_hero": {
      "headline": "Main value proposition (≤8 words)",
      "subline": "Secondary elaboration (≤20 words)",
      "cta": "Single primary action"
    },
    "level_2_secondary": {
      "headlines": "Section headers that reinforce the arc",
      "supporting": "Details that prove the headline"
    },
    "level_3_detail": {
      "body": "Full explanations, lists, descriptions",
      "expandable": "FAQs, specifications, optional depth"
    }
  }
}
```

**Principle:** A user should understand the page's entire value proposition by reading only Level 1. Levels 2 and 3 add conviction, not confusion.

---

## 6. Persuasion Layer

Map established persuasion principles to sections:

```json
{
  "persuasion": [
    {"principle": "Social Proof",    "section": "Testimonials",     "mechanism": "Video testimonial with name and title"},
    {"principle": "Authority",       "section": "Why Us",          "mechanism": "Years of experience, accreditations logos"},
    {"principle": "Scarcity",        "section": "CTA",             "mechanism": "Limited spots, deadline indicator"},
    {"principle": "Reciprocity",     "section": "Hero",            "mechanism": "Free guide download before asking for application"},
    {"principle": "Liking",          "section": "Mission Values",  "mechanism": "Human-centered photography, shared values"},
    {"principle": "Consistency",     "section": "CTA",             "mechanism": "Small yes first (newsletter) → big yes (apply)"}
  ]
}
```

---

## 7. Conversion Funnel Alignment

Map sections to funnel stages to ensure no stage is neglected:

| Funnel Stage | Purpose | Minimum Sections |
|-------------|---------|-----------------|
| **Awareness** | "Who are you and why should I care?" | 1–2 (Hero, Mission) |
| **Interest** | "What do you offer me?" | 1–2 (Programs, Features) |
| **Consideration** | "Why you and not another?" | 1–2 (Why Us, Testimonials, Authority) |
| **Decision** | "What's stopping me?" | 1 (FAQ, Objections) |
| **Action** | "Do it now" | 1 (CTA) |

---

## 8. Structural Patterns (Reusable Compositions)

Recognize recurring narrative patterns that can be combined:

| Pattern | Structure | When to Use |
|---------|-----------|-------------|
| **Promise → Proof → Push** | Hook → Evidence → CTA | Per-section micro-arc |
| **Problem → Agitate → Solve** | Pain → Empathy → Solution | High-empathy products |
| **Feature → Benefit → Feeling** | What → So what → How you'll feel | Premium positioning |
| **Claim → Example → Test** | Statement → Story → Stat | Authority-heavy pages |
| **Hook → Explore → Resolve** | Intrigue → Detail → Payoff | Storytelling approach |

---

## 9. Cultural & Accessibility Sensitivity

For Mexican / Latin American audiences:

```json
{
  "cultural_sensitivity": {
    "family_values": "Include family-oriented imagery and language — decisions are often collective, not individual",
    "trust_signals": "Emphasize tradition, longevity, personal relationships over purely transactional benefits",
    "formality_scale": "1–5 (1=informal, 5=formal) — institutions lean toward 3–4, not 5 which feels cold",
    "religious_institutions": "If applicable, reference mission/values without being preachy — balance spiritual with professional",
    "economic_context": "Acknowledge cost sensitivity directly — use transparency, not avoidance",
    "accessibility": {
      "reading_level": "Aim for 6th–8th grade Spanish — complex ideas, simple sentences",
      "visual_hierarchy": "Strong contrast, large tap targets (≥48px), legible font sizes",
      "cognitive_load": "Limit 5–7 sections max per page. Fewer choices → higher conversion",
      "color_blindness": "Never rely on color alone to convey meaning — use icons, text labels, patterns"
    }
  }
}
```

---

## 10. Output Schema (Complete)

The Architect delivers this JSON to the Design Lead. This is the sole deliverable of Phase 1.

```json
{
  "page_title": "Example Page",
  "page_goal": "Primary conversion goal (apply, donate, register, inform)",
  "narrative_arc": "Hero's Call",
  "emotional_target": "Trust and aspiration",
  "brand_archetype": "Sage",
  "funnel_coverage": {
    "awareness": true,
    "interest": true,
    "consideration": true,
    "decision": true,
    "action": true
  },
  "sections": [
    {
      "name": "Hero",
      "intent": "hook",
      "feeling": "awe",
      "persuasion": "Reciprocity",
      "content_outline": {
        "headline": "Main value proposition (≤8 words)",
        "subline": "Secondary elaboration (≤20 words)",
        "cta_text": "Primary action button"
      }
    },
    {
      "name": "Mission / Values",
      "intent": "inspire",
      "feeling": "belonging",
      "persuasion": "Liking",
      "content_outline": {
        "headline": "Short mission statement",
        "values": ["Value 1 with brief description", "Value 2", "Value 3"]
      }
    },
    {
      "name": "Programs / Offerings",
      "intent": "educate",
      "feeling": "aspiration",
      "persuasion": null,
      "content_outline": {
        "headline": "Section title",
        "items": [
          {"name": "Program A", "brief": "One-line description"},
          {"name": "Program B", "brief": "One-line description"}
        ]
      }
    },
    {
      "name": "Testimonials",
      "intent": "social_proof",
      "feeling": "validation",
      "persuasion": "Social Proof",
      "content_outline": {
        "headline": "Section title",
        "testimonials": [
          {"quote": "Compelling quote", "author": "Name, Title", "format": "video / text"}
        ]
      }
    },
    {
      "name": "Why Us / Credentials",
      "intent": "authority",
      "feeling": "trust",
      "persuasion": "Authority",
      "content_outline": {
        "headline": "Section title",
        "credentials": ["Years of experience", "Accreditations", "Notable alumni"]
      }
    },
    {
      "name": "FAQ / Objections",
      "intent": "objection_handle",
      "feeling": "relief",
      "persuasion": null,
      "content_outline": {
        "headline": "Common questions",
        "questions": [
          {"q": "Question", "a": "Answer addressing concern directly"}
        ]
      }
    },
    {
      "name": "Final CTA",
      "intent": "convert",
      "feeling": "urgency",
      "persuasion": "Scarcity",
      "content_outline": {
        "headline": "Compelling closing headline",
        "cta_text": "Primary action button",
        "urgency_trigger": "Limited time / limited spots / deadline"
      }
    }
  ],
  "cultural_notes": [
    "Use family-inclusive language",
    "Emphasize tradition and longevity",
    "Address cost with transparency, not avoidance"
  ],
  "accessibility_notes": [
    "6th–8th grade reading level",
    "Strong contrast ratios",
    "Large touch targets (≥48px)"
  ]
}
```

---

## 11. Handoff Protocol

1. Deliver the JSON output to the **Design Lead** (Phase 2).
2. The Design Lead validates against brand guidelines, researches competitive positioning, and may request revisions.
3. Only after Design Lead approval does the JSON flow to the **Designer** (Phase 3) for technical mapping.
4. The Architect does **not** participate in Phases 2–4 unless clarifications are needed.

**Quality Gate:** The Architect output must pass these checks before handoff:
- [ ] Each section has exactly one `intent` from the typology
- [ ] The `emotional_arc` has no consecutive same-intent sections
- [ ] The `funnel_coverage` covers all 5 stages
- [ ] `persuasion` principles are identified for at least 50% of sections
- [ ] `cultural_notes` are specific to the audience (not generic)
- [ ] `content_outline` provides enough specificity for a copywriter to write from
- [ ] `accessibility_notes` include at least 3 concrete requirements
