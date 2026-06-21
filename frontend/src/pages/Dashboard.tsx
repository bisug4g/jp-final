import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { StickyNote, BookOpen, Target, CheckSquare, MessageCircle, Star, Wand2, Flame, Sun, Cake } from "lucide-react"
import Layout from "@/components/Layout"

interface Stats {
  recent_notes: number
  recent_diary: number
  active_goals: number
  pending_tasks: number
  birthday: { days_until: number; is_today: boolean }
}

interface ActivityDay {
  date: string
  day: number
  weekday: number
  activity_score: number
  has_activity: boolean
  details: { diary?: number; notes?: number; goals?: number; tasks?: number }
}

interface ActivityData {
  calendar: ActivityDay[]
  stats: { current_streak: number; active_days: number; inactive_days: number }
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [activity, setActivity] = useState<ActivityData | null>(null)
  const [briefing, setBriefing] = useState("")

  useEffect(() => {
    api.get<Stats>("/dashboard/stats").then(setStats).catch(() => {})
    api.get<ActivityData>("/dashboard/activity").then(setActivity).catch(() => {})
    api.get<{ briefing: string }>("/dashboard/briefing").then((d) => setBriefing(d.briefing)).catch(() => {})
  }, [])

  const QUICK_LINKS = [
    { to: "/notes/new", icon: StickyNote, label: "New Note", desc: "Capture thoughts" },
    { to: "/diary/write", icon: BookOpen, label: "Write Diary", desc: "Your day" },
    { to: "/goals", icon: Target, label: "Goals", desc: "Track progress" },
    { to: "/chat", icon: MessageCircle, label: "Ask Jayti", desc: "AI companion" },
    { to: "/astro", icon: Star, label: "Astro", desc: "Cosmic guidance" },
    { to: "/tangred", icon: Wand2, label: "Tangred", desc: "Wardrobe AI" },
  ]

  const scoreClass = (score: number) => {
    if (score >= 75) return "bg-white"
    if (score >= 50) return "bg-white/70"
    if (score > 0) return "bg-white/40"
    return "bg-white/15"
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold font-serif">Welcome back, Jayti!</h1>
          {briefing && <p className="text-muted-foreground mt-1 text-sm">{briefing}</p>}
        </div>

        {/* Activity tracker */}
        {activity && (
          <div
            className="rounded-2xl p-5"
            style={{ background: "linear-gradient(135deg,#FB6F92 0%,#FF8FAB 100%)" }}
          >
            <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
              <h3 className="font-bold text-black flex items-center gap-2">
                <Flame className="h-4 w-4" /> Your Journey Since Feb 6
              </h3>
              <div className="flex gap-2 text-sm font-bold text-black">
                <span className="flex items-center gap-1 bg-white/40 px-3 py-1 rounded-full">
                  <Flame className="h-3 w-3" /> {activity.stats.current_streak} streak
                </span>
                <span className="bg-white/40 px-3 py-1 rounded-full">{activity.stats.active_days} active</span>
                <span className="bg-white/40 px-3 py-1 rounded-full">{activity.stats.inactive_days} missed</span>
              </div>
            </div>
            <div className="grid grid-cols-7 gap-1.5">
              {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => (
                <div key={i} className="text-center text-[10px] text-black/50 font-bold py-1">{d}</div>
              ))}
              {activity.calendar.length > 0 &&
                Array.from({ length: activity.calendar[0].weekday }).map((_, i) => <div key={`pad-${i}`} />)}
              {activity.calendar.map((day) => (
                <div
                  key={day.date}
                  title={`${day.date}: ${day.has_activity ? "Active" : "No activity"}`}
                  className={`aspect-square rounded-lg flex items-center justify-center text-[11px] font-bold text-black cursor-default transition-transform hover:scale-110 ${scoreClass(day.activity_score)}`}
                >
                  {day.day}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { icon: StickyNote, value: stats.recent_notes, label: "Notes" },
              { icon: BookOpen, value: stats.recent_diary, label: "Diary Entries" },
              { icon: Target, value: stats.active_goals, label: "Active Goals" },
              { icon: CheckSquare, value: stats.pending_tasks, label: "Pending Tasks" },
            ].map(({ icon: Icon, value, label }) => (
              <Card key={label} className="bg-gradient-to-br from-[#FB6F92] to-[#FF8FAB] border-0 text-black">
                <CardContent className="pt-5 pb-4 text-center">
                  <div className="w-10 h-10 rounded-xl bg-white/40 flex items-center justify-center mx-auto mb-2">
                    <Icon className="h-5 w-5" />
                  </div>
                  <p className="text-3xl font-bold font-serif">{value}</p>
                  <p className="text-xs font-bold uppercase tracking-widest mt-0.5">{label}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Birthday countdown */}
        {stats?.birthday && !stats.birthday.is_today && (
          <Card className="bg-gradient-to-br from-[#FB6F92] to-[#FF8FAB] border-0 text-black">
            <CardContent className="flex items-center gap-4 py-4">
              <Cake className="h-8 w-8 shrink-0" />
              <div>
                <p className="font-bold text-lg font-serif">{stats.birthday.days_until} days to your birthday 🎂</p>
                <p className="text-sm text-black/70">February 6th is coming!</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick links */}
        <div>
          <h2 className="font-semibold text-sm uppercase tracking-widest text-muted-foreground mb-3">Quick Access</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {QUICK_LINKS.map(({ to, icon: Icon, label, desc }) => (
              <Link
                key={to}
                to={to}
                className="flex items-center gap-3 p-4 rounded-xl border bg-card hover:bg-accent transition-colors group"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-sm">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Daily briefing card */}
        {briefing && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Sun className="h-4 w-4 text-primary" /> Daily Briefing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed">{briefing}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  )
}
