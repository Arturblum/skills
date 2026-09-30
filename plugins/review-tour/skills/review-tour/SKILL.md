---
name: review-tour
description: Walk a reviewer through a code change in the order it actually runs, as a CodeTour in VS Code with real diffs - each step highlights one block, labels the file new or modified, and links to its diff. Use when someone asks to review, walk through, or go over the changes of a branch, commit or pull request, or wants to know which order to read changed files in.
---

# Review tour

A change is easiest to review in the order it **runs**, not in the order files are listed. This
skill builds that order as a [CodeTour](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour)
inside a **review copy** of the repository. The review copy is a git worktree at the base, with
the change applied as uncommitted edits, so VS Code shows the change as real diffs. Each step
highlights exactly one block, says whether its file is new or modified, and links to that file's
diff. The reviewer reads the highlight and stops where it ends.

The mechanical parts are in `scripts/review_tour.py`, in this skill's base directory. Reading
the change and choosing the order are yours.

## 1. Pin what is being reviewed

- **Base**: what the change is measured against, usually the default branch (`main`). If it is
  unclear, ask.
- **Head**: a commit, branch or tag. The default is `HEAD`.

The review copy holds **committed** work only. If the reviewer means uncommitted changes, say so,
and ask them to commit or stash first rather than guessing.

## 2. Make the review copy

Run from inside the repository:

```bash
python3 <skill-dir>/scripts/review_tour.py setup --base main --head HEAD --name <short-name>
```

It prints the review copy's path and the diff's size. It creates `<repo>-review-<name>` next to
the repository. It never changes the repository's branches, commits or remote, and it runs no git
hooks.

## 3. Read the whole change

Read all of it first: `git -C <review-copy> diff` covers modified files, and new files show in
full. Understand what the change does before deciding how to present it.

## 4. Choose the reading order: follow one flow

Pick the single path that best explains the change, such as one request, message, job or user
action, and follow it through the code in the order it runs. A typical shape:

1. **What and why.** A step with no file, then the design record if there is one.
2. **Where it starts.** The entry point, event, route or configuration the flow comes in through.
3. **Wiring.** Registration and configuration: how the pieces are connected.
4. **The flow itself**, in call order: each hop is a step.
5. **The failure paths**, where the flow can go wrong.
6. **Tests**, one step per seam or per test file, saying what each proves.
7. **Deployment and configuration**, **tooling**, then **docs and records**.
8. **A closing step**: the open questions, and anything deliberately left out of the tour.

Rules for the steps:

- **One step, one block**: a method, a class, a config section, a doc section. Keep a step to
  about 60 lines. Split a larger block where it has a natural seam, for example by giving each
  part of a method its own step.
- **Give every step an explicit `end` line.** The script can guess one, but only a person can be
  sure where the thought ends.
- **Every changed file appears in a step**, or is named in the closing step as not worth a visit.
  `finish` lists every changed file no step visits.

## 5. Write the steps

Each description says **what this block does in the flow, and why**. Keep it short, in plain
language, and use a list where there are several parts. Don't restate the code. End with
**Check:**, the one thing in that block that most needs the reviewer's judgement: a risky
decision, a departure from the spec, something untested. Say plainly what was not verified. Never
claim anything the code or a test does not show.

Write the draft to a scratch location, **not** into the repository:

```json
{
  "title": "#123 - short name of the change",
  "steps": [
    { "title": "Start here", "description": "What changed, in one paragraph. The flow this tour follows." },
    { "file": "src/orders/handler.py", "line": 40, "end": 72, "title": "Handling one order", "description": "... **Check:** ..." }
  ]
}
```

`line` and `end` are 1-based and inclusive, and paths are relative to the repository root.

## 6. Finish and check

```bash
python3 <skill-dir>/scripts/review_tour.py finish --worktree <review-copy> --draft <draft.json>
```

It writes the tour and a `.code-workspace` file that makes the highlight visible. It adds a
new-or-modified label and a diff link to every step, and prints the first and last line of each
step's range. **Read that output.** Fix any range that starts or stops mid-thought, cover or name
every file it lists as not visited, and run `finish` again. The tour lives in `.tours/`, which is
excluded from git, so it never shows up as a change or gets committed.

## 7. Hand over

Tell the reviewer:

- to open it with `code <review-copy>.code-workspace`;
- if CodeTour isn't installed, to run `code --install-extension vsls-contrib.codetour`;
- to start the tour from the **CodeTour** panel in the Explorer sidebar;
- that the gutter shows green for added, blue for modified and a red triangle for deleted lines;
- that each step's **⇄ Open this file's diff** link, or the file in **Source Control**, shows
  the side-by-side diff;
- **never to commit from the review copy.** Its base is the base branch, not theirs. Changes go
  on the real branch.

When they want a change, make it on the real branch. If the review should continue on the new
version, clean up and set up again.

## 8. Clean up when they are done

```bash
python3 <skill-dir>/scripts/review_tour.py cleanup --worktree <review-copy>
```

This removes the review copy and its workspace file. The repository's branches and commits are
untouched.
