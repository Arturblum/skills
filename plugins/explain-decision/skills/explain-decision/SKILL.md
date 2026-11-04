---
name: explain-decision
description: "Explain an open decision in plain words, with the context for each option, so the developer can choose fast. Use when the user asks to understand a decision or what its options mean."
---

# Explain decision

The reader must choose, and chooses only what they understand. They work on a large project and forget most of it. Explain each decision to a colleague at a whiteboard who has not touched this area for months: short sentences, real names from the system, one concrete example that shows where the options part ways. The explanation is _self-contained_: the reader can choose and answer in one line, with no question left for the agent.

Read-only: explain, and leave the issue and the repo as they are. The choice belongs to the reader.

## Process

1. **Find the decisions.** Take them from this conversation (the open items of an `explain-issue` or `issue-check` report), or from the issue the user names: `gh issue view <n> --comments`, the `## Open decisions` section, and any question the comments left unanswered. Take the one the user named; with none named, take all of them. List the decisions, ordered so a decision that others depend on comes first.
   Done when each decision is one line in your own words and every dependency between decisions is noted.

2. **Gather the facts each option stands on.** For each decision, read the issue and everything it points to (linked issues, PRs, specs), the glossary, the ADRs in the area (only `accepted` ones bind), and the code the options touch. Quote `path:line`.
   For each option, find: what changes in the code and where; which ADR it follows or breaks; what it costs now; what it makes harder or easier later, and how hard it is to undo.
   Done when every option has all four, and every domain term, ticket and ADR you will mention has a definition in half a sentence.

3. **Write each decision** in this shape, under these plain headings. Think with the leading words (_fork_, _reversible_, _blast radius_) and write them out as plain words.
   1. **The question**: one sentence a teammate outside the project would follow.
   2. **Why it needs an answer now**: what is stuck until it is answered.
   3. **What the choice stands on**: the few facts every option shares: what the code does today, what the ADRs already decided, what the issue requires. Each defined at first use.
   4. **The options**, two to four, each with:
      - **What it means**: one sentence, in everyday words first, the project's term second in brackets.
      - **In the example**: what happens to one concrete scenario with real names and values (`sensor 12`, `10:00`), the same scenario for every option, so the reader sees where they part ways.
      - **Wins** and **costs**: what it gets and what it costs, including what it makes harder later and how hard it is to undo.
      - **Fit**: the ADR or code convention it follows or breaks.
   5. **My pick**: one option, the reason in one sentence, and what would change it. When the answer rests on something only the reader knows (priorities, deadlines, a user's wishes), say so and name that fact.
   6. **How to answer**: the line to reply with ("B", or "B, with the retry limit at 3") and what the agent does next once it is answered.

   Options come from the issue, its comments and the ADRs first. Mark an option you added yourself as _my addition_, and include "do nothing" or "decide later" only when it is a real path with a cost of its own.
   Done when every option has all four parts, run on the same example, and every decision has a pick or names the missing fact.

4. **Ask the forgetful reader's questions.** Reread the draft decision by decision as a developer who forgot this project, and write down each question that reader would ask next: "what is X?", "what happens to Y under B?", "can I undo it?", "why not Z?". Answer each one in the text.
   Done when every term, component, ticket and ADR the text names is defined at its first mention, and the reader could explain to a teammate why the options differ without opening a file.

5. **Close on the answer.** Ask for the choice in the one-line form from "How to answer". When the issue holds the decision, offer to record the answer there; when it shapes the architecture, offer an ADR for it.

## Style

- Short sentences. Everyday words first; the project's term second, in brackets, when it differs.
- Say what a thing does, then its name: "the task service (it creates and assigns tasks)".
- Real names and example values. Mark a value you made up as an example.
- Give every option the same shape and the same example, so the reader compares like with like.
- A pointer (`path:line`, `ADR 0051`, `#123`) follows a plain statement of what it says; the reader opens it only for more detail.
- Aim for one screen per decision. A fact the reader needs outranks the length.
