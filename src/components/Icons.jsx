export function ArrowRight({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h13M14 7l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="square" strokeLinejoin="miter" />
    </svg>
  )
}

export function FileIcon({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 32" fill="none" aria-hidden="true">
      <path d="M3 1h14l8 8v22H3z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M17 1v8h8M8 16h12M8 21h12M8 26h8" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

export function PlusIcon({ open = false }) {
  return (
    <svg className={open ? 'icon-plus is-open' : 'icon-plus'} width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 4v16M4 12h16" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

export function MenuIcon({ open = false }) {
  return (
    <svg width="25" height="25" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {open ? (
        <path d="M5 5l14 14M19 5L5 19" stroke="currentColor" strokeWidth="1.8" />
      ) : (
        <path d="M3 7h18M3 12h18M3 17h18" stroke="currentColor" strokeWidth="1.8" />
      )}
    </svg>
  )
}
