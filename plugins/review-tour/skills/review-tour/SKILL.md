---
name: review-tour
description: Walk a reviewer through a code change in the order it actually runs, as a CodeTour in VS Code with real diffs - each step highlights one block, labels the file new or modified, and links to its diff. Creates a tour of the last commit or of all changes on the branch, and updates an existing tour when the code has moved on.
disable-model-invocation: true
---

# Review tour

A change is easiest to review in the order it **runs**, not in the order files are listed. This
skill builds that order as a [CodeTour](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour)
inside a **review copy** of the repository. The review copy is a git worktree at the base, with
the change applied as uncommitted edits, so VS Code shows the change as real diffs. Each step
highlights exactly one block, says whether its file is new or modified, and links to that file's
diff. The reviewer reads the highlight and stops where it ends.

The mechanical parts are in `scripts/review_tour.py`, in this skill's base directory. Reading the
change, choosing the order and writing the steps are yours.

First decide which of the two jobs this is:

- **A new tour.** Follow steps 1-8.
- **Updating a tour** that already exists, because the code has changed since it was written.
  Follow *Updating a tour* below. The signs: the reviewer says "update the tour", or a review copy
  for this repository already exists next to it (`<repo>-review-*` with a `.tours/` folder).

## 1. Ask what to review

Unless the reviewer already said, **ask** which of these they want, and never guess:

- **The last commit only**: just what changed most recently. Good for a follow-up review, when they
  have already been through the rest.
- **All changes on the branch**: everything that differs from the base branch (usually `main`),
  committed or not. Good for a first review, or a final one before merging.

If they name something else, such as a specific commit, a range or a pull request's base, use
that. Confirm the base branch if the repository's default is unclear.

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
  about 60 lines. Split a larger block where it has a natural seam.
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

Write the first draft to a scratch location, **not** into the repository:

```json
{
  "title": "#123 - short name of the change",
  "steps": [
    { "title": "Start here", "description": "What changed, in one paragraph. The flow this tour follows." },
    { "file": "src/orders/handler.py", "line": 40, "end": 72, "title": "Handling one order", "description": "... **Check:** ..." }
  ]
}
```

`line` and `end` are 1-based and inclusive, and paths are relative to the repository root. Say in
the first step which change the tour covers: the last commit, or all changes against the base.

## 6. Finish and check

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

## 7. Hand over

Tell the reviewer:

- to open it with `code <review-copy>.code-workspace`;
- if CodeTour isn't installed, to run `code --install-extension vsls-contrib.codetour`;
- to start the tour from the **CodeTour** panel in the Explorer sidebar;
- that the gutter shows green for added, blue for modified and a red triangle for deleted lines;
- that each step's **⇄ Open this file's diff** link, or the file in **Source Control**, shows the
  side-by-side diff;
- **never to commit from the review copy.** Its base is the base branch, not theirs. Changes go
  on the real branch;
- that when the code changes, they can ask for the tour to be **updated**.

## 8. Clean up when they are done

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

2. **Read what changed**, with `git -C <review-copy> diff` for the files it listed, and **edit
   `.tours/draft.json`**:
   - rewrite the REVIEW and LOST steps whose meaning changed;
   - add steps for new code, in flow order;
   - remove steps for code that no longer exists;
   - update the first step, so it says what this revision of the tour covers.

3. **Run `finish` without `--draft`**, read its output as in step 6, and fix what it reports.

4. **Tell the reviewer what changed in the tour**: which steps are new, rewritten or removed.
   CodeTour picks up the new tour file. If it doesn't, they reload the window (**Developer:
   Reload Window**).

If the reviewer wants a different scope, such as switching from the last commit to all changes,
don't refresh. Clean up, then set up again with the new mode.
