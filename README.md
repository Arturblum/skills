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

Then ask Claude to walk you through a change, or run `/review-tour:review-tour`.

If you'd rather not install a plugin, copy the skill folder into your personal skills folder
instead. It is then available as `/review-tour`:

```bash
git clone https://github.com/Arturblum/skills.git
cp -R skills/plugins/review-tour/skills/review-tour ~/.claude/skills/
```

## review-tour

A change is easiest to review in the order it **runs**, not in the order its files are listed.
Ask Claude to review a branch, commit or pull request, and it will:

1. **Make a review copy** of the repository: a git worktree at the base branch, with the change
   applied as uncommitted edits. VS Code then shows the change as real diffs. Your branch, its
   commits and its remote are not touched.
2. **Read the change** and work out the order it runs in: where it starts, how it's wired, the
   flow itself, the failure paths, then tests, configuration and docs.
3. **Write a [CodeTour](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour)**
   in that order. Each step:
   - highlights exactly one block, so you know where to stop reading;
   - says whether the file is 🟢 new or 🔵 modified;
   - links to that file's side-by-side diff;
   - ends with **Check:**, the one thing there most worth your judgement.
4. **Clean up** when you're done.

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
