---
name: issue-check
description: "Audit a GitHub issue before work starts. Use when the user gives an issue link or number and asks whether it is ready, blocked, still relevant, or needs a description update."
---

# Issue check

The issue was true on the day it was written; the code, the ADRs and the other issues have moved since. Find where they diverge.

Read-only: report findings and a proposed description. Edit, comment on or relabel the issue only when the user says so.

## Process

1. **Read the whole issue.** `gh issue view <n> --comments` (labels, state, assignees, linked PRs and issues included). Comments often hold decisions that supersede the body: read them as part of the spec.
   Done when you can state the goal and the acceptance criteria in your own words, including every change the comments made.

2. **Extract the claims.** A _claim_ is anything the issue says that the code can confirm or refute: a file, class, route, queue, field or config key it names; a behaviour it calls current ("today X does Y"); a prerequisite it assumes; each acceptance criterion.
   Done when every name, every "today" statement, every prerequisite and every acceptance criterion in the issue has a line on the list.

3. **Check each claim against the code** on the default branch, freshly fetched. One verdict per claim, with evidence as `path:line`:
   - **holds**: the code matches.
   - **stale**: it was true once; the code moved (renamed, relocated, rewritten).
   - **wrong**: it never matched the code.
   - **unverifiable**: nothing in the repo can confirm it. Say what would.

   Done when every claim has a verdict and a location.

4. **Read the decisions.** Find the ADRs that touch the area: search the ADR folder for the issue's key terms and the names of the files and types it touches. Only `accepted` ADRs bind; flag a `proposed` one as a risk; `superseded` and `deprecated` ones are history. Classify each ADR:
   - **conflicts**: the issue asks for what the ADR rejected or forbids.
   - **constrains**: the issue is allowed, but must follow the ADR's chosen approach.
   - **depends**: the ADR's decision must be implemented or accepted first.
   - **supersedes**: the ADR made the issue moot.
   - **unrelated**.

   Done when every ADR found has a classification with a reason, and "none found" names the folder and the terms searched.

5. **Check relevance.** Find the work already done or made moot: `git log --all --grep` the issue number and its key terms, merged and open PRs that reference it, the repo's architecture docs and AGENTS.md / CLAUDE.md, the `supersedes` ADRs from step 4, and acceptance criteria the code already satisfies.
   Done when one of these holds, with evidence: **open and needed**, **partly done** (name what remains), **done**, **superseded** (name by what), or **obsolete**.

6. **Hunt blockers.** A _blocker_ is something that makes starting now wrong or wasteful. It comes from three places:
   - **The code**: a missing prerequisite (an API, contract, schema, library, infrastructure the work builds on); an in-flight refactor of the same area; a constraint from AGENTS.md / CLAUDE.md.
   - **The ADRs**: every `conflicts` and every `depends` from step 4 whose dependency is unmet.
   - **Open issues and PRs**: start from the declared blockers: GitHub's native dependencies (`gh api repos/<owner>/<repo>/issues/<n>/dependencies/blocked_by`; `issue_dependencies_summary.blocked_by` on the issue counts the open ones), any "blocked by" line in the body or comments, and a parent issue's task list. Then search open issues and PRs for undeclared ones, using the issue's key terms and the names of the files and types it touches. Read each candidate and classify it: **blocks** (must land first), **overlaps** (same area; coordinate or merge), **duplicate**, or **adjacent** (harmless; mention only if it changes the approach).

   Done when every candidate has a classification with a reason, and "none found" names the searches that found nothing.

7. **Decide the verdict**, one of:
   - **Ready**: implementable as written.
   - **Ready after update**: implementable once the description is corrected.
   - **Blocked**: name each blocker and who or what clears it.
   - **Not relevant**: done, superseded or obsolete; recommend closing and say why.

   Feasibility is a judgement on what the code and the rules allow, not only on whether a path exists: name the main design choice or risk the implementer will meet.

8. **Check the description.** Compare what the issue says with what steps 3-6 showed. List each drift: stale references, missing acceptance criteria that comments settled, scope that moved, new constraints, and any ADR the issue contradicts or ignores.
   Done when every `stale` or `wrong` claim, and every decision buried in the comments, is either fixed in a proposed rewrite or marked as intentionally kept.

## Report

Lead with the verdict and the one-sentence reason. Then, omitting any section that has nothing to say:

- **Blockers**: each with its link and classification, ADRs included (`ADR 0051: conflicts`). With none, say "no blockers" in the verdict line.
- **Decisions that shape the work**: each `constrains` ADR in one line: the decision and what it means for the implementer.
- **Claims that no longer hold**: a table of claim, verdict, evidence.
- **Relevance**: the step 5 conclusion with its evidence.
- **Proposed description**: only the changed parts, as before and after, so the user can approve the edit. With no drift, say "description is current".

Stop at the report; the user's answer decides what happens to the issue. End with the next step:

- Drift found (any `stale` or `wrong` claim, a decision buried in comments, a missing criterion) or open design choices in the report: suggest `/rewrite-issue-after-check`. It is user-invoked, so name it for the user to run; it carries these findings into the issue.
- Description current: ask only whether to comment or relabel the issue.
