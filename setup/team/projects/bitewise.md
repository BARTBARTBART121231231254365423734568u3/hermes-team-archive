# BiteWise

Registered repository path: ~/Hermes Workspace/projects/BiteWise

Verify git origin and the current branch before work. Record architecture
and decisions only after inspecting this project. Deployment target must
come from a verified manifest; never infer it from the container environment.

Verified deployment targets:
- Staging: ~/.hermes/team/deployments/bitewise-staging.json
- Production: ~/.hermes/team/deployments/bitewise-production.json

Production inspection (2026-09-08): guarded deployment attempt for requested
main commit b92b04192a2f2897e618c5e87c6dd321e1b75cbc created Railway deployment
be5e9269-e439-4a35-a565-00544ecfa07f, but Railway deployed configured source
branch bitewise/staging at old commit 87dc215858f6f035f762f5b2aafb1cf582ef00d5.
That deployment is SUCCESS; previous deployment
bbfe16d9-cad1-45a9-afcf-2ef2f3d072ee is REMOVED. Production still returns 403
for nl.openfoodfacts.org through /api/proxy. The reviewed manifest targets main,
so do not claim promotion until an external operator changes the Railway service
source branch to main and the resulting exact revision and behavior are verified.

Follow-up after the operator reported switching the dashboard source to main:
two more guarded redeploys still produced Railway metadata branch
`bitewise/staging`, commit `87dc215858f6f035f762f5b2aafb1cf582ef00d5`.
Latest deployment `67073aea-8e9f-49d4-90b2-485da97e5d07` is SUCCESS; prior
deployment `39c455f8-afac-402c-9dac-97a95343fc5b` is REMOVED. Production health
is HTTP 200, but the Dutch barcode proxy remains HTTP 403. The Railway source
setting change is therefore not effective for this production environment/service.

Guarded production deployment attempt (2026-09-08 08:26 UTC) again verified
manifest branch `main` and requested exact commit
`b92b04192a2f2897e618c5e87c6dd321e1b75cbc`, but Railway deployment
`55056477-e5ba-41eb-a29d-ff4436302d1b` resolved to configured source branch
`bitewise/staging` at `87dc215858f6f035f762f5b2aafb1cf582ef00d5`. It reached
SUCCESS and replaced prior deployment `67073aea-8e9f-49d4-90b2-485da97e5d07`.
Live `/api/auth/status` is HTTP 200; a proxied request to
`nl.openfoodfacts.org` is still HTTP 403. An external Railway operator must fix
the production service source branch; repeated guarded deploys cannot publish
the requested main revision while Railway resolves this stale source config.

Production resolution (2026-09-08 08:55 UTC): reviewed commit
`aeba5c6d5f25e71978cde06d62b9b2a5c8173642` was pushed to `main`. Railway's
GitHub release path created deployment `76448ea3-25c5-4712-95cc-87b0919b617a`
for that exact repository, branch, and commit; it reached SUCCESS/RUNNING and
replaced deployment `28fa5bda-ae41-4797-b398-88b557d828c2` at `b92b041`.
Production `/api/auth/status` returns HTTP 200. The exact web/PWA proxy path
used by barcode lookup returns HTTP 200 with Open Food Facts `status: 1` for
verified products from Albert Heijn, Jumbo, Lidl NL, PLUS, and Aldi NL. The
Node 22 pinned-DNS callback failure is therefore fixed end-to-end; no data
source replacement is required for this incident. Broader coverage remains a
separate measured-provider benchmark rather than a release blocker.
