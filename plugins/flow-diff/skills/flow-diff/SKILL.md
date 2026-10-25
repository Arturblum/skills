---
name: flow-diff
description: "Draw a before/after flow diff of a design change, like a code diff but as swimlane diagrams: new, changed, removed and unchanged parts in colour, every arrow labelled and numbered, every box explained, a numbered step list under each diagram. Use it when a ticket, spec, ADR or PR changes how a flow works across services and the user wants to see the old flow and the proposed one to approve before any code is written, or says 'show me visually', 'diff diagram', 'before and after', 'how does it work now vs after'."
---

# Flow diff

A design review in pictures. The reader should not have to decode a step: each box says what it does, each arrow says what travels and who sends it, and the colours say what this change does to it.

The worked example is `example-notify-269.html` in this folder (the Notify node of issue #269). Copy it, keep the renderer, replace the data.

Where things are in that file: the CSS tokens and diff colours at the top; the page text and legend in `<main>`; the renderer in the `<script>` (`render`, `steps`, `wrap`); and the content in two `render('before', {rows, edges})` / `render('after', {rows, edges})` calls plus two `steps(...)` calls and the "Assumptions to confirm" list. Change only those, plus the title, headings and intro text. A node is `{id, col, kind, title, text}`; an edge is `{from: 'id.side', to: 'id.side', n, kind, label}`.

## Process

1. **Ground it in the code, not in the ticket.** Read the services, routes, queues, ADRs and the ticket's comments. Every box and arrow must correspond to something that exists (before) or is explicitly designed (after). Never draw a provider capability, route or event you did not find. If the "after" needs a design choice nobody made, list it under "Assumptions to confirm" rather than drawing it as settled. Verify the user's beliefs about the current flow in the repo before drawing them.
2. **Pick the lanes.** Four columns at most: the actors that own the steps (for example Workflow run, ControlCenter, Dispatcher, Notifications). One lane per owner, so ownership changes are visible at a glance.
3. **Write the before nodes and edges, then the after nodes and edges.** Same lanes in both.
4. **Colour every node and edge by what the change does to it** (below).
5. **Write the numbered steps** under each diagram, one per arrow number, in plain language with the real route, queue or event name in `code`.
6. **Add an "Assumptions to confirm" box** with the choices you made that the ticket does not settle.
7. **Publish as an Artifact** (load the Artifact tool's quickstart for a plain page first; the page contract and theme rules apply). Write the file to the scratchpad, publish, give the user the link. Republish the same file path after edits.
8. **Stop for approval.** The diagram is the thing the user approves; build nothing until they say so. If they ask what a word means, answer in plain terms and fix the label that confused them.

## Diff colours

| Kind | Meaning | Look |
|---|---|---|
| `new` | does not exist today | green |
| `chg` | exists, behaves differently or is renamed or reused | amber |
| `rm` | goes away | red, dashed outline |
| `same` | untouched | gray |
| `note` | a gap or remark, not a component | dashed, no fill |

Edges use `new`, `rm` or `same` the same way. In the "before" diagram colour what this change removes red; in the "after" diagram show removed things as a red dashed ghost box where they used to sit, so the deletion is visible. Colour is never the only cue: removed is also dashed.

## Writing the words

- **Box:** a short title (what it is) and 1-3 sentences (what it does, who owns it, what is new). Name the service or route. At most about 27 characters per line; the renderer wraps.
- **Arrow label:** actor and payload, in plain words: "Dispatcher approves or rejects", "POST /send with the approval reference and key. Answer: 202". Avoid a bare noun like "decision" or "result" - say whose choice, about what. A label that two readers could read two ways is a bug (this happened with "decision").
- **Arrow numbers** follow time. A split is `2a`/`2b`, `4a`/`4b`. An arrow that is only a wait has no number.
- **Steps list** repeats each number with one or two sentences, including failure and edge cases (nobody holds the role, closed incident, duplicate, never arrives).
- Say plainly who waits and who listens when a wait is involved; it is the most common confusion.

## Layout rules the renderer relies on

- Nodes sit on a grid: `col` 0-3, one row array per row. All nodes in a row get the same height, so side-to-side arrows are straight.
- An arrow runs between node sides (`id.t`, `id.b`, `id.l`, `id.r`) and is routed with right angles. **Never leave a node in a cell an arrow passes through**: a straight run along a row crosses every empty cell between its ends, and a vertical run crosses the cells above and below. Move the node to another row or lane instead.
- The label pill sits above the longest segment of horizontal arrows and beside vertical ones (on the left in the last column, so it stays inside the diagram).
- Keep nodes of one row in adjacent concerns; put ghosts of removed things in a row no arrow uses.
- Twelve nodes per diagram is comfortable; more than about fourteen means split the flow in two diagrams.
- The page scrolls the diagram sideways inside its frame on a phone; the step lists carry the content there.

## Do not

- Draw the "after" before you understand the "before".
- Put real secrets, tokens or personal data in a diagram.
- Present an assumption as decided.
- Make this a widget for anything bigger than a rough sketch: the widget is narrow and its labels have to stay tiny. Use the page.
