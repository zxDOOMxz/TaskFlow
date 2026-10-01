import { useAuthStore } from '@/stores/authStore'
import { Link, useLocation } from 'react-router-dom'

interface SidebarProps {
  workspaceSlug: string
}

export function Sidebar({ workspaceSlug }: SidebarProps) {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  const navItems = [
    { label: 'Дашборд', path: `/w/${workspaceSlug}` },
    { label: 'Проекты', path: `/w/${workspaceSlug}/projects` },
    { label: 'Wiki', path: `/w/${workspaceSlug}/wiki` },
    { label: 'Чаты', path: `/w/${workspaceSlug}/chat` },
    { label: 'Файлы', path: `/w/${workspaceSlug}/files` },
  ]

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col h-screen sticky top-0">
      <div className="p-4 border-b border-slate-800">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center font-bold">TF</div>
          <span className="font-semibold text-lg">TaskFlow</span>
        </Link>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`block px-3 py-2 rounded-lg transition-colors ${
              location.pathname.startsWith(item.path)
                ? 'bg-primary-600 text-white'
                : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-sm font-medium">
            {user?.first_name[0]}{user?.last_name[0]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.first_name} {user?.last_name}</p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full text-left px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
        >
          Выйти
        </button>
      </div>
    </aside>
  )
}
