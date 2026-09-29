---
name: product-feature-inventory
description: "Use when cataloguing app features for product decisions."
---

# Product feature inventory

Use when cataloguing either implemented app capabilities or a proposed feature list so the owner can decide scope. This is **not** a bug audit, implementation authorization, or a roadmap. Label which kind of inventory it is; proposed features are not claims about working code.

## Procedure

**For a supplied proposal rather than an existing app:** read the original attachment as the source of truth; preserve its item IDs, order, intentional numbering gaps, exclusions, and unresolved choices. Group into selectable Markdown checkboxes without silently inventing missing numbers or mixing requirements from an older project with the same name. Compare the output's ID sequence and item text to the source programmatically before delivery; put visual navigation and implementation phases in separate artifacts unless explicitly requested. Deliver the requested downloadable `.md` itself with a simple attachment path (copy and byte-compare if needed), not an HTML preview or a prose path. Do not perform a repository audit for a purely prospective inventory. For an implemented-app inventory, follow the revision and code-tracing steps below.

1. **Fix the inspected revision.** Locate the actual repository, check branch, working-tree changes, remote and commit. If the local branch trails its remote, inspect the changed paths or update read-only references; state which revision underlies the inventory. Do not blend unmerged feature branches, untracked prototypes, documentation roadmaps and released code into one list.
2. **Build a coverage map before drafting.** Read the app router/navigation, route components, shared state, server endpoints, integration/scheduler modules, settings, export/backup modules, and platform manifests. Use documentation as a discovery aid, then confirm every substantive feature against its active implementation. Search both frontend and backend for a claimed provider or data flow; an OAuth connection without data import is not a sync feature.
3. **Label implementation maturity.** Distinguish available code paths from a verified live deployment, experiments, provider-dependent setup, local-only features, platform-specific code, and roadmap items. Check actual executable paths when describing native releases, health integrations, notifications, exports, and AI. Do not infer that a menu option, package dependency, or README claim means the end-to-end feature works.
4. **Present a decision-friendly inventory.** Group features by user journey (daily core loop, library, goals, insights, integrations, accounts, settings/data/platform), use stable numbered checkboxes, and write one independently selectable capability per item. Include secondary options without exploding every toggle into a separate item. Explain material caveats immediately beside affected groups, particularly ambiguous measurements or partial integrations.
5. **Carry decisions forward without renumbering.** When the owner drops or modifies numbered items, retain the original item numbers, omit dropped entries, and rewrite changed entries in the full updated list. Distinguish a firm exclusion from an open research/design choice. Answer a question about an obscure item with a concrete example and a recommendation; once accepted, apply it to the inventory rather than asking again.
6. **Research comparators only when requested.** Compare competing apps on actual user workflows and the owner's retained scope, using current first-party product/help pages for specific claims. Separate extra features from better execution of an existing feature; flag subscriptions, geography, unavailable APIs/licenses and unverified marketing claims. For food databases, assess local product/barcode coverage, data quality, portions, rights and maintenance before calling a source 'best.' Recommend a shortlist of concrete changes tied back to inventory item numbers, plus explicit non-recommendations; never silently reintroduce excluded features.
7. **Ground and close.** Cite the inspected source paths/revision (and direct comparator links when applicable), state that a code inventory is not live QA when no runtime check occurred, and invite the owner to mark item numbers keep/rethink/drop. Do not start design or implementation merely because the owner is exploring options.

## Pitfalls

- Trace a feature through its producer, persistence and consumer before naming it complete; a settings toggle alone can overstate capability.
- Verify food-unit conversions and source-specific serving data before calling portion choices validated; a generic unit dropdown can rescale numbers without a trustworthy physical conversion.
- Keep a core app feature distinct from a conditional integration; external credentials, supported devices, or native environments change availability.
- Prefer concise, neutral descriptions to marketing claims; the owner needs a reliable menu to select from, not an implicit recommendation to carry everything forward.
