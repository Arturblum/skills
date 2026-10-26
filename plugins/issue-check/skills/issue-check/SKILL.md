---
name: issue-check
description: "Check a GitHub issue before work starts: can it be implemented, what blocks it in the code or in other open issues and PRs, is the description still accurate, is it still relevant. Use it when the user gives an issue link or number and asks whether it is ready, doable, blocked, outdated or needs an update to its description."
---

# Issue check

A pre-implementation audit of one issue. The issue was true on the day it was written; the code and the other issues have moved since. Find where they diverge, and report a verdict the user can act on.

Read-only. Report findings and a proposed description; edit, comment on or relabel the issue only when the user says so.

## Process

1. **Read the whole issue.** `gh issue view <n> --comments` (labels, state, assignees, linked PRs and issues included). Comments often hold decisions that supersede the body: read them as part of the spec.
   Done when you can state the goal and the acceptance criteria in your own words, including every change the comments made.

2. **Extract the claims.** A _claim_ is anything the issue says that the code can confirm or refute: a file, class, route, queue, field or config key it names; a behaviour it calls current ("today X does Y"); a prerequisite it assumes; each acceptance criterion.
   Done when every claim is on a list.

3. **Check each claim against the code** on the default branch, freshly fetched. Quote the file and line you found. Give each claim one verdict:
   - **holds**: the code matches.
   - **stale**: it was true once; the code moved (renamed, relocated, rewritten).
   - **wrong**: it never matched the code.
   - **unverifiable**: nothing in the repo can confirm it. Say what would.

   Done when no claim lacks a verdict and a location.

4. **Check relevance.** Look for the work already done or made moot: `git log --all --grep` the issue number and its key terms, merged and open PRs that reference it, the decision records and docs the repo keeps (ADRs, architecture docs, AGENTS.md / CLAUDE.md), and acceptance criteria the code already satisfies.
   Done when you can say which of these holds: **open and needed**, **partly done** (name what remains), **done**, **superseded** (name by what), or **obsolete**.

5. **Hunt blockers**, in two places. A _blocker_ is something that makes starting now wrong or wasteful.
   - **In the code**: a missing prerequisite (an API, contract, schema, library, infrastructure the work builds on); a conflict with an approved decision; an in-flight refactor of the same area; a constraint from the repo's own rules.
   - **In open issues and PRs**: start from the issue's declared blockers: GitHub's native dependencies (`gh api repos/<owner>/<repo>/issues/<n>/dependencies/blocked_by`; `issue_dependencies_summary.blocked_by` on the issue counts the open ones), any "blocked by" line in the body or comments, and a map or parent issue's task list. Then search for undeclared ones (`gh issue list --state open --search`, `gh pr list --state open --search`, using the issue's key terms and the names of the files and types it touches). Read each candidate and classify it as **blocks** (must land first), **overlaps** (same area; coordinate or merge), **duplicate**, or **adjacent** (harmless; mention only if it changes the approach).
   Done when every candidate has a classification with a reason, and "none found" names the searches that found nothing.

6. **Decide the verdict**, one of:
   - **Ready**: implementable as written.
   - **Ready after update**: implementable once the description is corrected.
   - **Blocked**: name each blocker and who or what clears it.
   - **Not relevant**: done, superseded or obsolete; recommend closing and say why.

   Feasibility is a judgement on what the code and the rules allow, not only on whether a path exists: name the main design choice or risk the implementer will meet.

7. **Check the description.** Compare what the issue says with what steps 3-5 showed. List each drift: stale references, missing acceptance criteria that comments settled, scope that moved, new constraints.
   Done when every `stale` or `wrong` claim, and every decision buried in the comments, is either fixed in a proposed rewrite or marked as intentionally kept.

## Report

Lead with the verdict and the one-sentence reason. Then:

- **Blockers**: each with its link and classification. Omit the section when there are none, and say "no blockers" in the verdict line.
- **Claims that no longer hold**: a table of claim, verdict, evidence (`path:line`).
- **Relevance**: the step 4 conclusion with its evidence.
- **Proposed description**: only the changed parts, as before and after, so the user can approve the edit. Say "description is current" when step 7 found no drift.

End with the next step, and apply nothing before the answer:

- When step 7 found drift (any `stale` or `wrong` claim, a decision buried in comments, a missing criterion) or the report names open design choices, suggest `/rewrite-issue-after-check`. It is user-invoked, so name it for the user to run; it carries these findings into the issue.
- When the description is current, ask only whether to comment or relabel the issue.
