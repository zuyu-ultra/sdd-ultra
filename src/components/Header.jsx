import { useState } from 'react'
import { ArrowRight, MenuIcon } from './Icons.jsx'

const links = [
  ['什么是 SDD', '#what'],
  ['工作流', '#workflow'],
  ['关键产物', '#artifacts'],
  ['常见问题', '#faq'],
]

export default function Header() {
  const [open, setOpen] = useState(false)

  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="返回顶部">
        <strong>SDD</strong><span>/</span><span>规格驱动开发</span>
      </a>
      <button className="menu-button" onClick={() => setOpen(!open)} aria-expanded={open} aria-label="切换导航">
        <MenuIcon open={open} />
      </button>
      <nav className={open ? 'nav-links is-open' : 'nav-links'} aria-label="页面导航">
        {links.map(([label, href]) => (
          <a href={href} key={href} onClick={() => setOpen(false)}>{label}</a>
        ))}
        <a className="nav-action" href="#workflow" onClick={() => setOpen(false)}>
          看流程 <ArrowRight size={16} />
        </a>
      </nav>
    </header>
  )
}
