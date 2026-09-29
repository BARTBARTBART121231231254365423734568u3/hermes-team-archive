# Provider Quota Exhaustion: Diagnosis and Honest Reporting

How to tell a provider-quota wall apart from a flaky dispatcher, and what to
tell the user when the model they asked for cannot run.

## Symptom that is routinely misread

A dispatched worker dies shortly after spawn. The board reports only:

```
✖ @<profile> Kanban t_xxxx worker crashed (pid gone); dispatcher will retry
✖ @<profile> Kanban t_xxxx gave up after repeated spawn failures
```

The task-specific log is empty, so this looks like infrastructure flakiness.
It usually is not. The worker process **did** start; it failed on its first
API call, exhausted its internal retry budget, and exited. The dispatcher only
sees a dead PID and reports process death, which hides the real cause.

A crash landing consistently ~30-90s after spawn, across multiple retries,
with an empty task log, is the fingerprint of a provider rejection rather
than a bad brief.

## Diagnosis

Read the **central** error log, not the per-task log — the provider error is
logged by the agent runtime, not the dispatcher:

```bash
grep -nE "RateLimitError|usage_limit_reached|429|API call failed after" \
  "$LOCALAPPDATA/hermes/logs/errors.log" | tail -40
```

A conclusive hit looks like `HTTP 429: The usage limit has been reached`,
with a `resets_at` epoch and `plan_type` in the payload. Convert `resets_at`
to a date before reporting it — "resets in N days" is actionable, a raw epoch
is not.

Corroborating signals in the same log window:

- The **same** 429 appearing for both the primary and the fallback model. If
  both belong to one provider, this is provider-level exhaustion; the
  fallback chain provides no protection.
- The context summarizer failing with the same error. Anything sharing that
  provider degrades simultaneously.

## Verify the account before trusting a claim about it

When a user says "use the other account, it still has credits," verify which
account is actually authenticated instead of switching blind. Decode the
identity token's claims payload (base64url middle segment of the JWT) and read
the email and plan claims. Print **only** identity and plan fields; never echo
token material.

This routinely shows the "other" account is already the one in use, which
turns a proposed fix into a dead end before any time is spent on it.

## Credit pools are not fungible

A subscription's agent/CLI quota and that vendor's pay-as-you-go API credits
are **separate pools with separate billing**. Credits visible in a platform
billing dashboard do not refill an exhausted subscription-tier quota, and a
subscription-authenticated provider entry will keep returning 429 regardless
of that balance.

Before proposing "use the credits," establish three things:

1. Which pool the credits actually live in.
2. Whether a provider entry exists that draws on that pool (an API-key
   provider is a different entry from a subscription-OAuth provider).
3. Whether the requested model is even offered on that pool — newest models
   often appear in the subscription product before the public API.

If any of the three is unconfirmed, say so rather than implying the switch
will work.

## Reporting

A quota wall is a hard external constraint, not something to retry around.
Report it as a decision, not a status update:

- Name the exact error, the affected provider, and the reset date.
- State plainly that the requested model cannot run until then.
- Offer concrete options: run on an available provider now, wait for reset, or
  upgrade/attach a different credential path.
- Park the card rather than deleting it — a fully specced card costs nothing
  to hold and runs immediately once a path is chosen.

When the user pinned that model deliberately ("use X, not Y"), flag the
conflict explicitly instead of silently falling back to the model they
excluded. The choice of which constraint to break is theirs.
