---
name: explain-issue
description: "Explain a GitHub issue in plain words, with the context from the code and the ADRs, so the reader understands it fast. Use it when the user gives an issue link or number and asks to explain it, to understand the task, or what it is about."
---

# Explain issue

The reader owns the decisions and will not pick what they do not understand. Explain the issue the way a colleague would at a whiteboard: short sentences, real names from the system, one concrete example, then where the code stands and what is still open.

Read-only. Explain; change nothing on the issue or in the repo.

## Process

1. **Read the issue and its neighbourhood.** `gh issue view <n> --comments`, then the **spec** or map it belongs to, its sibling tickets, its blockers (GitHub's native dependencies, `gh api repos/<owner>/<repo>/issues/<n>/dependencies/blocked_by`) and linked PRs. Comments often supersede the body: read them as part of the issue.
   Done when you can state the goal, the acceptance criteria and every change the comments made.

2. **Ground it in the repo's own language.** Read the domain docs if the repo keeps them (`knowledge/CONTEXT.md` and `knowledge/adr/` in the Matt Pocock layout; `setup-matt-pocock-skills` records where).
   - **Glossary**: every domain term the issue uses, with its definition, so you speak the project's _ubiquitous language_ and avoid the synonyms the glossary rules out.
   - **ADRs** in the area: each decision, and the alternative it rejected.
   - **Code**: where the issue's files, types, routes and events live and what they do today. Quote `path:line`.

   Done when every domain term has a definition or is flagged as missing from the glossary, every ADR that touches the area is read, and every named file or type is located or flagged as not found.

3. **Verify the issue against the code.** Every "today it does X" in the issue is checked. Where the issue and the code disagree, say so in the explanation, plainly: the code wins, and the reader decides what to do.

4. **Explain**, in this order, in plain wording (define a term at first use, in half a sentence):
   1. **The ask**: one sentence, in words a teammate outside the project would follow.
   2. **Why it exists**: the problem today as a _timeline_ of three to five moments, with the real system names and example times: "10:00 the sensor reports X; the Workflow Engine starts Y; ...". Then one analogy from everyday life.
   3. **Where it lands in the code**: the _seam_, meaning the place where behaviour changes without editing every caller; the module that owns it; what changes there and what stays. Name the existing module before proposing a new one.
   4. **What is already decided**: each ADR as one line: the decision and the alternative it rejected.
   5. **The fog**: what the issue leaves undecided or unknown. Each item is the reader's call: what the question is in plain words, what each option costs, and which you recommend.
   6. **How to start**: the _tracer bullet_, the thinnest slice that runs end to end first. Then the order against other tickets: what blocks it, what it unblocks, whether it is the next ticket on the _frontier_, and whether it reads as ready for an agent or needs a human's judgement.

   Done when the reader could retell sections 1 and 2 to a teammate, and every section is filled or says "none".

5. **Offer depth.** Close with the sharpest open question from the fog and offer `/grill-with-docs` to settle it. If the issue's description looks stale or the issue looks done or blocked, offer `/issue-check`.

## Style

- Short sentences. Everyday words first; the project's term second, in brackets, when it differs.
- Real names and example values: `task service`, `10:00`, `sensor 12`. A made-up name teaches nothing.
- Fit one screen, about 25 lines. Offer the longer version of any section when asked.
- Quote the code and ADRs as pointers (`path:line`, `ADR 0051`); the reader opens them when they want the detail.
