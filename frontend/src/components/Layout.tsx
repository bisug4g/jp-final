import { ReactNode } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  StickyNote,
  BookOpen,
  Target,
  Star,
  MessageCircle,
  Wand2,
  LogOut,
  Menu,
  X,
} from "lucide-react"
import { useState } from "react"

const NAV = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/notes", icon: StickyNote, label: "Notes" },
  { to: "/diary", icon: BookOpen, label: "Diary" },
  { to: "/goals", icon: Target, label: "Goals" },
  { to: "/astro", icon: Star, label: "Astro" },
  { to: "/chat", icon: MessageCircle, label: "Ask Jayti" },
  { to: "/tangred", icon: Wand2, label: "Tangred" },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex w-56 flex-col border-r bg-card fixed h-full z-20">
        <div className="p-4 border-b">
          <Link to="/dashboard" className="flex items-center gap-2">
            <span className="text-2xl font-bold font-serif text-primary">Jayti</span>
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                location.pathname.startsWith(to)
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t">
          <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Mobile header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-30 h-14 border-b bg-card flex items-center justify-between px-4">
        <Link to="/dashboard" className="text-xl font-bold font-serif text-primary">Jayti</Link>
        <Button variant="ghost" size="icon" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </header>

      {/* Mobile nav overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-20 bg-black/50" onClick={() => setMobileOpen(false)}>
          <div className="absolute left-0 top-14 bottom-0 w-64 bg-card border-r p-3 space-y-1 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            {NAV.map(({ to, icon: Icon, label }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  location.pathname.startsWith(to)
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            ))}
            <div className="pt-2 border-t mt-2">
              <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
                Sign out
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 md:ml-56 mt-14 md:mt-0 min-h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
