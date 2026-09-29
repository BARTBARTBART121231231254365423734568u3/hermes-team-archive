# Status Honesty and Completion Reporting

Report only what you verified on the live board, and notify Thomas once when the outcome is live — never in between.

## Procedure

1. Read live state before any status reply: `kanban_show` on the owned card plus `kanban_list` for the lane. Quote status and last worker evidence, not what you changed about the card.
2. When asked how long remains, give a rough planning range labeled with its assumptions, or state that no reliable estimate exists.
3. Deliver one consolidated completion notice in the originating conversation after the outcome is live and verified.

## Rules

- Queue repair is not resumed execution: restoring a priority, unblocking a card, or fixing a test environment means the work still waits for a worker slot — say that explicitly instead of implying work restarted.
- Never promise a completion time that depends on worker pickup, queue depth, or review outcomes; a single number is read as a promise.
- Send no interim progress pings on any channel, and never ask the user to relay board notifications you can read yourself — read the card directly.

## Pitfalls

- Treat an unblocked or `ready` card as waiting for pickup, not in progress — the dispatcher may take an unknown time to spawn a worker, and claiming otherwise manufactures a missed deadline.
- State time figures as ranges with assumptions (slots free, review passes first try) — precise ETAs without control over the queue erode trust when they slip.
