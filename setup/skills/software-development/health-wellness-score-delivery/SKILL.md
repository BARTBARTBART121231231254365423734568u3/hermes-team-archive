---
name: health-wellness-score-delivery
description: Use when delivering health-data wellness scores.
---

# Health-data ingestion and wellness score delivery

## Procedure

1. **Establish the evidence chain before changing score UI.** Verify, in order: the provider sends the metric, the ingestion endpoint accepts its real alias and unit, the normalized value persists under the correct owner and local calendar day, the wellness query returns enough history, and the scorer consumes that history. Treat a visible provider-side “unsupported metric” notice as a lead to map or intentionally skip that metric—not proof that a score is wrong.

2. **Prove the exact exporter contract before codifying aliases.** Back every asserted provider metric name, unit, and nested field with either a sanitized real export from the exact exporter/version or an immutable authoritative artifact that explicitly contains those values. Record provenance beside the fixture and distinguish generic envelope evidence from metric-specific evidence; a schema proving only `{qty,date,source}` does not prove an HRV label, exercise label, or unit. Exhaust public and repository evidence before asking the user for a sample; if a sample is necessary, request the smallest export possible and require removal of credentials, identities, device metadata, and real health values.

3. **Make acceptance changes allowlist-based.** Keep a bounded canonical metric registry with provider aliases, compatible units, normalization rules, and validation. Persist only metrics required by product features; skip unknown groups without retaining raw health values, metric names, device identifiers, request bodies, or diagnostic payloads. Reject invalid values or dimensionally incompatible units for known metrics atomically rather than coercing them.

4. **Define score contracts before implementation.** For every score, document required inputs, optional contributors, source precedence, missing-data behavior, local-day aggregation, and the exact history window. If mirroring a commercial wellness product, use only its publicly documented contributor categories and call the result an informed estimate; never claim a proprietary formula or invented exact weights.

5. **Fetch at least the complete baseline window plus the score day.** Align the page/API history query with the score helper’s declared baseline. A helper supporting a rolling 30-day baseline is not a 30-day model unless the caller retrieves 30 valid prior days. Add a regression test that proves the fetch limit and scorer window agree.

6. **Use personal baselines correctly.** Compare current/overnight physiological readings with a rolling personal baseline, while treating historical data as calibration rather than as today’s raw measurement. Show a provisional or “building baseline” state when the minimum valid-history threshold is met but the target baseline is incomplete; withhold the score, using `—` and a concrete reason, when required inputs are absent.

7. **Keep measurement semantics distinct from display concepts.** Preserve the exact physiological statistic supplied by the provider: SDNN is not RMSSD, and neither may be relabeled or used to extend the other's baseline. Store and score each statistic under its own canonical field and historical series. At the presentation layer, an “HRV” card may select whichever supported statistic is available, but it must label the chosen statistic and completeness logic must treat supported alternatives as `SDNN OR RMSSD`, not require both. Test ingestion, scoring, completeness, and the visible card together so a correct backend field cannot ship as a blank UI.

8. **Keep provider ownership and provider-specific interpretation intact.** Preserve existing source-preferred scores and non-target provider behavior. Add new provider aliases or normalizers behind the ingestion boundary; do not make dashboard or scoring changes that alter Google/Fitbit/Garmin/Withings/Strava behavior without an explicit product decision.

9. **Separate selected-day truth from latest-known presentation.** A dashboard that selects one calendar day can legitimately have gaps even when recent historical rows exist. Keep the selected-day value and score inputs null when that day is missing; for informational cards only, expose a separate `latestReading { value, date, provenance }` within the bounded history window and label its measurement date/freshness explicitly. Preserve a real zero as a valid current value, keep trends on their original dated series, and never feed display fallback values into Sleep, Recovery, or Activity scores. When choosing between alternative HRV statistics for the visible card, select deterministically by recency and label the statistic; do not merge SDNN and RMSSD histories.

10. **Unify nutrition and wearable data through one dated daily-context contract.** Build a server-owned, user-scoped aggregate for local day, timezone, nutrition targets/logged intake/meal timing/hydration, sleep, HRV statistic, resting heart rate, steps, active energy, workouts, and recovery/activity estimates. Preserve source, measurement date, freshness, and completeness per value; define provider precedence and prevent double counting. Use the context to connect Wellness, Goals, Statistics, and Diary through one relevant action rather than presenting two adjacent dashboards.

11. **Stage cross-domain guidance from deterministic rules to evidence-backed relationships.** Start with transparent, testable rules that summarize observed inputs and suggest one bounded action without silently changing calorie or macro targets. Add statistical nutrition↔recovery relationship detection only after sufficient paired observations, timezone/day-boundary controls, missingness checks, effect-size and confidence thresholds, and user opt-in exist. Let an LLM verbalize an approved structured result, but never invent its direction, magnitude, confidence, causality, or recommendation; use associative language and keep medical diagnosis out of scope.

12. **Verify in layers before release.** Run unit tests for aliases/units/invalid values, owner-isolation and atomicity tests, score-contract fixtures for missing/partial/full baseline states, focused UI tests, lint, and production build. For daily context, test provider precedence, duplicate-provider suppression, timezone boundaries, missing-versus-zero, historical freshness, and that display fallback cannot affect current-day recommendations. For latest-known display behavior, test historical fallback, explicit date/provenance, current-day replacement, a real current zero, responsive rendering, refresh, and unchanged score withholding in Chromium and WebKit. Require independent review to verify both ingestion and query-to-scorer continuity; a UI-only score patch is incomplete if required source metrics are not proven to persist. In privacy tests, assert structured redaction or exact forbidden values rather than short sentinel substrings that can occur randomly in generated IDs.

## Pitfalls

- **Trace real exporter aliases before adding mappings — provider labels often differ from canonical app fields, so a generic mapping can leave the score permanently input-starved.**
- **Never collapse related physiological statistics into one field — SDNN and RMSSD are different measurements, and mixing them corrupts personal baselines even when both are shown generically as HRV.**
- **Test the visible card after adding a canonical field — ingestion and scoring can pass while the UI still reads only the previous field and renders `—`.**
- **Do not fill a selected-day gap with an undated historical value — it misrepresents freshness; use a separate dated latest-reading presentation field and keep score inputs unchanged.**
- **Do not label a synthetic fixture “evidence-backed” from a generic schema — provenance must explicitly establish each exact metric name, unit, and special field used by the parser.**
- **Do not convert missing readings to zero — zero is a physiological claim and distorts recovery, sleep, and activity results.**
- **Do not deploy a baseline score solely because the helper accepts a long window — the API/page may silently supply a shorter history.**
- **Keep automated exports on the current day after a one-time history import — historical data establishes calibration, while daily scoring needs current readings.**
- **Do not log raw health payloads while debugging unsupported metrics — metric values and device metadata are sensitive, and aggregate acceptance/skipped counts are enough for operational diagnosis.**
- **Probe the live table shape when scorer queries fail on a missing column — migration files on disk do not prove what ran, so query `information_schema` on the real database before rewriting the query.**
- **Keep every migration replay-safe when the project's migrator re-executes all files without a tracking table — use `IF NOT EXISTS` and condition destructive reshapes on the old shape actually existing, otherwise each boot or test run breaks.**
- **Order migration files so prerequisites sort first — an untracked migrator replays files alphabetically and aborts on the first failure, so a reshape/guard file must sort before the file whose statements assume the new shape; otherwise a fresh database migrates halfway and every later file never runs.**
