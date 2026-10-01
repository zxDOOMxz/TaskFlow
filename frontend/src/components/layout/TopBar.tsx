import { useAuthStore } from '@/stores/authStore'

export function TopBar({ title, children }: { title: string; children?: React.ReactNode }) {
  const { workspace } = useAuthStore()

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {workspace && <p className="text-sm text-slate-500">{workspace.name}</p>}
      </div>
      <div className="flex items-center gap-3">
        {children}
      </div>
    </header>
  )
}
