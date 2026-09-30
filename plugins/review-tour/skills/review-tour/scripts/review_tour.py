#!/usr/bin/env python3
"""Review a change as a guided CodeTour in VS Code, with real diffs.

    review_tour.py setup   --base main --working-tree        [--name 136]   all changes, committed or not
    review_tour.py setup   --base HEAD~1 --head HEAD         [--name last]  one commit (or any range)
    review_tour.py finish  --worktree <path> [--draft <draft.json>]
    review_tour.py refresh --worktree <path>
    review_tour.py cleanup --worktree <path>

setup    Creates a review copy: a git worktree next to the repository, at the merge-base of --base
         and the change, with the change applied as UNCOMMITTED edits, so VS Code shows it as diffs
         (gutter markers, Source Control, "Open Changes"). The repository itself, its branches and
         its remote are never touched, and no git hooks run.
           --working-tree   the change is the repository's current state: every commit since the
                            merge-base plus staged, unstaged and untracked (not ignored) files.
           --head <commit>  the change is what that commit holds (a commit, branch or tag).

finish   Turns the draft - the steps in reading order - into the tour. Fills in each step's
         highlighted range, labels its file new / modified / deleted / unchanged, and links to the
         file's diff. Keeps the draft as <worktree>/.tours/draft.json (edit that one on updates),
         writes the tour and <worktree>.code-workspace, and prints where each step starts and ends.

refresh  Brings an existing review copy up to date: applies the change again as it is now, reports
         which files changed since the tour was written, and moves each step whose code moved.
         Steps it cannot place are reported as LOST; the draft is updated, the tour is not - edit
         the draft, then run finish again.

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

Standard library only; Python 3.9 or later, git 2.31 or later.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DIFF_LINK = "[⇄ Open this file's diff](command:git.openChange)"
LABELS = {
    "A": "🟢 **New file.** Everything highlighted is new.",
    "M": "🔵 **Modified file.** The highlight may mix old and new lines, so open the diff to see exactly what changed.",
    "D": "🔴 **Deleted file.** Open the diff to see what was removed.",
    None: "⚪ **Unchanged file**, shown for context.",
}
SEPARATOR = "\n\n---\n\n"
WORKSPACE_SETTINGS = {
    "workbench.colorCustomizations": {
        # CodeTour marks a step's lines as a text selection; make it visible, focused or not.
        "editor.selectionBackground": "#2b6cb088",
        "editor.inactiveSelectionBackground": "#2b6cb066",
    },
    "scm.diffDecorations": "all",
    "diffEditor.renderSideBySide": True,
}
TOURS = ".tours"
STATE = "review-tour.state.json"
DRAFT = "draft.json"
ANCHOR = "_anchor"


def git(*args, cwd=None, check=True, env=None):
    # Hooks off: a review copy must not run the repository's post-checkout or other hooks.
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd, capture_output=True, text=True, env=env,
    )
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    # Trailing newline only: `git status --porcelain` starts with a significant space.
    return result.stdout.rstrip("\n")


def zlist(output):
    return [item for item in output.split("\0") if item]


# ── Building the review copy ─────────────────────────────────────────────────────────────


def resolve(top, state):
    """The base commit and, for a commit review, the head commit - resolved now, from the refs."""
    if state["mode"] == "working-tree":
        head = git("rev-parse", "HEAD", cwd=top)
    else:
        head = git("rev-parse", "--verify", f"{state['headRef']}^{{commit}}", cwd=top)
    base = git("merge-base", state["baseRef"], head, cwd=top)
    return base, head


def apply_change(top, worktree, state):
    """Resets the review copy to the base, then lays the change on it as uncommitted edits."""
    base, head = resolve(top, state)
    git("reset", "-q", "--hard", base, cwd=worktree)
    git("clean", "-fdq", cwd=worktree)  # not -x: the ignored .tours/ stays

    if state["mode"] == "working-tree":
        # Everything that differs from the base, as it is on disk right now.
        changed = zlist(git("diff", "--name-only", "--no-renames", "-z", base, cwd=top))
        changed += zlist(git("ls-files", "--others", "--exclude-standard", "-z", cwd=top))
        for path in dict.fromkeys(changed):
            source, target = top / path, worktree / path
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif target.exists():
                target.unlink()
    else:
        git("checkout", head, "--", ".", cwd=worktree)
        for path in zlist(git("diff", "--name-only", "--no-renames", "--diff-filter=D", "-z", base, head, cwd=top)):
            if (worktree / path).exists():
                (worktree / path).unlink()

    git("reset", "-q", cwd=worktree)
    # New files as intent-to-add, so they show as all-green diffs rather than untracked files.
    untracked = zlist(git("ls-files", "--others", "--exclude-standard", "-z", cwd=worktree))
    if untracked:
        git("add", "-N", "--", *untracked, cwd=worktree)

    state.update(base=base, head=head, snapshot=snapshot(worktree))
    return state


def snapshot(worktree):
    """A git tree id of the review copy's content, so a later refresh can say what changed."""
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        git("add", "-A", ".", cwd=worktree, env=env)
        return git("write-tree", cwd=worktree, env=env)


def exclude_tours(top):
    """Keeps tours out of every status and every commit (shared by all worktrees of the repository)."""
    exclude = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=top)) / "info" / "exclude"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if f"{TOURS}/" not in lines:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("\n".join([*lines, f"{TOURS}/"]) + "\n")


def load_state(worktree):
    path = worktree / TOURS / STATE
    if not path.exists():
        sys.exit(f"{worktree} was not made by setup (no {TOURS}/{STATE}).")
    return json.loads(path.read_text())


def save_state(worktree, state):
    (worktree / TOURS).mkdir(exist_ok=True)
    (worktree / TOURS / STATE).write_text(json.dumps(state, indent=2) + "\n")


def setup(args):
    top = Path(git("rev-parse", "--show-toplevel"))
    if args.working_tree == bool(args.head):
        sys.exit("Say what to review: --working-tree (all changes, committed or not) or --head <commit>.")

    state = {
        "repository": str(top),
        "mode": "working-tree" if args.working_tree else "commit",
        "baseRef": args.base,
        "headRef": args.head,
    }
    base, head = resolve(top, state)
    if state["mode"] == "commit" and base == head:
        sys.exit(f"{args.head} has no changes relative to {args.base}.")
    name = args.name or git("rev-parse", "--short", head, cwd=top)
    worktree = top.parent / f"{top.name}-review-{name}"
    if worktree.exists():
        sys.exit(f"{worktree} already exists. Use refresh to update it, or cleanup first.")

    exclude_tours(top)
    git("worktree", "add", "--detach", str(worktree), base, cwd=top)
    state = apply_change(top, worktree, state)
    save_state(worktree, state)

    print(json.dumps({
        "worktree": str(worktree),
        "reviewing": ("all changes since the merge-base, committed or not"
                      if state["mode"] == "working-tree" else f"{args.head} against {args.base}"),
        "base": base,
        "diff": git("diff", "--shortstat", cwd=worktree) or "no changes",
    }, indent=2))


# ── Writing the tour ─────────────────────────────────────────────────────────────────────


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


def read_lines(path):
    return path.read_text(encoding="utf-8", errors="replace").split("\n")


def without_label(description):
    """The draft's own text, if a finished step's label and link were pasted back into it."""
    if description.startswith(tuple(LABELS.values())) and SEPARATOR in description:
        return description.split(SEPARATOR, 1)[1]
    return description


def finish(args):
    worktree = Path(args.worktree).resolve()
    state = load_state(worktree)
    stored = worktree / TOURS / DRAFT
    draft_path = Path(args.draft).resolve() if args.draft else stored
    if not draft_path.exists():
        sys.exit(f"No draft: pass --draft, or write {stored}.")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    status = status_of(worktree)
    problems, report, steps = [], [], []

    for number, step in enumerate(draft["steps"], 1):
        step["description"] = without_label(step.get("description", ""))
        path = step.get("file")
        if not path:
            step.pop(ANCHOR, None)
            steps.append(dict(step))
            continue

        source = worktree / path
        if not source.is_file():
            problems.append(f"step {number}: {path} does not exist in the review copy")
            continue
        lines = read_lines(source)
        start = int(step["line"])
        if not 1 <= start <= len(lines):
            problems.append(f"step {number}: line {start} is outside {path} ({len(lines)} lines)")
            continue
        end = int(step.get("end") or 0) or guess_end(lines, start - 1) + 1
        end = max(start, min(end, len(lines)))
        while end > start and not lines[end - 1].strip():
            end -= 1
        step["end"] = end

        tour_step = {key: value for key, value in step.items() if key not in ("end", ANCHOR)}
        tour_step["selection"] = {
            "start": {"line": start, "character": 1},
            "end": {"line": end, "character": len(lines[end - 1]) + 1},
        }
        tour_step["description"] = f"{LABELS[status.get(path)]} {DIFF_LINK}{SEPARATOR}{step['description']}"
        steps.append(tour_step)
        # Kept in the draft, not the tour: what refresh looks for to find the block again.
        step[ANCHOR] = {"file": path, "line": start, "end": end,
                        "startText": lines[start - 1].strip(), "endText": lines[end - 1].strip()}
        report.append(f"{number:3} {step.get('title', '')[:40]:40} {path}:{start}-{end}\n"
                      f"      starts: {lines[start - 1].strip()[:90]}\n"
                      f"      ends:   {lines[end - 1].strip()[:90]}")

    if problems:
        sys.exit("Not written:\n  " + "\n  ".join(problems))

    title = draft.get("title") or f"Review of {worktree.name}"
    tour_file = worktree / TOURS / f"{re.sub(r'[^A-Za-z0-9._-]+', '-', title).strip('-').lower()[:60]}.tour"
    if state.get("tour") and state["tour"] != str(tour_file) and Path(state["tour"]).exists():
        Path(state["tour"]).unlink()  # the title changed: one tour per review copy
    tour_file.write_text(json.dumps({"$schema": "https://aka.ms/codetour-schema", "title": title, "steps": steps},
                                    indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stored.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    workspace = worktree.parent / f"{worktree.name}.code-workspace"
    workspace.write_text(json.dumps({"folders": [{"path": worktree.name}], "settings": WORKSPACE_SETTINGS},
                                    indent=2) + "\n", encoding="utf-8")

    # The draft now matches this state of the review copy; a refresh measures from here.
    state.update(tour=str(tour_file), draftSnapshot=state["snapshot"])
    save_state(worktree, state)

    print("\n".join(report))
    visited = {step["file"] for step in steps if step.get("file")}
    missing = sorted(path for path in status if path not in visited)
    if missing:
        print(f"\nChanged but not in any step ({len(missing)}) - add a step, or name them in the closing step:")
        print("\n".join(f"  {status[path]} {path}" for path in missing))
    print(f"\n{len(steps)} steps -> {tour_file}\nDraft kept at {stored}\nOpen with: code {workspace}")


# ── Updating an existing tour ────────────────────────────────────────────────────────────


def place(lines, anchor):
    """Where the anchored block is now: (start, end) 1-based, or None when its first line is gone."""
    candidates = [index + 1 for index, line in enumerate(lines) if line.strip() == anchor["startText"]]
    if not candidates:
        return None
    start = min(candidates, key=lambda line: abs(line - anchor["line"]))
    end = start + (anchor["end"] - anchor["line"])
    # The block may have grown or shrunk: prefer the old last line, if it is still near.
    near = [index + 1 for index, line in enumerate(lines)
            if line.strip() == anchor["endText"] and start <= index + 1 <= start + 3 * (anchor["end"] - anchor["line"] + 10)]
    if near:
        end = min(near, key=lambda line: abs(line - end))
    return start, min(end, len(lines))


def refresh(args):
    worktree = Path(args.worktree).resolve()
    state = load_state(worktree)
    if "draftSnapshot" not in state:
        sys.exit("No tour has been finished in this review copy yet: run finish first.")
    top = Path(state["repository"])
    before = state["draftSnapshot"]
    state = apply_change(top, worktree, state)

    changed = {}
    for line in git("diff", "--name-status", "--no-renames", before, state["snapshot"], cwd=worktree).splitlines():
        code, path = line.split("\t", 1)
        changed[path] = code
    if not changed:
        save_state(worktree, state)
        print("Nothing changed since the draft was last matched to the code.")
        return

    print(f"Changed since the draft was last matched to the code ({len(changed)}):")
    print("\n".join(f"  {code} {path}" for path, code in sorted(changed.items())))

    draft_path = worktree / TOURS / DRAFT
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    print("\nSteps:")
    for number, step in enumerate(draft["steps"], 1):
        anchor = step.get(ANCHOR)
        if not step.get("file"):
            continue
        if anchor is None or anchor["file"] != step["file"]:
            print(f"  {number:3} {step.get('title', '')[:40]:40} NEW - not placed by a finish yet")
            continue
        title = step.get("title", "")[:40]
        if anchor["file"] not in changed:
            print(f"  {number:3} {title:40} unchanged")
            continue
        source = worktree / anchor["file"]
        if not source.is_file():
            print(f"  {number:3} {title:40} LOST - {anchor['file']} no longer exists")
            continue
        placed = place(read_lines(source), anchor)
        if placed is None:
            print(f"  {number:3} {title:40} LOST - its first line is gone from {anchor['file']}")
            continue
        start, end = placed
        step["line"], step["end"] = start, end
        lines = read_lines(source)
        step[ANCHOR] = {**anchor, "line": start, "end": end,
                        "startText": lines[start - 1].strip(), "endText": lines[end - 1].strip()}
        moved = "" if (start, end) == (anchor["line"], anchor["end"]) else f", was {anchor['line']}-{anchor['end']}"
        print(f"  {number:3} {title:40} REVIEW - file changed; now {start}-{end}{moved}")

    draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # The draft now matches this state; LOST steps keep their old anchor until they are rewritten.
    state["draftSnapshot"] = state["snapshot"]
    save_state(worktree, state)
    print(f"\nDraft updated: {draft_path}\nRewrite what the REVIEW and LOST steps say, add steps for new code, "
          "then run finish (without --draft).")


def cleanup(args):
    worktree = Path(args.worktree).resolve()
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=worktree)
    git("worktree", "remove", "--force", str(worktree), cwd=Path(common).parent)
    workspace = worktree.parent / f"{worktree.name}.code-workspace"
    if workspace.exists():
        workspace.unlink()
    print(f"Removed {worktree} and its workspace file.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    setup_parser = commands.add_parser("setup", help="create the review copy")
    setup_parser.add_argument("--base", required=True, help="what the change is measured against, e.g. main or HEAD~1")
    change = setup_parser.add_mutually_exclusive_group()
    change.add_argument("--working-tree", action="store_true", help="the change is the repository's current state")
    change.add_argument("--head", help="the change is what this commit, branch or tag holds")
    setup_parser.add_argument("--name", help="suffix for the review folder (default: the head's short id)")
    setup_parser.set_defaults(run=setup)

    finish_parser = commands.add_parser("finish", help="write the tour and the workspace file")
    finish_parser.add_argument("--worktree", required=True)
    finish_parser.add_argument("--draft", help="a new draft; without it, the draft kept in the review copy")
    finish_parser.set_defaults(run=finish)

    refresh_parser = commands.add_parser("refresh", help="update the review copy and re-place the steps")
    refresh_parser.add_argument("--worktree", required=True)
    refresh_parser.set_defaults(run=refresh)

    cleanup_parser = commands.add_parser("cleanup", help="remove the review copy")
    cleanup_parser.add_argument("--worktree", required=True)
    cleanup_parser.set_defaults(run=cleanup)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
