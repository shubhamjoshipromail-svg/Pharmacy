import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-stone-50 text-slate-900">
      <aside className="fixed inset-y-0 left-0 flex w-[220px] flex-col border-r border-slate-200 bg-white px-5 py-6">
        <div>
          <div className="text-[18px] font-semibold tracking-tight text-slate-950">RxCheck</div>
          <p className="mt-1 text-sm text-slate-400">Drug interaction tracker</p>
        </div>

        <nav className="mt-10 space-y-2">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              [
                'flex items-center rounded-xl px-3 py-2 text-sm font-medium transition',
                isActive
                  ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-100'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
              ].join(' ')
            }
          >
            Patients
          </NavLink>
        </nav>

        <div className="mt-auto border-t border-slate-200 pt-4 text-[11px] text-red-400">
          Prototype — not for clinical use
        </div>
      </aside>

      <main className="ml-[220px] min-h-screen bg-white">
        <Outlet />
      </main>
    </div>
  )
}
