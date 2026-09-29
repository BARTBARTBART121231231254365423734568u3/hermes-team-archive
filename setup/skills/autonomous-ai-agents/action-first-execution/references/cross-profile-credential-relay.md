# Cross-profile credential relay

Use this when a specialist has completed and tested its scoped work but is blocked solely because its worker profile cannot access a credential that the coordinator profile already has.

## Boundary rule

Keep specialist ownership intact. The coordinator performs only the narrow authenticated boundary action, then returns the task to the specialist for the remaining merge, deploy, and live verification work.

Do **not** use this pattern when the worker still needs diagnosis, implementation, or testing. Do not copy plaintext tokens into task comments, logs, prompts, or another profile.

## GitHub push pattern

1. Read the task handoff and confirm it names a concrete branch, commit, and passing test result.
2. In the shared workspace, confirm the checked-out branch and local commit. Ensure the worktree is clean enough that the push cannot include unrelated changes.
3. In the coordinator profile, remove ambient token overrides that can shadow the persisted login:
   ```bash
   unset GH_TOKEN GITHUB_TOKEN
   gh auth status
   ```
4. If authenticated, wire Git to the persisted `gh` credential store:
   ```bash
   gh auth setup-git --hostname github.com
   ```
5. Push only the named branch:
   ```bash
   git push --set-upstream origin <branch>
   ```
6. Verify exact remote identity rather than trusting the push message:
   ```bash
   local_sha=$(git rev-parse HEAD)
   remote_sha=$(git ls-remote origin refs/heads/<branch> | cut -f1)
   test "$local_sha" = "$remote_sha"
   ```
7. Add a durable task comment containing the branch and verified commit SHA, but no secrets.
8. Unblock the existing specialist task. Explicitly instruct it to continue with PR/merge/deploy/live verification and to end with the required lifecycle call.
9. Report only the narrow verified fact to the user: the branch was pushed and the specialist resumed. Do not say the feature is live until deployment and behavioral verification finish.

## Why this matters

Authentication is profile-scoped, while a task workspace may be shared. A worker’s failed push does not prove GitHub access is unavailable globally. Checking the coordinator’s persisted login and relaying only the authenticated boundary action avoids asking the user for credentials, avoids duplicating the specialist’s investigation, and preserves an auditable handoff.