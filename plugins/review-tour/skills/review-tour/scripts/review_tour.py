#!/usr/bin/env python3
"""Review a change as a guided CodeTour in VS Code, with real diffs.

    review_tour.py setup   --base main [--head HEAD] [--name 136]
    review_tour.py finish  --worktree <path> --draft <draft.json> [--title "..."]
    review_tour.py cleanup --worktree <path>

setup    Creates a review copy: a git worktree next to the repository, at the merge-base of
         --base and --head, with everything --head changed applied as UNCOMMITTED edits. VS Code
         then shows the change as diffs (gutter markers, Source Control, "Open Changes").
         The repository itself, its branches and its remote are not touched.

finish   Turns a draft - the steps in reading order - into the tour. For every step it fills in
         the highlighted range, labels the file new / modified / deleted / unchanged, and adds a
         link that opens the file's diff. It writes <worktree>/.tours/<name>.tour (git-ignored
         through .git/info/exclude), writes <worktree>.code-workspace, and prints the line each
         step starts and ends on, so the ranges can be checked.

cleanup  Removes the review copy and its workspace file. Branches and commits are untouched.

Draft format (JSON):
    {
      "title": "optional tour title",
      "steps": [
        {"title": "Start here", "description": "markdown - a step with no file is an intro"},
        {"file": "src/app.py", "line": 12, "end": 40, "title": "...", "description": "..."}
      ]
    }
"line" and "end" are 1-based and inclusive. Give "end" explicitly: the fallback that guesses it
(the matching bracket, or the next Markdown heading) is only a heuristic.

Standard library only; Python 3.9 or later.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DIFF_LINK = "[⇄ Open this file's diff](command:git.openChange)"
LABELS = {
    "A": "🟢 **New file.** Everything highlighted is new.",
    "M": "🔵 **Modified file.** The highlight may mix old and new lines, so open the diff to see exactly what changed.",
    "D": "🔴 **Deleted file.** Open the diff to see what was removed.",
    None: "⚪ **Unchanged file**, shown for context.",
}
WORKSPACE_SETTINGS = {
    "workbench.colorCustomizations": {
        # CodeTour marks a step's lines as a text selection; make it visible, focused or not.
        "editor.selectionBackground": "#2b6cb088",
        "editor.inactiveSelectionBackground": "#2b6cb066",
    },
    "scm.diffDecorations": "all",
    "diffEditor.renderSideBySide": True,
}


def git(*args, cwd=None, check=True):
    # Hooks off: a review copy must not run the repository's post-checkout or other hooks.
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd, capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    # Trailing newline only: `git status --porcelain` starts with a significant space.
    return result.stdout.rstrip("\n")


def setup(args):
    top = Path(git("rev-parse", "--show-toplevel"))
    head = git("rev-parse", "--verify", f"{args.head}^{{commit}}")
    base = git("merge-base", args.base, head)
    if base == head:
        sys.exit(f"{args.head} has no changes relative to {args.base}.")

    dirty = git("status", "--porcelain", "--untracked-files=no", cwd=top)
    if dirty and args.head == "HEAD":
        print("Note: uncommitted changes in the repository are NOT included - commit or stash them "
              "first if they belong in the review.", file=sys.stderr)

    name = args.name or git("rev-parse", "--short", head)
    worktree = top.parent / f"{top.name}-review-{name}"
    if worktree.exists():
        sys.exit(f"{worktree} already exists. Run cleanup first, or pass another --name.")

    git("worktree", "add", "--detach", str(worktree), base, cwd=top)

    # Apply the change without committing it: every file --head has, then remove what it deleted.
    git("checkout", head, "--", ".", cwd=worktree)
    for path in git("diff", "--no-renames", "--name-only", "--diff-filter=D", base, head, cwd=top).splitlines():
        target = worktree / path
        if target.exists():
            target.unlink()
    git("reset", "-q", cwd=worktree)

    # New files as intent-to-add, so they show as all-green diffs rather than untracked files.
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", cwd=worktree).split("\0")
    untracked = [path for path in untracked if path]
    if untracked:
        git("add", "-N", "--", *untracked, cwd=worktree)

    # Keep tours out of every status and every commit (shared by all worktrees of the repository).
    exclude = Path(git("rev-parse", "--git-common-dir", cwd=top))
    exclude = (exclude if exclude.is_absolute() else top / exclude) / "info" / "exclude"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if ".tours/" not in lines:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("\n".join([*lines, ".tours/"]) + "\n")

    stat = git("diff", "--shortstat", cwd=worktree) or "no changes"
    print(json.dumps({
        "worktree": str(worktree),
        "base": base,
        "head": head,
        "diff": stat,
        "reviewedDiff": f"git diff {base[:12]}...{head[:12]}",
    }, indent=2))


def status_of(worktree):
    status = {}
    for line in git("status", "--porcelain", "--no-renames", cwd=worktree).splitlines():
        code = line[:2].strip()
        status[line[3:]] = "A" if code in ("A", "??") else "D" if "D" in code else "M"
    return status


def guess_end(lines, start):
    """0-based index of the last line of the block starting at `start`. A fallback only."""
    if lines[start].lstrip("> ").startswith("#"):
        level = len(re.match(r"#+", lines[start].lstrip("> ")).group(0))
        for index in range(start + 1, len(lines)):
            heading = re.match(r"(#+) ", lines[index])
            if heading and len(heading.group(1)) <= level:
                return index - 1
        return len(lines) - 1

    depth, opened = 0, False
    for index in range(start, len(lines)):
        for char in lines[index]:
            # Braces and brackets only: a signature's parentheses close on its own line.
            if char in "{[":
                depth, opened = depth + 1, True
            elif char in "}]":
                depth -= 1
        if opened and depth <= 0:
            return index
        if not opened and index > start and lines[index].rstrip().endswith(";"):
            return index
    return start


def finish(args):
    worktree = Path(args.worktree).resolve()
    draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    status = status_of(worktree)
    problems, report, steps = [], [], []

    for number, step in enumerate(draft["steps"], 1):
        step = dict(step)
        path = step.get("file")
        if path:
            source = worktree / path
            if not source.is_file():
                problems.append(f"step {number}: {path} does not exist in the review copy")
                continue
            lines = source.read_text(encoding="utf-8", errors="replace").split("\n")
            start = int(step["line"])
            if not 1 <= start <= len(lines):
                problems.append(f"step {number}: line {start} is outside {path} ({len(lines)} lines)")
                continue
            end = int(step.pop("end", 0)) or guess_end(lines, start - 1) + 1
            end = max(start, min(end, len(lines)))
            while end > start and not lines[end - 1].strip():
                end -= 1
            step["selection"] = {
                "start": {"line": start, "character": 1},
                "end": {"line": end, "character": len(lines[end - 1]) + 1},
            }
            label = LABELS[status.get(path)]
            step["description"] = f"{label} {DIFF_LINK}\n\n---\n\n{step.get('description', '')}"
            report.append(f"{number:3} {step.get('title', '')[:40]:40} {path}:{start}-{end}\n"
                          f"      starts: {lines[start - 1].strip()[:90]}\n"
                          f"      ends:   {lines[end - 1].strip()[:90]}")
        steps.append(step)

    if problems:
        sys.exit("Not written:\n  " + "\n  ".join(problems))

    title = args.title or draft.get("title") or f"Review of {worktree.name}"
    tour = {"$schema": "https://aka.ms/codetour-schema", "title": title, "steps": steps}
    tour_file = worktree / ".tours" / f"{re.sub(r'[^A-Za-z0-9._-]+', '-', title).strip('-').lower()[:60]}.tour"
    tour_file.parent.mkdir(exist_ok=True)
    tour_file.write_text(json.dumps(tour, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    workspace = worktree.parent / f"{worktree.name}.code-workspace"
    workspace.write_text(json.dumps({
        "folders": [{"path": worktree.name}],
        "settings": WORKSPACE_SETTINGS,
    }, indent=2) + "\n", encoding="utf-8")

    print("\n".join(report))

    # Every changed file should be visited, or named in the closing step on purpose.
    visited = {step["file"] for step in steps if step.get("file")}
    missing = sorted(path for path in status if path not in visited and not path.startswith(".tours/"))
    if missing:
        print(f"\nChanged but not in any step ({len(missing)}) - add a step, or name them in the closing step:")
        print("\n".join(f"  {status[path]} {path}" for path in missing))

    print(f"\n{len(steps)} steps -> {tour_file}\nOpen with: code {workspace}")


def cleanup(args):
    worktree = Path(args.worktree).resolve()
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=worktree)
    repository = Path(common).parent
    git("worktree", "remove", "--force", str(worktree), cwd=repository)
    workspace = worktree.parent / f"{worktree.name}.code-workspace"
    if workspace.exists():
        workspace.unlink()
    print(f"Removed {worktree} and its workspace file.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    setup_parser = commands.add_parser("setup", help="create the review copy")
    setup_parser.add_argument("--base", required=True, help="what the change is measured against, e.g. main")
    setup_parser.add_argument("--head", default="HEAD", help="the change: a commit, branch or tag (default HEAD)")
    setup_parser.add_argument("--name", help="suffix for the review folder (default: the head's short id)")
    setup_parser.set_defaults(run=setup)

    finish_parser = commands.add_parser("finish", help="write the tour and the workspace file")
    finish_parser.add_argument("--worktree", required=True)
    finish_parser.add_argument("--draft", required=True)
    finish_parser.add_argument("--title")
    finish_parser.set_defaults(run=finish)

    cleanup_parser = commands.add_parser("cleanup", help="remove the review copy")
    cleanup_parser.add_argument("--worktree", required=True)
    cleanup_parser.set_defaults(run=cleanup)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
