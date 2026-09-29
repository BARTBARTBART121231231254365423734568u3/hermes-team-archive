# Existing-work discovery

Use this before creating a new task or answering whether work is already open.

1. Resolve the object being requested: a registered repository/project is not the same as a Kanban task. If the user corrects “project” to “task,” stop project discovery and query the board.
2. Search only nonterminal tasks unless the user asks for history. Match the requested capability against task title, body, and comments; title-only matching misses implementation hidden under broader card names.
3. Return concrete evidence: matching task ID, title, status, and assignee. For no match, include the count of open tasks searched so the negative result is auditable.
4. Create new work only after this search, preventing duplicate lanes and conflicting ownership.

Do not make the user inspect the board or reconcile similar cards themselves.