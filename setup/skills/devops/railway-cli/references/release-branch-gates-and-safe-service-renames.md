# Release branch gates and safe service renames

## Problem pattern

A release candidate can be fully built, tested, and pushed while production remains unchanged because Railway's GitHub integration watches a different branch (commonly `main`). Treat this as a release-promotion gate, not a Railway build failure.

## Safe promotion checklist

1. Record the exact RC branch and SHA.
2. Fetch origin and inspect the deployment branch relationship.
3. Promote with a normal fast-forward when possible; otherwise create a conventional merge after resolving only understood conflicts.
4. Never force-push or overwrite remote deployment-branch commits.
5. Verify the final remote deployment-branch SHA using `git ls-remote` and confirm it contains the RC commit.
6. Then observe the GitHub-triggered Railway deployment; do not substitute `railway up` for a GitHub-connected service.

## Safe Railway service rename checklist

When a user confirms an oddly named service is the correct production target and asks to rename it:

1. Target the confirmed project/service with the Railway targeting helper and inspect status first.
2. Use Railway's supported service update/rename operation, changing only the name.
3. Do not recreate/delete the service or modify secrets, domains, source, volumes, or traffic settings.
4. Verify the same service ID remains, the source connection and persistent volume are unchanged, and the existing production URL returns successfully.
5. Resume deployment only after that verification.

## Handoff facts worth recording

- Project ID and environment
- Service ID (stable identity) and final display name
- Source repository and deployment branch
- RC and resulting deployment-branch SHA
- Volume/domain preservation evidence
- Actual live deployment/log and HTTP verification results
