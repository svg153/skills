---
name: social-publishing
description: "Plan, fact-check, draft, adapt, and maintain credible social posts, comments, reposts, threads, and long-form articles for LinkedIn, X/Twitter, blogs, and community channels. Use when turning technical work, research, repositories, events, or external posts into publishable content while preserving attribution, evidence, tone, and privacy."
license: MIT
metadata:
  author: svg153
  version: "1.0.0"
---

# Social Publishing

Create social and long-form content that is useful before it is promotional, evidence-aware before it is confident, and explicit about where ideas came from.

## Use this skill when

- drafting or revising LinkedIn posts, comments, reposts, newsletters, blog posts, articles, X posts, or threads;
- turning technical research, a repository, release, event, talk, or conversation into publishable content;
- responding to another person's work while adding an independent perspective;
- repurposing one idea across platforms without copy-pasting the same format everywhere;
- maintaining content drafts in a repository with status, sources, and editorial notes;
- deciding how to credit inspiration, forks, upstream projects, collaborators, or community work.

Do not invoke a full editorial workflow for a trivial typo-only edit unless the user asks for broader review.

## Core principles

1. **Contribution before promotion.** The reader should get an idea, observation, warning, lesson, or useful resource before being asked to care about the author's project.
2. **Attribution before self-reference.** When reacting to somebody else's work, identify and credit that work before presenting the derivative idea or project.
3. **Separate fact from interpretation.** Mark causal claims, predictions, estimates, and personal conclusions as such.
4. **Prefer verified specificity.** Verify dates, releases, product capabilities, repository facts, statistics, and quotes when they materially affect the piece.
5. **Remove unsupported precision.** If an exact number cannot be sourced, use a defensible qualitative formulation instead of inventing confidence.
6. **Do not hijack the source post.** A comment should primarily engage with the author's idea. A repost or standalone article is the better place for a longer thesis or project promotion.
7. **Preserve privacy by default.** Do not publish private repository contents, customer names, email addresses, credentials, exact personal locations, private financial details, unpublished employer information, or other sensitive context unless the user explicitly chooses to disclose it.
8. **No fake neutrality.** Critique weak claims and alternatives when useful, but do not manufacture controversy for engagement.

## Attribution and independent implementations

When a new project was inspired by another project but diverged substantially, prefer wording such as:

> This project was inspired in part by X. The scope became sufficiently different that keeping the implementations independent was clearer than turning X into a much broader project.

If asked why there was no PR or fork:

- explain the **scope/architecture difference**, not superiority;
- state that attribution remains explicit;
- avoid implying that a PR was rejected unless it actually was;
- do not describe an independent implementation as an upstream continuation;
- if a fork would have preserved useful lineage, acknowledge that trade-off without apologetic language.

Never use "official" in a way that could imply vendor endorsement. For community projects, prefer "published by the community", "maintained by <community>", or "a community skill/project" unless official status is documented.

## Workflow

### 1. Establish the content job

Identify:

- platform and format;
- target audience;
- desired action or outcome;
- source material being reacted to;
- author's independent thesis;
- whether a project/resource link belongs in the piece;
- facts that require current verification.

### 2. Build an evidence ledger

Separate notes into:

- **verified facts** — dates, releases, links, repository state, direct statements;
- **interpretations** — why the facts matter;
- **personal experience** — clearly framed as experience, not universal evidence;
- **open questions** — claims that should be softened or removed if not verified.

Prefer primary sources for factual claims. Community discussion is useful for sentiment, not for establishing hard facts by itself.

### 3. Choose the right degree of self-promotion

| Format | Default promotion level |
| --- | --- |
| Reply/comment on someone else's post | Low |
| Repost/quote-post with commentary | Medium |
| Standalone project post | Medium-high |
| Long-form article/blog | Context-dependent; value should dominate |
| Release announcement | High, but explain why the release matters |

When linking a project in a comment, credit the source idea first and keep the explanation compact.

### 4. Draft for the platform

#### LinkedIn comment

- Start directly with the idea you are responding to.
- Usually 2–6 short paragraphs.
- Credit the author/project naturally.
- Add one useful extension or disagreement.
- If linking your own project, do it after the substantive response.
- Avoid turning the comment into a mini press release.

#### LinkedIn repost / post with commentary

- Give the source project/person clear credit in the first third.
- Explain the connection to your own thesis or experience.
- Develop the independent argument.
- Introduce your project or resource only after the reader understands why it exists.
- End on the idea, question, or practical implication rather than a generic engagement bait CTA.

#### X / Twitter

- Make the first post independently useful.
- Credit the source in the first post when the whole thread depends on it.
- Prefer one strong idea per post.
- Use a thread only when compression would remove necessary evidence or nuance.
- Do not fragment prose into a thread just to increase impressions.

#### Article / blog

Use a structure such as:

1. motivating observation or concrete story;
2. changed context / why the old assumption no longer holds;
3. thesis;
4. evidence and examples;
5. strongest counterargument or limitation;
6. practical framework or decision model;
7. project/resource if relevant;
8. conclusion that returns to the thesis;
9. sources / fact-check notes when useful.

### 5. Review tone

Prefer:

- natural, technical-professional language;
- short paragraphs;
- concrete nouns and verbs;
- qualified claims where evidence is incomplete;
- constructive disagreement;
- explicit uncertainty.

Avoid:

- inflated claims such as "this changes everything";
- corporate filler and motivational clichés;
- fake contrarian hooks;
- unnecessary superlatives;
- unsupported numeric claims;
- claiming precedence ("I invented this first") when the evidence only shows prior similar thinking;
- language that diminishes the source author to make the derivative project look stronger.

### 6. Repository-backed editorial workflow

When drafts live in a Git repository:

- keep publishable copy separate from research/fact-check notes;
- record platform, date, format, and status when the repository convention supports it;
- keep source URLs in a fact-check section even if they are removed from the final social copy;
- preserve alternative versions only when they support a real publishing choice;
- update stale project status/version references before marking a draft ready;
- never copy private repo-only context into a public reusable skill.

Suggested statuses:

`idea -> research -> draft -> draft-ready -> scheduled -> published -> repurpose`

## Final quality gate

Before returning or publishing, check:

- Does the opening say something useful rather than merely announce something?
- Is the original source/person credited before the derivative project is promoted?
- Are factual claims current and sourced where needed?
- Are interpretation and causation clearly distinguished?
- Could any private information leak from notes, filenames, links, examples, or metadata?
- Does the platform adaptation feel native rather than copied from another format?
- Is the CTA necessary?
- Is there a shorter version that preserves the actual point?

## Default deliverable

For substantial drafting work, return or store:

1. a recommended publishable version;
2. one materially different shorter or lower-promotion alternative when useful;
3. fact-check/source notes outside the clean copy;
4. a brief editorial note explaining any claim that was softened, removed, or reframed.
