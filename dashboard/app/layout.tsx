import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ROSTR — Agent OS Dashboard',
  description: 'AI Agent Operating System with knowledge brain, NPAO task engine, and persistent memory',
};

const NAV_ITEMS = [
  { href: '/', icon: '🏠', label: 'Home' },
  { href: '/chat', icon: '💬', label: 'Chat' },
  { href: '/brain', icon: '🧠', label: 'Brain' },
  { href: '/tasks', icon: '📋', label: 'Tasks' },
  { href: '/memory', icon: '💾', label: 'Memory' },
  { href: '/settings', icon: '⚙️', label: 'Settings' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="sidebar-logo">
              ROSTR
              <span>Agent OS v0.1.0</span>
            </div>
            <nav className="sidebar-nav">
              {NAV_ITEMS.map((item) => (
                <a key={item.href} href={item.href} className="nav-item">
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </a>
              ))}
            </nav>
            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span className="status-dot online" />
              Agent Online
            </div>
          </aside>
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
