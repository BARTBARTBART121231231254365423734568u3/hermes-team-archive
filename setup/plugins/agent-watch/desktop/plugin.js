/**
 * Agent Watch — read-only live Kanban status in the Hermes desktop app.
 *
 * SPIKE DECISION (2026-09-22, task t_75ea7a33): no `kanban.*` gateway RPC
 * methods exist (source scan of gateway/hermes_cli found only
 * sessions/profiles/cron/skills/config), so this pane reads the contracted
 * `GET /summary` backend below via `ctx.rest`. V1 is read-only: no
 * steer/stop/kill, no transcript tails. Plain ESM: jsx() calls, no build.
 */
import { Codicon, EmptyState, ErrorState, Skeleton, StatusDot, Tip, cn, host, queryClient, useQuery, useValue } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'agent-watch'
const POLL_MS = 5000
const STALE_HEARTBEAT_S = 300
const READY_CAP = 10
let api = null

function durationText(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0))
  if (total < 60) return `${total}s`
  const minutes = Math.floor(total / 60)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours}h ${rest}m` : `${hours}h`
}

function metaLine(row) {
  const parts = [row.assignee || 'unassigned']
  if (row.tenant) parts.push(row.tenant)
  if (row.branch) {
    const short = row.branch.length > 40 ? `…${row.branch.slice(-39)}` : row.branch
    parts.push(short)
  }
  return parts.join(' · ')
}

function openInKanban(taskId) {
  // The Kanban route is the canonical task-detail surface; the id stays
  // visible on every row so the matching drawer is immediately identifiable.
  host.navigate('/kanban')
}

function SectionHeader({ icon, title, count }) {
  return jsxs('div', {
    className: 'mb-2 flex items-center gap-1.5',
    children: [
      jsx(Codicon, { name: icon, size: '0.8rem' }),
      jsx('h3', { className: 'text-xs font-semibold uppercase tracking-wide text-(--ui-text-secondary)', children: title }),
      count == null ? null : jsx('span', {
        className: 'ml-auto rounded-full bg-(--ui-bg-secondary) px-1.5 py-0.5 text-[0.6875rem] tabular-nums text-(--ui-text-tertiary)',
        children: count
      })
    ]
  })
}

function RunningRow({ row }) {
  const stale = row.stale === true || (row.heartbeat_age_s || 0) > STALE_HEARTBEAT_S
  return jsxs('button', {
    type: 'button',
    onClick: () => openInKanban(row.task_id || row.id),
    title: `Open ${row.task_id || row.id} in Kanban`,
    className: cn(
      'group w-full rounded-md border border-(--ui-stroke-secondary) p-2.5 text-left',
      'transition-colors hover:bg-(--chrome-action-hover) focus-visible:outline-none',
      'focus-visible:ring-1 focus-visible:ring-(--ui-accent)'
    ),
    children: [
      jsxs('div', {
        className: 'flex items-start gap-2',
        children: [
          jsx('span', {
            className: 'mt-1 shrink-0',
            children: jsx(StatusDot, { tone: stale ? 'warn' : 'good' })
          }),
          jsxs('div', {
            className: 'min-w-0 flex-1',
            children: [
              jsxs('div', {
                className: 'flex items-center justify-between gap-2',
                children: [
                  jsx(Tip, {
                    label: row.title,
                    children: jsx('span', { className: 'truncate text-[0.8125rem] font-semibold text-foreground', children: row.title })
                  }),
                  jsx('span', {
                    className: cn(
                      'shrink-0 rounded px-1.5 py-0.5 text-[0.6875rem] tabular-nums',
                      stale ? 'bg-(--ui-accent) text-(--ui-on-accent)' : 'bg-(--ui-bg-secondary) text-(--ui-text-tertiary)'
                    ),
                    children: stale ? `stale · ${durationText(row.heartbeat_age_s)}` : durationText(row.elapsed_seconds)
                  })
                ]
              }),
              jsx('div', {
                className: 'mt-0.5 truncate text-[0.6875rem] text-(--ui-text-tertiary)',
                children: metaLine(row)
              }),
              jsxs('div', {
                className: 'mt-1 flex items-center justify-between gap-2 text-[0.6875rem] text-(--ui-text-tertiary)',
                children: [
                  jsx('span', { className: 'truncate', children: `${row.icon ? `${row.icon} ` : ''}${row.task_id || row.id}` }),
                  jsx('span', { className: 'shrink-0', children: row.heartbeat_text || `${durationText(row.heartbeat_age_s)} ago` })
                ]
              })
            ]
          })
        ]
      })
    ]
  })
}

function QueueRow({ row, extra }) {
  return jsxs('button', {
    type: 'button',
    onClick: () => openInKanban(row.task_id || row.id),
    title: `Open ${row.task_id || row.id} in Kanban`,
    className: cn(
      'w-full rounded-md px-2 py-1.5 text-left transition-colors',
      'hover:bg-(--chrome-action-hover) focus-visible:outline-none',
      'focus-visible:ring-1 focus-visible:ring-(--ui-accent)'
    ),
    children: [
      jsx(Tip, {
        label: row.title,
        children: jsx('div', { className: 'truncate text-xs text-foreground', children: row.title })
      }),
      jsxs('div', {
        className: 'mt-0.5 flex items-center justify-between gap-2 text-[0.6875rem] text-(--ui-text-tertiary)',
        children: [
          jsx('span', { className: 'truncate', children: extra }),
          jsx('span', { className: 'shrink-0 tabular-nums', children: row.task_id || row.id })
        ]
      })
    ]
  })
}

function RunningSection({ rows }) {
  if (!rows || rows.length === 0) {
    return jsx(EmptyState, {
      title: 'No agents working right now',
      description: 'Active Kanban workers will appear here automatically.'
    })
  }
  return jsx('div', {
    className: 'space-y-2',
    children: rows.map(row => jsx(RunningRow, { row }, row.task_id || row.id))
  })
}

function ReadySection({ collection }) {
  const items = (collection && collection.items) || []
  const total = (collection && collection.total) || 0
  if (total === 0) {
    return jsx(EmptyState, {
      title: 'Ready queue is empty',
      description: 'Tasks waiting to be picked up will appear here.'
    })
  }
  const shown = items.slice(0, READY_CAP)
  const more = Math.max(0, total - shown.length)
  return jsxs('div', {
    className: 'space-y-1',
    children: [
      jsx('div', {
        className: 'space-y-0.5',
        children: shown.map(row => jsx(QueueRow, {
          row,
          extra: `${row.assignee || 'unassigned'}${row.tenant ? ` · ${row.tenant}` : ''}`
        }, row.task_id || row.id))
      }),
      more > 0 ? jsx('div', {
        className: 'px-2 pt-1 text-[0.6875rem] text-(--ui-text-quaternary)',
        children: `+${more} more`
      }) : null
    ]
  })
}

function NeedsInputSection({ collection }) {
  const items = (collection && collection.items) || []
  const total = (collection && collection.total) || 0
  if (total === 0) {
    return jsx(EmptyState, {
      title: 'Nothing needs input',
      description: 'Blocked tasks waiting on a human will appear here.'
    })
  }
  return jsxs('div', {
    className: 'space-y-1',
    children: [
      jsx('div', {
        className: 'space-y-0.5',
        children: items.map(row => jsx(QueueRow, {
          row,
          extra: `${row.block_kind || 'needs_input'} · ${durationText(row.age_s)} ago`
        }, row.task_id || row.id))
      }),
      total > items.length ? jsx('div', {
        className: 'px-2 pt-1 text-[0.6875rem] text-(--ui-text-quaternary)',
        children: `+${total - items.length} more`
      }) : null
    ]
  })
}

function LoadingSections() {
  return jsx('div', {
    className: 'space-y-4',
    children: [0, 1, 2].map(index => jsxs('div', {
      children: [
        jsx(Skeleton, { className: 'mb-2 h-4 w-28 rounded' }),
        jsx(Skeleton, { className: 'h-20 w-full rounded-md' })
      ]
    }, index))
  })
}

function AgentWatchPane() {
  const query = useQuery({
    queryKey: [ID, 'summary'],
    queryFn: () => api('/summary'),
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: true
  })
  const running = query.data?.running ?? []
  const ready = query.data?.ready ?? { total: 0, items: [] }
  const needsInput = query.data?.needs_input ?? { total: 0, items: [] }

  return jsxs('section', {
    className: 'flex h-full min-h-0 flex-col p-3 text-sm',
    'aria-label': 'Agent Watch',
    children: [
      jsxs('header', {
        className: 'mb-3 flex items-center gap-2 border-b border-(--ui-stroke-secondary) pb-2.5',
        children: [
          jsx(Codicon, { name: 'broadcast', size: '0.9rem' }),
          jsx('h2', { className: 'font-semibold text-foreground', children: 'Agent Watch' }),
          query.data ? jsx('span', {
            className: 'ml-auto rounded-full bg-(--ui-bg-secondary) px-1.5 py-0.5 text-[0.6875rem] tabular-nums text-(--ui-text-tertiary)',
            children: `${running.length} running`
          }) : null
        ]
      }),
      jsx('div', {
        className: 'min-h-0 flex-1 space-y-5 overflow-y-auto pb-1',
        children: query.isLoading
          ? jsx(LoadingSections, {})
          : query.isError
            ? jsx(ErrorState, {
              title: 'Agent status unavailable',
              description: query.error?.message ?? 'The Agent Watch backend could not be reached.',
              children: jsx('button', {
                type: 'button',
                className: 'mx-auto rounded-md border border-border px-3 py-1.5 text-xs hover:bg-(--chrome-action-hover)',
                onClick: () => query.refetch(),
                children: 'Retry'
              })
            })
            : [
              jsx('section', {
                'aria-label': `Running (${running.length})`,
                children: [
                  jsx(SectionHeader, { icon: 'pulse', title: `Running (${running.length})` }),
                  jsx(RunningSection, { rows: running })
                ]
              }, 'running'),
              jsx('section', {
                'aria-label': `Ready queue (${ready.total || 0})`,
                children: [
                  jsx(SectionHeader, { icon: 'clock', title: `Ready queue (${ready.total || 0})` }),
                  jsx(ReadySection, { collection: ready })
                ]
              }, 'ready'),
              jsx('section', {
                'aria-label': `Needs input (${needsInput.total || 0})`,
                children: [
                  jsx(SectionHeader, { icon: 'comment', title: `Needs input (${needsInput.total || 0})` }),
                  jsx(NeedsInputSection, { collection: needsInput })
                ]
              }, 'needs-input')
            ]
      }),
      jsx('footer', {
        className: 'mt-3 border-t border-(--ui-stroke-secondary) pt-2 text-[0.6875rem] text-(--ui-text-quaternary)',
        children: 'Updates automatically from the active Kanban board.'
      })
    ]
  })
}

function AgentWatchChip() {
  const gateway = useValue(host.state.gateway)
  const query = useQuery({
    queryKey: [ID, 'summary'],
    queryFn: () => api('/summary'),
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: true,
    retry: 1
  })
  const offline = gateway !== 'open'
  const count = query.data?.running?.length
  const label = query.isLoading ? 'agents …' : `${count ?? 0} running`

  return jsx(Tip, {
    label: offline ? 'Agent Watch — gateway offline' : `Agent Watch — ${count ?? 0} agent${count === 1 ? '' : 's'} running`,
    children: jsx('button', {
      className: cn(
        'inline-flex h-full items-center gap-1.5 px-1.5 text-[0.6875rem] tabular-nums transition-colors',
        offline ? 'text-(--ui-text-quaternary)' : 'text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground'
      ),
      type: 'button',
      onClick: () => host.navigate('/kanban'),
      'aria-live': 'polite',
      children: [
        jsx(StatusDot, { tone: offline ? 'muted' : count > 0 ? 'good' : 'muted' }),
        label
      ]
    })
  })
}

export default {
  id: ID,
  name: 'Agent Watch',
  description: 'See which Kanban agents are working and what they are doing.',
  defaultEnabled: false,
  register(ctx) {
    api = ctx.rest
    let lastInvalidate = 0
    let disposeEvents = null
    // Event-driven refresh where the gateway stream exists, throttled to
    // >=5s so bursts never outrun the poll cadence; polling above stays the
    // mandatory fallback (ctx.socket is a no-op on OAuth remotes).
    try {
      if (host && typeof host.onEvent === 'function') {
        disposeEvents = host.onEvent('*', () => {
          const now = Date.now()
          if (now - lastInvalidate < POLL_MS) return
          lastInvalidate = now
          queryClient.invalidateQueries({ queryKey: [ID, 'summary'] })
        })
      }
    } catch (err) {
      disposeEvents = null
    }
    ctx.onDispose(() => {
      if (typeof disposeEvents === 'function') disposeEvents()
    })
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'Agent Watch',
      data: { placement: 'right', width: '320px' },
      render: () => jsx(AgentWatchPane, {})
    })
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 130,
      render: () => jsx(AgentWatchChip, {})
    })
  }
}
