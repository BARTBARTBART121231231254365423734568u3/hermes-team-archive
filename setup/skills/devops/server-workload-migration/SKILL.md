---
name: server-workload-migration
description: "Use when migrating workloads between servers safely."
version: 1.0.0
metadata:
  hermes:
    category: devops
    tags: [migration, ssh, backup, rollback, linux]
---

# Server Workload Migration

Move a working environment to another machine without losing task state, repository history, credentials, or rollback capability.

## Procedure

1. **Define the cutover contract.** Record the source host, destination host, destination OS, transport, which host becomes primary, rollback window, and the exact workloads and state stores in scope. Preserve completed milestones and in-flight work as explicit acceptance criteria.
2. **Verify SSH identity before copying anything.** Confirm the destination host-key fingerprint out of band, add it to `known_hosts`, and identify the exact case-sensitive remote account with `whoami`. Select a specific private key with `ssh -i <private-key> -o IdentitiesOnly=yes <user>@<host>` instead of relying on whichever key the agent offers by default.
3. **Match the public key to the private key.** Run `ssh-keygen -lf <public-key>` locally, then use `ssh -vv -i <private-key> -o IdentitiesOnly=yes <user>@<host> true` only when needed to verify the fingerprint actually offered. If the server rejects the offered fingerprint, stop retrying and correct the remote account, `authorized_keys`, ownership, or modes.
4. **Bootstrap remote authorization safely.** Install only the public key in the intended account's `$HOME/.ssh/authorized_keys`; use mode `700` for `.ssh`, `600` for `authorized_keys`, and ensure both are owned by that account. Never request or paste passwords or private keys into chat, task cards, logs, or memory.
5. **Inventory both hosts.** Check architecture, OS, free space, required runtimes, services, repositories, worktrees, uncommitted changes, databases, schedulers, secrets backends, ports, and process managers. Separate portable state from host-specific caches, temporary files, lock files, and Windows-only paths.
6. **Freeze and back up mutable state.** Pause writers where consistency requires it. Create a dated archive or snapshot, generate checksums, and verify the archive can be listed or restored before transfer. Keep the source host unchanged through the rollback window.
7. **Stage instead of overwriting.** Transfer into a new destination directory, verify checksums, then adapt paths, ownership, permissions, service definitions, and line endings. Move secrets through the existing secrets manager or a direct secure channel, never inside source archives intended for broad retention.
8. **Install and validate.** Install pinned runtime versions, restore state, build projects, run tests, start services, and exercise real health checks. Verify board/task history, profiles, schedules, repository branches, and application data—not merely that files exist.
9. **Prepare orchestration state for a cross-OS cutover.** Before switching the coordinator or dispatcher, finish or block source-host workers and inspect every runnable task for host-specific absolute workspace paths. Pre-create the post-cutover verification task with a destination-native workspace, or create it after the destination gateway is authoritative. Never parent the replacement to a malformed source-workspace card, because that dependency strands the recovery lane.
10. **Cut over once.** Stop source writers, perform a final incremental sync, start the destination, and switch traffic or operator entry points. Avoid parallel primaries when both can mutate the same state. Confirm the conversation or control plane is actually executing on the destination hostname before treating the switch as successful.
11. **Verify from destination-native execution.** Check database integrity, task/milestone continuity, active project registries, repository WIP preservation, model/provider smoke tests, and service enablement from the destination itself. Treat a post-cutover worker failure caused solely by an old source workspace path as an orchestration repair: preserve completed migration evidence and route only the remaining verification through a fresh destination-native task.
12. **Prove rollback.** Document the exact command or switch that returns service to the source host. Keep the source intact until the destination has passed the agreed soak period, then retire it explicitly.

## SSH Pitfalls

- Confirm the exact Linux username before changing keys; usernames and home paths are case-sensitive, and a correct key under the wrong account is indistinguishable from a bad key at login.
- Pair the public key with its matching private-key filename before testing; a machine may hold several valid keys, and OpenSSH defaults may offer a different one.
- Treat `Permission denied (publickey)` after the expected fingerprint is visibly offered as a destination authorization problem; repeated client retries do not change the server's account, ownership, modes, or `authorized_keys` contents.
- Preserve the verified server host key while debugging user authentication; host identity and user authorization are separate gates.

## Completion Evidence

Report the destination hostname, verified services, test/build commands and real results, restored state categories, checksum or snapshot evidence, cutover status, and rollback status. Do not call the migration complete while SSH access, state restoration, runtime verification, or rollback remains unproved.
