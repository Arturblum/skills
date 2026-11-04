---
name: explain-issue
description: "Explain a GitHub issue in plain words, with the context it needs from the code, the ADRs and the issues it links to. Use when the user gives an issue link or number and asks what it is about."
---

# Explain issue

The reader works on a large project and forgets most of it. Write for a colleague at a whiteboard who has not touched this area for months: short sentences, real names from the system, one concrete example. The explanation is _self-contained_: the reader finishes it with no question left for the agent.

Read-only: explain, and leave the issue and the repo as they are.

## Process

1. **Read the issue and everything it points to.** `gh issue view <n> --comments`, then the **spec** or map it belongs to, its sibling tickets, its blockers (GitHub's native dependencies, `gh api repos/<owner>/<repo>/issues/<n>/dependencies/blocked_by`) and linked PRs. Comments often supersede the body: read them as part of the issue. Then open every issue, PR, ADR and doc the text names by number or link, and write one line on each: what it is, and what it decided or did.
   Done when you can state the goal, the acceptance criteria and every change the comments made, and every reference has its line.

2. **Ground it in the repo's own language.** Read the domain docs the repo keeps: glossary, ADR folder, AGENTS.md / CLAUDE.md (`knowledge/CONTEXT.md` and `knowledge/adr/` in the Matt Pocock layout; `setup-matt-pocock-skills` records where).
   - **Glossary**: every domain term the issue uses, with its definition, so you speak the project's _ubiquitous language_ and avoid the synonyms the glossary rules out.
   - **ADRs** in the area: each decision, the alternative it rejected, and its status; only `accepted` ones bind.
   - **Code**: where the issue's files, types, routes and events live and what they do today. Quote `path:line`.

   Done when every domain term has a definition or is flagged as missing from the glossary, every ADR that touches the area is read, and every named file or type is located or flagged as not found.

3. **Verify the issue against the code.** Every "today it does X" in the issue is checked. Where the issue and the code disagree, say so in the explanation, plainly: the code wins, and the reader decides what to do.

4. **Write the explanation**, in this order, under these plain headings. Think with the leading words (_seam_, _tracer bullet_, _frontier_) and write them out as plain words.
   1. **What it asks**: one sentence a teammate outside the project would follow.
   2. **Why it exists**: the problem today as a _timeline_ of three to five moments, with the real system names and example times: "10:00 the sensor reports X; the Workflow Engine starts Y; ...". Then one analogy from everyday life.
   3. **Where it lands in the code**: what the code does today, then the _seam_: the one place where behaviour changes without editing every caller, the module that owns it, what changes there and what stays. Name the existing module before proposing a new one.
   4. **What is already decided**: each ADR as one line: the decision, the alternative it rejected, and what it means for this issue.
   5. **What is still open**: what the issue leaves undecided or unknown. Each item is the reader's call: the question in plain words, what each option costs, and which you recommend.
   6. **How to start**: the _tracer bullet_, the thinnest slice that runs end to end first. Then the order against other tickets: what blocks it, what it unblocks, whether it is the next ticket on the _frontier_, and whether it is ready for an agent or needs a human's judgement.

   Done when every section is filled or says "none".

5. **Ask the forgetful reader's questions.** Reread the draft section by section as a developer who forgot this project, and write down each question that reader would ask next: "what is X?", "where does that live?", "what did #123 say?", "why not Y?", "what does it do today?". Answer each one in the text.
   Done when every term, component, ticket and ADR the text names is defined at its first mention in half a sentence, and the reader could retell sections 1 and 2 to a teammate without opening a file.

6. **Offer depth.** Close with the sharpest open question and offer `/grill-with-docs` to settle it. If the issue's description looks stale or the issue looks done or blocked, offer `/issue-check`.

## Style

- Short sentences. Everyday words first; the project's term second, in brackets, when it differs.
- Say what a thing does, then its name: "the task service (it creates and assigns tasks)".
- Real names and example values: `task service`, `10:00`, `sensor 12`. Mark a value you made up as an example.
- A pointer (`path:line`, `ADR 0051`, `#123`) follows a plain statement of what it says; the reader opens it only for more detail.
- Aim for one screen. A definition the reader needs outranks the length.
