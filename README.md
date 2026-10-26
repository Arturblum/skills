# Skills for Claude Code

Skills for [Claude Code](https://code.claude.com), published as a plugin marketplace.

| Skill | What it does |
|---|---|
| [review-tour](plugins/review-tour/skills/review-tour/SKILL.md) | Review a code change in the order it runs, as a guided tour in VS Code with real diffs |
| [flow-diff](plugins/flow-diff/skills/flow-diff/SKILL.md) | Draw a before/after flow diff of a design change as swimlane diagrams, to approve before any code is written |
| [issue-check](plugins/issue-check/skills/issue-check/SKILL.md) | Check a GitHub issue before work starts: feasibility, blockers in the code and in open issues, whether the description is current and the issue still relevant |
| [explain-issue](plugins/explain-issue/skills/explain-issue/SKILL.md) | Explain a GitHub issue in plain words, with context from the code and the ADRs, so you understand it fast |

## Install

In Claude Code:

```
/plugin marketplace add Arturblum/skills
/plugin install review-tour@arturblum-skills
/plugin install flow-diff@arturblum-skills
/plugin install issue-check@arturblum-skills
/plugin install explain-issue@arturblum-skills
```

Then run `/review-tour:review-tour` in the repository you want to review. It only runs when you
ask for it: Claude never starts it on its own.

If you'd rather not install a plugin, copy the skill folder into your personal skills folder
instead. It is then available as `/review-tour`:

```bash
git clone https://github.com/Arturblum/skills.git
cp -R skills/plugins/review-tour/skills/review-tour ~/.claude/skills/
```

## review-tour

A change is easiest to review in the order it **runs**, not in the order its files are listed.
Run the skill in a repository, and it will:

1. **Ask what to review**: only the **last commit**, or **all changes on the branch** compared to
   `main`, committed or not. It also asks **how deep** the tour should go:
   - **1 (low)**: only the main flow, with a few sentences per step;
   - **2 (medium)**, the default: the whole flow, plus tests, configuration and docs;
   - **3 (high)**: every changed block, with the full reasoning, the alternatives considered and
     the edge cases.
2. **Make a review copy** of the repository: a git worktree at the base branch, with the change
   applied as uncommitted edits. VS Code then shows the change as real diffs. Your branch, its
   commits and its remote are not touched.
3. **Gather the context**: why the change was made. It reads the issue, the pull request, the
   commit messages and the docs. If Claude wrote the change in the same conversation, it also uses
   what it remembers from writing it.
4. **Read the change** and work out the order it runs in: where it starts, how it's wired, the
   flow itself, the failure paths, then tests, configuration and docs.
5. **Write a [CodeTour](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour)**
   in that order. It opens with the problem, the approach and where to look hardest. Then each
   step:
   - highlights exactly one block, so you know where to stop reading;
   - explains in plain words **why** the block exists and why it was written this way;
   - says whether the file is 🟢 new or 🔵 modified;
   - links to that file's side-by-side diff;
   - ends with **Check:**, the one thing there most worth your judgement.
6. **Update the tour** when the code changes: run the skill again and ask for an update. It
   moves each step to where its code is now, and tells Claude which steps changed, which code is
   new and which is gone, so only those are rewritten. You can also ask for a different depth.
7. **Clean up** when you're done.

### Requirements

- VS Code with the CodeTour extension: `code --install-extension vsls-contrib.codetour`
- git 2.31 or later
- Python 3.9 or later. The script uses the standard library only.

### Using the tour

1. Open the workspace file Claude gives you: `code <repo>-review-<name>.code-workspace`.
2. In the Explorer sidebar, open the **CodeTour** panel and start the tour.
3. In the gutter, green is added, blue is modified, and a red triangle marks deleted lines.
4. **⇄ Open this file's diff**, or the file in **Source Control**, shows the side-by-side diff.

**Don't commit from the review copy.** Its base is the base branch, not yours. Make changes on
your real branch.

## issue-check

Give Claude an issue link or number and ask whether it can be implemented. Claude can start it on
its own from that kind of question, and it only reads: it changes nothing on the issue until you
say so. It will:

1. Read the issue and its comments, and list every **claim** the code can confirm or refute: files,
   routes and fields named, behaviour called current, each acceptance criterion.
2. Check each claim against the default branch and mark it **holds**, **stale**, **wrong** or
   **unverifiable**, with `path:line` evidence.
3. Check **relevance**: already done, partly done, superseded or obsolete, from the git log, PRs
   and the repo's decision records.
4. Hunt **blockers** in the code (missing prerequisites, conflicts with decisions) and in open
   issues and PRs (blocks, overlaps, duplicates).
5. Give a verdict (ready, ready after update, blocked, not relevant) and a proposed description
   as before and after, then ask whether to update the issue.

Needs the [GitHub CLI](https://cli.github.com) (`gh`), signed in.

## explain-issue

Give Claude an issue link or number and ask it to explain the task. Claude can start it on its own
from that kind of request, and it only reads. It works in the vocabulary of
[mattpocock/skills](https://github.com/mattpocock/skills): the glossary (`knowledge/CONTEXT.md`),
ADRs, seams, tracer bullets and the frontier. It will:

1. Read the issue, its comments, its spec or map, its sibling tickets and its blockers.
2. Look up the glossary terms and ADRs in the area, and locate the code the issue names.
3. Check the issue's "today it does X" claims against the code, and say where they disagree.
4. Explain, on about one screen: the ask in one sentence; why it exists as a timeline with real
   system names and example times, plus an analogy; where it lands in the code; what the ADRs
   already decided; what is still open, with the cost of each option and a recommendation; and how
   to start, as the thinnest slice first.
5. Offer `/grill-with-docs` for the open question, or `/issue-check` if the issue looks stale.

Needs the [GitHub CLI](https://cli.github.com) (`gh`), signed in.

## Licence

[MIT](LICENSE)
