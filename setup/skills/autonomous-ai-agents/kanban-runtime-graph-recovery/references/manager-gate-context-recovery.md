# Manager-gate context recovery

Use when a manager-only gate refuses a dispatched worker that inherited a delegated-child context.

## Rule

- When a dispatched worker is refused by a manager-only gate because it inherited a delegated-child context, do not unblock and retry the same run: the inherited context persists across retries, so the refusal is deterministic, not transient. Execute the narrowly scoped authorized action directly from the coordinator's own default-manager session, record the outcome on the card, and complete or release it.

## Why

- Inherited delegation context survives unblock/retry cycles; only a clean manager session passes the gate, so repeated retries burn budget without changing the verdict.
