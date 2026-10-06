# Skills for Claude Code

Skills for [Claude Code](https://code.claude.com), published as a plugin marketplace.

| Skill | What it does |
|---|---|
| [review-tour](plugins/review-tour/skills/review-tour/SKILL.md) | Review a code change in the order it runs, as a guided tour in VS Code with real diffs |

## Install

In Claude Code:

```
/plugin marketplace add Arturblum/skills
/plugin install review-tour@arturblum-skills
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

## Licence

[MIT](LICENSE)
