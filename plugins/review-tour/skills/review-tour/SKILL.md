---
name: review-tour
description: Walk a reviewer through a code change in the order it actually runs, as a CodeTour in VS Code with real diffs - each step highlights one block, explains in plain words why it was done (drawing on the issue, the docs and the implementation itself), labels the file new or modified, and links to its diff. Creates a tour of the last commit or of all changes on the branch at a chosen depth (1 low, 2 medium, 3 high), and updates an existing tour when the code has moved on.
disable-model-invocation: true
---

# Review tour

A change is easiest to review in the order it **runs**, not in the order files are listed. This
skill builds that order as a [CodeTour](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour)
inside a **review copy** of the repository. The review copy is a git worktree at the base, with
the change applied as uncommitted edits, so VS Code shows the change as real diffs. Each step
highlights exactly one block, says whether its file is new or modified, and links to that file's
diff. The reviewer reads the highlight and stops where it ends.

The reviewer should never have to guess **why** they are looking at something. Each step explains
in plain words why the block exists and why it was written this way. Those explanations draw on
everything that shaped the change: the issue, the docs and, when you wrote the code yourself, what
you learned while writing it.

The mechanical parts are in `scripts/review_tour.py`, in this skill's base directory. Reading the
change, choosing the order and writing the steps are yours.

First decide which of the two jobs this is:

- **A new tour.** Follow steps 1-9.
- **Updating a tour** that already exists, because the code has changed since it was written.
  Follow *Updating a tour* below. The signs: the reviewer says "update the tour", or a review copy
  for this repository already exists next to it (`<repo>-review-*` with a `.tours/` folder).

## 1. Ask what to review, and how deep

Unless the reviewer already said, **ask both questions together**, and never guess.

**What to review:**

- **The last commit only**: just what changed most recently. Good for a follow-up review, when they
  have already been through the rest.
- **All changes on the branch**: everything that differs from the base branch (usually `main`),
  committed or not. Good for a first review, or a final one before merging.

If they name something else, such as a specific commit, a range or a pull request's base, use
that. Confirm the base branch if the repository's default is unclear.

**How deep the tour goes**, as a number from 1 to 3:

| Depth | Steps | Each description |
|---|---|---|
| **1 - low** | Only the main flow: the entry point and the hops that carry the change. Tests, config, tooling and docs are named in the closing step, not visited. | Two or three sentences: why the block is there, then **Check:**. |
| **2 - medium** | The whole reading order in step 5. A minor block can share a step with its neighbour. | A short paragraph on why, a list of the parts if there are several, then **Check:**. |
| **3 - high** | Every changed block gets its own step, including each test, config section and doc section. | The full explanation: why, how it fits the flow, the alternatives you considered and why they were rejected, edge cases, and what is and isn't tested, then **Check:**. |

If the reviewer gives no depth, use 2 and say so.

## 2. Make the review copy

Run from inside the repository:

```bash
# All changes on the branch: every commit since the merge-base, plus uncommitted and untracked files
python3 <skill-dir>/scripts/review_tour.py setup --base main --working-tree --name <short-name>

# The last commit only (or --base <ref> --head <ref> for any other range)
python3 <skill-dir>/scripts/review_tour.py setup --base HEAD~1 --head HEAD --name <short-name>
```

It prints the review copy's path and the diff's size. Compare the size with `git diff main --shortstat`
or `git show --shortstat HEAD` if in doubt. The script creates `<repo>-review-<name>` next to the
repository. It never changes the repository's branches, commits, index or remote, and it runs no
git hooks.

## 3. Gather the context: why this change exists

The diff shows what changed. Before reading it, find out **why**, from every source you can reach:

- **Your own memory of the work.** If you wrote this change in this conversation, you know things
  no file records: the problem as it was first described, what you tried first and dropped, the
  bugs you hit, and the reasons for each decision. Use them. This is often the most valuable
  context there is.
- **The issue or ticket.** Look for its number in the branch name, the commit messages or the pull
  request, then read it, with `gh issue view <n>` or the tracker's tool if one is connected. Read
  the comments too: requirements often change there.
- **The pull request**, if there is one: `gh pr view --comments` gives the description and the
  discussion so far.
- **The commit messages**: `git log <base>..<head>` (add `--format=%B` for the full messages).
- **Docs and design records** that the change touches or that the issue links to: specs, ADRs,
  READMEs, API docs.

Keep notes on what each source says the change is *for*, and on any place where the code seems to
depart from it. Don't invent a reason the sources don't support. If you can't find out why
something was done, say so in that step. At depth 1, the issue and your own memory are usually
enough. At depth 3, read everything.

## 4. Read the whole change

Read all of it: `git -C <review-copy> diff` covers modified files, and new files show in full.
Understand what the change does, and match each part to the reason you found for it in step 3,
before deciding how to present it.

## 5. Choose the reading order: follow one flow

Pick the single path that best explains the change, such as one request, message, job or user
action, and follow it through the code in the order it runs. A typical shape:

1. **What and why.** A step with no file (see step 6), then the design record if there is one.
2. **Where it starts.** The entry point, event, route or configuration the flow comes in through.
3. **Wiring.** Registration and configuration: how the pieces are connected.
4. **The flow itself**, in call order: each hop is a step.
5. **The failure paths**, where the flow can go wrong.
6. **Tests**, one step per seam or per test file, saying what each proves.
7. **Deployment and configuration**, **tooling**, then **docs and records**.
8. **A closing step**: the open questions, and anything deliberately left out of the tour.

The depth chosen in step 1 decides how many of these steps the tour has. Keep the order the same
at every depth.

Rules for the steps:

- **One step, one block**: a method, a class, a config section, a doc section. Keep a step to
  about 60 lines. Split a larger block where it has a natural seam.
- **Give every step an explicit `end` line.** The script can guess one, but only a person can be
  sure where the thought ends.
- **Every changed file appears in a step**, or is named in the closing step as not worth a visit.
  `finish` lists every changed file no step visits.

## 6. Write the steps

Write for someone who has not seen the issue and was not there when the code was written. Use
plain words, short sentences, and name things the way the issue and the docs name them.

**The first step** (no file) answers *why am I reviewing this?* before any code appears:

- **The problem**: what was wrong or missing, and who it affected. Link the issue.
- **The approach**: what the change does about it, in two or three sentences, and why this
  approach rather than the obvious alternative, if there was one.
- **What the tour covers**: the last commit, or all changes against the base, and at which depth.
- **The flow it follows**, and roughly how many steps there are.
- **Where to look hardest**: the one or two places where the reviewer's judgement matters most.

**Every other step** says, in this order:

1. **Why**: the reason this block exists, tied back to the problem or to a requirement in the
   issue. ("The issue asks for retries on timeouts, so...")
2. **What it does in the flow**: where it is called from, and what it hands on. Use a list where
   there are several parts. Don't restate the code line by line.
3. **Why it is written this way**, when that isn't obvious: a constraint, a bug found while writing
   it, a rejected alternative. Your memory of the implementation from step 3 belongs here.
4. **Check:** the one thing in that block that most needs the reviewer's judgement: a risky
   decision, a departure from the issue or the spec, something untested.

How long each part is depends on the depth (step 1): a sentence each at depth 1, and everything
you know at depth 3. At every depth, say plainly what was not verified, and never claim anything
that the code, a test or one of the sources from step 3 does not show.

Write the first draft to a scratch location, **not** into the repository. Record the depth in the
draft, so that an update keeps it:

```json
{
  "title": "#123 - short name of the change",
  "depth": 2,
  "steps": [
    { "title": "Start here", "description": "**The problem:** ... ([#123](...))\n\n**The approach:** ...\n\n**This tour:** ..." },
    { "file": "src/orders/handler.py", "line": 40, "end": 72, "title": "Handling one order", "description": "**Why:** ...\n\n... **Check:** ..." }
  ]
}
```

`line` and `end` are 1-based and inclusive, and paths are relative to the repository root.

## 7. Finish and check

```bash
python3 <skill-dir>/scripts/review_tour.py finish --worktree <review-copy> --draft <draft.json>
```

It writes the tour and a `.code-workspace` file that makes the highlight visible. It adds a
new-or-modified label and a diff link to every step, and prints the first and last line of each
step's range. **Read that output.** Fix any range that starts or stops mid-thought, cover or name
every file it lists as not visited, and run `finish` again.

`finish` keeps the draft as `<review-copy>/.tours/draft.json`, with a `_anchor` on each step that
records where its block was. **From then on, edit that draft** and run `finish` without `--draft`.
The tour, the draft and the script's state live in `.tours/`, which is excluded from git, so they
never show up as a change or get committed.

## 8. Hand over

Tell the reviewer:

- to open it with `code <review-copy>.code-workspace`;
- if CodeTour isn't installed, to run `code --install-extension vsls-contrib.codetour`;
- to start the tour from the **CodeTour** panel in the Explorer sidebar;
- that the gutter shows green for added, blue for modified and a red triangle for deleted lines;
- that each step's **⇄ Open this file's diff** link, or the file in **Source Control**, shows the
  side-by-side diff;
- **never to commit from the review copy.** Its base is the base branch, not theirs. Changes go
  on the real branch;
- that when the code changes, they can ask for the tour to be **updated**, and that they can ask
  for a different depth.

## 9. Clean up when they are done

```bash
python3 <skill-dir>/scripts/review_tour.py cleanup --worktree <review-copy>
```

This removes the review copy, its tour and its workspace file. The repository's branches and
commits are untouched.

## Updating a tour

When the code has changed since the tour was written, update it rather than starting again:
unchanged steps keep their wording, and only what moved or changed needs attention.

1. **Refresh the review copy:**

   ```bash
   python3 <skill-dir>/scripts/review_tour.py refresh --worktree <review-copy>
   ```

   It applies the change again, as it is now and in the same mode it was set up with. For the
   last-commit mode, that means the *new* last commit. It then prints:
   - **the files that changed** since the draft was last matched to the code;
   - for every step, one of:
     - **unchanged**: its file didn't change. Leave it.
     - **REVIEW**: its file changed. The script has moved the step to where its first line is now.
       Check the range, and whether the description is still true.
     - **LOST**: its file or its first line is gone, for example after a rename. Point it at the
       new place, rewrite it, or remove it.
     - **NEW**: a step added to the draft since the last `finish`.

   It updates `.tours/draft.json` with the new line numbers. It does not touch the tour itself.

2. **Read what changed**, with `git -C <review-copy> diff` for the files it listed. Find out why
   it changed, as in step 3: new commit messages, new comments on the issue or the pull request,
   and what you remember if you made the change. Then **edit `.tours/draft.json`**, keeping the
   depth recorded in it unless the reviewer asks for another:
   - rewrite the REVIEW and LOST steps whose meaning changed, including their **Why**;
   - add steps for new code, in flow order, written as in step 6;
   - remove steps for code that no longer exists;
   - update the first step, so it says what this revision of the tour covers and why the code
     changed since the last one.

   If the reviewer asks for a different depth, change `depth` in the draft and add, merge or
   expand steps to match it. The scope stays the same, so there's no need to start again.

3. **Run `finish` without `--draft`**, read its output as in step 7, and fix what it reports.

4. **Tell the reviewer what changed in the tour**: which steps are new, rewritten or removed.
   CodeTour picks up the new tour file. If it doesn't, they reload the window (**Developer:
   Reload Window**).

If the reviewer wants a different scope, such as switching from the last commit to all changes,
don't refresh. Clean up, then set up again with the new mode.
